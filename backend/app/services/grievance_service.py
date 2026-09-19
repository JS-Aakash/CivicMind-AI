"""
CivicMind AI — Grievance Service (Module 3 Decision Pipeline)
Orchestrates:
Citizen Input
      ↓
IndicLID Language Analysis
      ↓
MuRIL v1.1 Neural Classifier (6 Heads)
      ↓
Lightweight Context & Hazard Extraction
      ↓
Context-Aware Priority Engine (Neural + Rules + Safety)
      ↓
Smart Multi-Issue Department Router
      ↓
SLA & Escalation Engine
      ↓
Explainable Governance Decision
"""
import logging
from typing import Optional, Dict, Any

from app.services.interfaces import LanguageInfo, ClassificationResult
from app.services.language_service import language_detection_service
from app.services.mock_classifier import mock_classifier, mock_entity_extractor
from app.services.routing_service import routing_service
from app.ml.extraction.lightweight_extractor import LightweightCivicExtractor
from app.priority.priority_engine import priority_engine, FinalPriorityResult
from app.priority.priority_explanation import PriorityExplanationGenerator
from app.routing.routing_engine import routing_engine
from app.routing.sla_engine import sla_engine
from app.schemas.schemas import (
    AIAnalysisResult,
    DepartmentTargetSchema,
    SLASchema,
    PriorityFactorSchema,
    ExplanationSchema,
    Module3DecisionSchema,
)

logger = logging.getLogger(__name__)


