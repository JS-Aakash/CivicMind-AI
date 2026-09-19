"""
CivicMind AI — Module 4 Demo Seeding Script
Generates realistic multilingual grievances containing 4 emergent spatio-temporal clusters + background noise:
1. Water Supply Disruption (T. Nagar / Kodambakkam) — 20+ complaints in Tamil, Tanglish, English, Hindi, Hinglish
2. Road Damage Cluster (Anna Nagar) — 12+ complaints across English, Tamil, Tanglish
3. Garbage Accumulation Cluster (Velachery) — 10+ complaints across Tamil, English, Hindi
4. Electrical Hazard / Live Wire (Mylapore) — 6+ critical complaints
5. Uncorrelated noise complaints across Chennai

IMPORTANT: Inputs do NOT contain pre-assigned incident IDs; they are discovered by Module 4 clustering!
"""
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.muril_classifier import muril_classifier_service
from app.services.incident_service import incident_service
from app.services.duplicate_service import duplicate_detection_service


def generate_module4_demo_complaints():
    now = datetime.now(timezone.utc)
    complaints = []

    # ─────────────────────────────────────────────────────────────────────────────
    # Cluster 1: Water Supply Disruption (T. Nagar: ~13.0418° N, 80.2341° E)
    # ─────────────────────────────────────────────────────────────────────────────
    water_texts = [
        ("Anna 3 days ah water supply varala. Kadaisi la kudam vachi collect panrom.", "ta", "roman", True, "T. Nagar, Ward 112", 13.0415, 80.2338, 2),
        ("மூன்று நாட்களாக குடிநீர் வரவில்லை. மக்கள் மிகவும் கஷ்டப்படுகிறோம்.", "ta", "native", False, "Ranganathan Street, T. Nagar", 13.0422, 80.2345, 3),
        ("Water supply illa for 3 days in our entire street. Please send water tanker.", "en", "roman", False, "South Usman Road, T. Nagar", 13.0408, 80.2332, 4),
        ("Teen din se paani nahi aa raha. Pipeline leak hua hai shayad.", "hi", "roman", True, "Panagal Park, T. Nagar", 13.0428, 80.2351, 5),
        ("Thanni varala, whole street affected for past 72 hours. Serious shortage.", "ta", "roman", True, "G.N. Chetty Road, T. Nagar", 13.0435, 80.2360, 6),
        ("குடிநீர் குழாயில் அழுக்கு நீர் வருகிறது மற்றும் தண்ணீர் வரத்து முற்றிலும் நின்றுவிட்டது.", "ta", "native", False, "T. Nagar Bus Terminus Area", 13.0411, 80.2325, 7),
        ("No water in residential apartments since morning. Third day of disruption.", "en", "roman", False, "Venkatnarayana Road, T. Nagar", 13.0440, 80.2370, 8),
        ("Pani ki bahut killat hai yahan 3 din se. Tanker bhi nahi pahunch raha.", "hi", "roman", True, "Burkit Road, T. Nagar", 13.0395, 80.2318, 9),
        ("Water connection totally dry. Motor potalum thanni varala.", "ta", "roman", True, "Pondy Bazaar, T. Nagar", 13.0419, 80.2349, 10),
        ("Three days no municipal water supply in block B.", "en", "roman", False, "Sarojini Street, T. Nagar", 13.0425, 80.2335, 11),
        ("தண்ணீர் விநியோகம் கடந்த 3 நாட்களாக தடைபட்டுள்ளது.", "ta", "native", False, "Mambalam Station Road, T. Nagar", 13.0402, 80.2320, 12),
        ("Water pressure is zero since 3 days. Please restore supply urgently.", "en", "roman", False, "Habibullah Road, T. Nagar", 13.0450, 80.2380, 14),
        ("Paani nahi aa raha sab log pareshan hain pipeline band hai.", "hi", "roman", True, "Bazullah Road, T. Nagar", 13.0430, 80.2365, 16),
        ("Continuous 72 hrs water cut in our locality. Essential supplies exhausted.", "en", "roman", False, "North Usman Road, T. Nagar", 13.0438, 80.2340, 18),
        ("ரங்கநாதன் தெருவில் குடிநீர் வரத்து இல்லை.", "ta", "native", False, "Ranganathan Street Corner", 13.0417, 80.2342, 20),
        ("Main pipeline damaged near flyover, water supply stopped for 3 days.", "en", "roman", False, "Usman Flyover, T. Nagar", 13.0413, 80.2339, 22),
    ]

    for text, lang, script, is_cm, loc, lat, lng, hrs_ago in water_texts:
        complaints.append({
            "id": str(uuid.uuid4()),
            "complaint_code": f"CMP-{random.randint(10000, 99999)}",
            "text": text,
            "language": lang,
            "script": script,
            "is_code_mixed": is_cm,
            "detected_languages": [lang, "en"] if is_cm else [lang],
            "is_grievance": True,
            "category": "water",
            "subcategory": "supply_disruption",
            "severity": "high",
            "priority": "high",
            "confidence": round(random.uniform(0.91, 0.98), 3),
            "entities": {"duration": "3 days"},
            "duration_mentioned": "3 days",
            "latitude": lat,
            "longitude": lng,
            "location_text": loc,
            "ward": "Ward 112",
            "department_name": "Water Supply Department",
            "status": "open",
            "created_at": (now - timedelta(hours=hrs_ago)).isoformat(),
        })

    # ─────────────────────────────────────────────────────────────────────────────
    # Cluster 2: Road Damage & Potholes (Anna Nagar: ~13.0850° N, 80.2100° E)
    # ─────────────────────────────────────────────────────────────────────────────
    road_texts = [
        ("Huge potholes near Anna Nagar Roundtana causing accidents and vehicle damage.", "en", "roman", False, "Anna Nagar Roundtana", 13.0852, 80.2105, 5),
        ("ரோட்டில் பெரிய பள்ளம் ஏற்பட்டுள்ளது. இருசக்கர வாகனங்கள் விழுகின்றன.", "ta", "native", False, "2nd Avenue, Anna Nagar", 13.0860, 80.2112, 6),
        ("Road full of deep potholes after rain. Traffic jammed completely.", "en", "roman", False, "3rd Avenue, Anna Nagar", 13.0845, 80.2095, 8),
        ("Rodu fulla periya pothole irukku, night la visibility illa accident aagudhu.", "ta", "roman", True, "Shanthi Colony, Anna Nagar", 13.0838, 80.2120, 10),
        ("Asphalt washed away near signal, craters formed on main road.", "en", "roman", False, "Anna Nagar West Extension", 13.0870, 80.2080, 12),
        ("Sadak par bahut bada gaddha hai gaadi chalana mushkil ho gaya.", "hi", "roman", True, "12th Main Road, Anna Nagar", 13.0855, 80.2100, 14),
        ("ரோடு முற்றிலும் சேதமடைந்துள்ளது உடனடியாக தார் ரோடு போடவும்.", "ta", "native", False, "4th Avenue, Anna Nagar", 13.0848, 80.2108, 16),
        ("Multiple crater potholes on both sides of carriage way.", "en", "roman", False, "Anna Nagar East", 13.0865, 80.2130, 20),
    ]

    for text, lang, script, is_cm, loc, lat, lng, hrs_ago in road_texts:
        complaints.append({
            "id": str(uuid.uuid4()),
            "complaint_code": f"CMP-{random.randint(10000, 99999)}",
            "text": text,
            "language": lang,
            "script": script,
            "is_code_mixed": is_cm,
            "detected_languages": [lang, "en"] if is_cm else [lang],
            "is_grievance": True,
            "category": "roads",
            "subcategory": "potholes",
            "severity": "moderate",
            "priority": "medium",
            "confidence": round(random.uniform(0.88, 0.95), 3),
            "entities": {"hazard": "pothole"},
            "duration_mentioned": None,
            "latitude": lat,
            "longitude": lng,
            "location_text": loc,
            "ward": "Ward 95",
            "department_name": "Roads & Highways Department",
            "status": "in_progress",
            "created_at": (now - timedelta(hours=hrs_ago)).isoformat(),
        })

    # ─────────────────────────────────────────────────────────────────────────────
    # Cluster 3: Garbage Accumulation (Velachery: ~12.9750° N, 80.2210° E)
    # ─────────────────────────────────────────────────────────────────────────────
    garbage_texts = [
        ("Garbage not cleared for one week, overflowing into road near bypass.", "en", "roman", False, "Velachery Bypass Road", 12.9755, 80.2215, 6),
        ("குப்பை தொட்டி நிரம்பி வழிகிறது, கடும் துர்நாற்றம் வீசுகிறது.", "ta", "native", False, "Gandhi Road, Velachery", 12.9748, 80.2205, 8),
        ("Kuppai 5 days ah collect panla. Street fulla smell and mosquito menace.", "ta", "roman", True, "Baby Nagar, Velachery", 12.9760, 80.2220, 10),
        ("Solid waste accumulating on sidewalk blocking pedestrian movement.", "en", "roman", False, "Taramani Link Road, Velachery", 12.9735, 80.2230, 12),
        ("Kachra pichle 4 din se nahi uthaya gaya hai, bimari phail rahi hai.", "hi", "roman", True, "Vijaya Nagar, Velachery", 12.9770, 80.2195, 15),
        ("குப்பை கொட்டி வைக்கப்பட்டு அப்புறப்படுத்தப்படாமல் உள்ளது.", "ta", "native", False, "Dhandeeswaram, Velachery", 12.9765, 80.2210, 18),
    ]

    for text, lang, script, is_cm, loc, lat, lng, hrs_ago in garbage_texts:
        complaints.append({
            "id": str(uuid.uuid4()),
            "complaint_code": f"CMP-{random.randint(10000, 99999)}",
            "text": text,
            "language": lang,
            "script": script,
            "is_code_mixed": is_cm,
            "detected_languages": [lang, "en"] if is_cm else [lang],
            "is_grievance": True,
            "category": "sanitation",
            "subcategory": "garbage_collection",
            "severity": "moderate",
            "priority": "medium",
            "confidence": round(random.uniform(0.89, 0.96), 3),
            "entities": {"duration": "1 week"},
            "duration_mentioned": "1 week",
            "latitude": lat,
            "longitude": lng,
            "location_text": loc,
            "ward": "Ward 178",
            "department_name": "Sanitation & Solid Waste Management",
            "status": "open",
            "created_at": (now - timedelta(hours=hrs_ago)).isoformat(),
        })

    # ─────────────────────────────────────────────────────────────────────────────
    # Cluster 4: Electrical Hazard / Transformer Sparking (Mylapore: ~13.0330° N, 80.2670° E)
    # ─────────────────────────────────────────────────────────────────────────────
    electric_texts = [
        ("Electric transformer sparking heavily with open exposed live wire on street!", "en", "roman", False, "Luz Church Road, Mylapore", 13.0335, 80.2675, 1),
        ("மின் கம்பி அறுந்து விழுந்து தீப்பொறி பறக்கிறது. ஆபத்து!", "ta", "native", False, "Kutchery Road, Mylapore", 13.0328, 80.2668, 2),
        ("Live wire hanging down on pavement near bus stop. Immediate danger.", "en", "roman", False, "Mylapore Tank Area", 13.0340, 80.2680, 2),
        ("Transformer la fire spark aagudhu, power fluctuating dangerously.", "ta", "roman", True, "Royapettah High Road, Mylapore", 13.0345, 80.2660, 3),
        ("Bijli ka taar toota hua hai footpath par, kabhi bhi shock lag sakta hai.", "hi", "roman", True, "East Mada Street, Mylapore", 13.0330, 80.2685, 3),
    ]

    for text, lang, script, is_cm, loc, lat, lng, hrs_ago in electric_texts:
        complaints.append({
            "id": str(uuid.uuid4()),
            "complaint_code": f"CMP-{random.randint(10000, 99999)}",
            "text": text,
            "language": lang,
            "script": script,
            "is_code_mixed": is_cm,
            "detected_languages": [lang, "en"] if is_cm else [lang],
            "is_grievance": True,
            "category": "electricity",
            "subcategory": "hazard",
            "severity": "critical",
            "priority": "critical",
            "is_immediate_hazard": True,
            "confidence": round(random.uniform(0.94, 0.99), 3),
            "entities": {"hazard": "live wire", "danger": True},
            "duration_mentioned": None,
            "latitude": lat,
            "longitude": lng,
            "location_text": loc,
            "ward": "Ward 124",
            "department_name": "Electricity & Power Board",
            "status": "open",
            "created_at": (now - timedelta(hours=hrs_ago)).isoformat(),
        })

    # ─────────────────────────────────────────────────────────────────────────────
    # Noise Complaints (Spread across Guindy, Tambaram, Perambur, Triplicane)
    # ─────────────────────────────────────────────────────────────────────────────
    noise_texts = [
        ("Street light not working in residential street.", "electricity", "streetlighting", "low", 13.0067, 80.2020, "Guindy", 30),
        ("Property tax assessment query for new house.", "revenue", "property_tax", "low", 12.9249, 80.1000, "Tambaram", 45),
        ("Dog barking at night causing disturbance.", "other", "noise", "low", 13.1100, 80.2300, "Perambur", 50),
        ("Need birth certificate copy from municipality.", "revenue", "certificate", "low", 13.0580, 80.2760, "Triplicane", 60),
    ]

    for text, cat, subcat, prio, lat, lng, loc, hrs_ago in noise_texts:
        complaints.append({
            "id": str(uuid.uuid4()),
            "complaint_code": f"CMP-{random.randint(10000, 99999)}",
            "text": text,
            "language": "en",
            "script": "roman",
            "is_code_mixed": False,
            "detected_languages": ["en"],
            "is_grievance": True,
            "category": cat,
            "subcategory": subcat,
            "severity": "low",
            "priority": prio,
            "confidence": 0.85,
            "entities": {},
            "duration_mentioned": None,
            "latitude": lat,
            "longitude": lng,
            "location_text": loc,
            "ward": "General Ward",
            "department_name": "General Grievance Cell",
            "status": "open",
            "created_at": (now - timedelta(hours=hrs_ago)).isoformat(),
        })

    return complaints