class GrievanceService:
    """
    Orchestrates the full end-to-end CivicMind AI grievance intelligence pipeline.
    """

    async def analyze(
        self,
        text: str,
        location_text: str | None = None,
    ) -> AIAnalysisResult:
        """
        Full analysis pipeline returning canonical Module 3 decision.
        """
        # Step 1: Language detection (IndicLID)
        lang_info = await language_detection_service.detect(text)
        logger.debug(f"Language detected: {lang_info.primary_language} | code-mixed: {lang_info.is_code_mixed}")

        # Step 2: Classification (MuRIL v1.1 Multi-Task)
        from app.core.config import settings
        from app.services.muril_classifier import muril_classifier_service

        is_trained = (
            settings.AI_MODE == "trained"
            and muril_classifier_service.is_trained_model_available
        )

        category_probabilities = None
        task_confidences = None
        secondary_categories = []

        if is_trained:
            logger.info("Running real fine-tuned MuRIL multi-task model inference")
            pred_detail = muril_classifier_service.predict_detailed(text, lang_info)
            is_grievance = pred_detail["is_grievance"]
            category = pred_detail["category"]
            subcategory = pred_detail["subcategory"]
            severity = pred_detail["severity"]
            neural_priority = pred_detail["priority"]
            confidence = pred_detail["confidence"]
            explanation_raw = pred_detail.get("explanation", "")
            category_probabilities = pred_detail.get("category_probabilities")
            secondary_categories = pred_detail.get("secondary_categories", [])
            task_confidences = {
                "grievance": pred_detail["grievance_confidence"],
                "category": pred_detail["category_confidence"],
                "subcategory": pred_detail["subcategory_confidence"],
                "severity": pred_detail["severity_confidence"],
                "priority": pred_detail["priority_confidence"],
            }
            model_version = "muril-multitask-v1.1"
            is_mock = False
        else:
            if settings.AI_MODE == "trained":
                logger.warning("AI_MODE=trained requested, but trained model not yet available. Falling back to demo mode.")
            classification = await mock_classifier.classify(text, lang_info)
            is_grievance = classification.is_grievance
            category = classification.category
            subcategory = classification.subcategory
            severity = classification.severity
            neural_priority = classification.priority
            confidence = classification.confidence
            explanation_raw = classification.explanation
            model_version = "muril-base-cased-mock-v1"
            is_mock = True

        # Step 3: Lightweight Entity & Hazard Extraction
        entities_obj = LightweightCivicExtractor.extract_entities(text)
        entities_dict = {
            "duration": f"{entities_obj.duration_days} day" if entities_obj.duration_days else None,
            "duration_days": entities_obj.duration_days,
            "affected_count": entities_obj.affected_count,
            "safety_hazard": entities_obj.safety_hazard,
            "hazard_types": entities_obj.hazard_types,
            "vulnerable_impact": entities_obj.vulnerable_impact,
            "location_mentions": entities_obj.location_mentions,
        }

        # Step 4: Context-Aware Priority Engine (Neural + Rules + Safety)
        priority_res: FinalPriorityResult = priority_engine.evaluate(
            text=text,
            category=category,
            subcategory=subcategory,
            neural_priority=neural_priority,
            neural_probabilities={neural_priority: confidence},
            extracted_hazards=entities_obj.hazard_types,
        )
        final_priority = priority_res.final_priority

        # Step 5: Smart Multi-Issue Department Routing
        routing_res = routing_engine.route(
            category=category,
            subcategory=subcategory,
            category_confidence=task_confidences.get("category", confidence) if task_confidences else confidence,
            subcategory_confidence=task_confidences.get("subcategory", 0.6) if task_confidences else 0.6,
            secondary_categories=secondary_categories,
            is_grievance=is_grievance,
            is_immediate_hazard=priority_res.safety_assessment.is_immediate_hazard,
        )

        # Step 6: Configurable SLA Engine
        sla_res = sla_engine.calculate_sla(
            priority=final_priority,
            department_id=routing_res.primary_department.id,
            category=category,
            is_immediate_hazard=priority_res.safety_assessment.is_immediate_hazard,
        )

        # Step 7: Deterministic Governance Explainability Generator
        structured_explanation = PriorityExplanationGenerator.generate(
            text=text,
            category=category,
            subcategory=subcategory,
            neural_priority=neural_priority,
            neural_prob=task_confidences.get("priority", 0.7) if task_confidences else 0.7,
            final_priority=final_priority,
            context=priority_res.context_signals,
            safety=priority_res.safety_assessment,
            department_name=routing_res.primary_department.name,
            sla_hours=sla_res.target_sla_hours,
            routing_confidence=routing_res.routing_confidence,
            review_decision=routing_res.routing_decision,
            factors=priority_res.factors,
        )

        # Step 8: Build Canonical Decision Object
        primary_dept_schema = DepartmentTargetSchema(
            id=routing_res.primary_department.id,
            code=routing_res.primary_department.code,
            name=routing_res.primary_department.name,
            contact_email=routing_res.primary_department.contact_email,
            confidence=routing_res.primary_department.confidence,
            is_primary=True,
            role="primary_lead",
        )

        sec_depts_schema = [
            DepartmentTargetSchema(
                id=d.id,
                code=d.code,
                name=d.name,
                contact_email=d.contact_email,
                confidence=d.confidence,
                is_primary=False,
                role=d.role,
            )
            for d in routing_res.secondary_departments
        ]

        sla_schema = SLASchema(
            target_sla_hours=sla_res.target_sla_hours,
            target_response_minutes=sla_res.target_response_minutes,
            created_at=sla_res.created_at,
            due_at=sla_res.due_at,
            status=sla_res.status,
            elapsed_minutes=sla_res.elapsed_minutes,
            remaining_minutes=sla_res.remaining_minutes,
            percent_elapsed=sla_res.percent_elapsed,
            is_breached=sla_res.is_breached,
            is_approaching=sla_res.is_approaching,
        )

        explanation_schema = ExplanationSchema(
            summary=structured_explanation.summary,
            what_category_reason=structured_explanation.what_category_reason,
            why_urgent_factors=[
                PriorityFactorSchema(
                    factor=f.factor,
                    label=f.label,
                    value=f.value,
                    impact=f.impact,
                    weight_contribution=f.weight_contribution,
                    description=f.description,
                )
                for f in structured_explanation.why_urgent_factors
            ],
            who_department_reason=structured_explanation.who_department_reason,
            when_sla_reason=structured_explanation.when_sla_reason,
            how_confident_reason=structured_explanation.how_confident_reason,
            human_review_reason=structured_explanation.human_review_reason,
            reasoning_mode=structured_explanation.reasoning_mode,
        )

        from app.schemas.schemas import ContextSignalsSchema

        context_schema = ContextSignalsSchema(
            duration_hours=priority_res.context_signals.duration.normalized_hours,
            is_prolonged=priority_res.context_signals.duration.is_prolonged,
            affected_population=priority_res.context_signals.population.scope,
            estimated_population=priority_res.context_signals.population.estimated_count,
            safety_risk=priority_res.safety_assessment.is_immediate_hazard,
            vulnerable_population=priority_res.context_signals.is_vulnerable_impact,
            vulnerable_groups=priority_res.context_signals.vulnerable_groups,
            critical_infrastructure=priority_res.context_signals.is_critical_infrastructure,
            infrastructure_types=priority_res.context_signals.infrastructure_types,
            is_night_time=priority_res.context_signals.is_night_time,
            location_category=priority_res.context_signals.location_category,
        )

        routing_dict = {
            "primary_department": primary_dept_schema.model_dump(),
            "secondary_departments": [d.model_dump() for d in sec_depts_schema],
            "routing_confidence": routing_res.routing_confidence,
            "routing_decision": routing_res.routing_decision,
        }

        priority_dict = {
            "neural_prediction": neural_priority,
            "neural_probability": confidence,
            "final_priority": final_priority,
            "priority_score": priority_res.composite_score,
            "reasoning_mode": priority_res.reasoning_mode,
        }

        review_dict = {
            "decision": routing_res.routing_decision,
            "requires_human_review": routing_res.requires_human_review,
            "reason": routing_res.routing_reason,
        }

        decision_details_schema = Module3DecisionSchema(
            final_priority=final_priority,
            composite_score=priority_res.composite_score,
            neural_priority=neural_priority,
            neural_probabilities=priority_res.neural_probabilities,
            primary_department=primary_dept_schema,
            secondary_departments=sec_depts_schema,
            routing_confidence=routing_res.routing_confidence,
            routing_decision=routing_res.routing_decision,
            requires_human_review=routing_res.requires_human_review,
            sla=sla_schema,
            explanation=explanation_schema,
            context=context_schema,
            routing=routing_dict,
            priority=priority_dict,
            review=review_dict,
            is_compound_multi_issue=routing_res.is_compound_multi_issue,
            is_immediate_hazard=priority_res.safety_assessment.is_immediate_hazard,
        )

        return AIAnalysisResult(
            # Language
            primary_language=lang_info.primary_language,
            language_name=lang_info.language_name,
            languages=lang_info.languages,
            script=lang_info.script,
            is_code_mixed=lang_info.is_code_mixed,

            # Classification
            is_grievance=is_grievance,
            category=category,
            subcategory=subcategory,
            severity=severity,
            priority=final_priority,
            confidence=confidence,

            # Entities
            entities=entities_dict,
            duration_mentioned=entities_dict["duration"],

            # Routing
            department_code=routing_res.primary_department.code,
            department_name=routing_res.primary_department.name,
            routing_reason=routing_res.routing_reason,

            # Explainability & Evidence
            explanation=structured_explanation.summary,
            category_probabilities=category_probabilities,
            task_confidences=task_confidences,

            # Module 3 Advanced Decision
            routing_decision=routing_res.routing_decision,
            requires_human_review=routing_res.requires_human_review,
            primary_department=primary_dept_schema,
            secondary_departments=sec_depts_schema,
            sla=sla_schema,
            decision_details=decision_details_schema,

            # Metadata
            is_mock=is_mock,
            model_version=model_version,
        )


grievance_service = GrievanceService()