def seed_and_cluster():
    print("=" * 60)
    print("CIVICMIND AI — MODULE 4 DEMO DATA SEEDING & INCIDENT CLUSTERING")
    print("=" * 60)

    complaints = generate_module4_demo_complaints()
    print(f"\n[1/3] Generated {len(complaints)} raw complaints across 4 target incidents + noise.")

    print("\n[2/3] Computing 768-dim MuRIL embeddings for all complaints...")
    for idx, c in enumerate(complaints):
        c["embedding"] = muril_classifier_service.get_embedding(c["text"])
        if (idx + 1) % 10 == 0 or idx == len(complaints) - 1:
            print(f"  Processed {idx + 1}/{len(complaints)} embeddings...")

    print("\n[3/3] Executing spatio-temporal DBSCAN clustering engine...")
    incident_service.seed_complaints(complaints)
    result = incident_service.recompute_all_incidents(time_window_hours=720, dry_run=False)

    print(f"\nDiscovered {result['formed_incidents_count']} Incidents in {result['runtime_ms']:.2f}ms:")
    for inc in result["incidents"]:
        print(f"\n  * {inc['title']}")
        print(f"     Incident Code : {inc['incident_code']}")
        print(f"     Category      : {inc['category'].upper()} | Priority: {inc['priority'].upper()}")
        print(f"     Complaints    : {inc['complaint_count']} reports | Languages: {', '.join(inc['languages'])}")
        print(f"     Trend         : {inc['trend']} ({inc['complaints_per_hour']} complaints/hr) | Emerging: {inc['is_emerging']}")
        print(f"     Confidence    : {inc['confidence']*100:.1f}% (Semantic: {inc['confidence_signals']['semantic_cohesion']*100:.0f}%, Geo: {inc['confidence_signals']['geographic_cohesion']*100:.0f}%)")
        print(f"     Lead Dept     : {inc['primary_department']}")

    print("\n" + "=" * 60)
    print("MODULE 4 DEMO SEEDING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    seed_and_cluster()
