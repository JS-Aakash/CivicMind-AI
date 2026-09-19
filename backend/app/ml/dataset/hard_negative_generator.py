"""
CivicMind AI — Targeted Hard-Negative & Robustness Generator (Module 2.5)
Generates high-value, realistic civic complaints focusing on short transliterations,
code-mixing, multi-issue combinations, safety hazards, and adversarial inquiries.
"""
import random
from typing import List, Dict, Any
from app.ml.taxonomy import CATEGORIES, ALL_SUBCATEGORIES, get_scoped_subcategory
from app.ml.dataset.label_policy import determine_intent

class HardNegativeGenerator:
    """Generates targeted hard negative and multi-issue dataset examples."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate_short_tanglish(self, count: int = 400) -> List[Dict[str, Any]]:
        """Group A: Short 2-5 word Tanglish complaints without English anchors."""
        templates = [
            # Water
            ("thanni varala", "water", "no_water_supply", "high", "high"),
            ("3 naala thanni illa", "water", "no_water_supply", "high", "high"),
            ("water illa anna", "water", "no_water_supply", "high", "high"),
            ("kudineer varala", "water", "no_water_supply", "high", "high"),
            ("tanni romba low ah varudhu", "water", "low_water_pressure", "medium", "medium"),
            ("pipe la thanni leak aaguthu", "water", "water_leakage", "medium", "medium"),
            ("kudineer la sand kalandhu varudhu", "water", "contaminated_water", "high", "high"),
            ("tanker water innum varala", "water", "water_tanker_issue", "medium", "high"),

            # Electricity
            ("current pochu", "electricity", "power_outage", "medium", "high"),
            ("current illa", "electricity", "power_outage", "medium", "high"),
            ("voltage romba low ah iruku", "electricity", "voltage_issue", "medium", "medium"),
            ("current kamba wire arunthu vizhundhuchu", "electricity", "fallen_wire", "critical", "critical"),
            ("transformer la smoke varudhu", "electricity", "transformer_issue", "critical", "critical"),
            ("street light eriyala", "electricity", "street_light_failure", "medium", "medium"),
            ("current shock adikidhu pole la", "electricity", "electrical_hazard", "critical", "critical"),

            # Roads
            ("road la periya pallam", "roads", "pothole", "medium", "high"),
            ("saalai romba mosam", "roads", "damaged_road", "medium", "medium"),
            ("road block aagi iruku", "roads", "road_blockage", "medium", "high"),
            ("nadai paadhai odanjiruchu", "roads", "broken_footpath", "low", "medium"),
            ("traffic signal vela seiyala", "roads", "traffic_signal_issue", "medium", "high"),
            ("road la rain water thengi iruku", "roads", "road_flooding", "high", "high"),

            # Sanitation
            ("kuppai edukala", "sanitation", "garbage_not_collected", "medium", "high"),
            ("dustbin overflow aagudhu", "sanitation", "overflowing_bin", "medium", "medium"),
            ("theru fulla kuppai kottirukaanga", "sanitation", "illegal_dumping", "medium", "high"),
            ("toilet romba dirty ah iruku", "sanitation", "public_toilet_issue", "medium", "medium"),

            # Drainage
            ("kaalvaai adaichiruchu", "drainage", "blocked_drain", "medium", "high"),
            ("saakadai overflow aagudhu", "drainage", "sewage_overflow", "high", "high"),
            ("drainage water therula pogudhu", "drainage", "sewage_overflow", "high", "high"),
            ("mazhai thanni thengi nikkudhu", "drainage", "waterlogging", "high", "high"),

            # Transport
            ("bus time ku varala", "transport", "bus_delay", "low", "low"),
            ("bus eh varala innum", "transport", "bus_unavailable", "medium", "medium"),
            ("bus la semma crowd", "transport", "overcrowding", "low", "low"),
            ("bus conductor extra fare kekuraaru", "transport", "fare_issue", "low", "low"),

            # Public Safety
            ("anga wall collapse aaga pogudhu", "public_safety", "fallen_structure", "critical", "critical"),
            ("therula theevilaguthu", "public_safety", "fire_hazard", "critical", "critical"),
            ("manhole open ah iruku", "public_safety", "accident_hazard", "critical", "critical"),
        ]

        results = []
        for i in range(count):
            tpl = self.rng.choice(templates)
            text = tpl[0]
            # Add occasional citizen conversational variation
            prefix = self.rng.choice(["", "Anna ", "Sir ", "Pls ", "Romba urgent ", ""])
            suffix = self.rng.choice(["", " please fix", " romba kashtam", " fix pannunga", "!!", ""])
            full_text = f"{prefix}{text}{suffix}".strip()

            results.append({
                "text": full_text,
                "primary_language": "ta",
                "languages": ["ta", "en"] if any(c.isascii() and c.isalpha() for c in full_text) else ["ta"],
                "script": "roman",
                "is_code_mixed": True,
                "is_grievance": True,
                "intent": "grievance",
                "category": tpl[1],
                "subcategory": tpl[2],
                "severity": tpl[3],
                "priority": tpl[4],
                "variant_type": "short_tanglish",
                "source_type": "hard_negative_augmentation",
            })
        return results

    def generate_short_hinglish(self, count: int = 400) -> List[Dict[str, Any]]:
        """Group B: Short 2-5 word Hinglish complaints without English anchors."""
        templates = [
            # Water
            ("paani nahi aa raha", "water", "no_water_supply", "high", "high"),
            ("3 din se paani nahi", "water", "no_water_supply", "high", "high"),
            ("paani ka pressure bohot kam hai", "water", "low_water_pressure", "medium", "medium"),
            ("pipe se paani beh raha hai", "water", "water_leakage", "medium", "medium"),
            ("ganda paani aa raha hai", "water", "contaminated_water", "high", "high"),
            ("tanker abhi tak nahi aaya", "water", "water_tanker_issue", "medium", "high"),

            # Electricity
            ("bijli chali gayi", "electricity", "power_outage", "medium", "high"),
            ("light nahi hai", "electricity", "power_outage", "medium", "high"),
            ("voltage bohot low hai", "electricity", "voltage_issue", "medium", "medium"),
            ("bijli ka taar tut kar gir gaya", "electricity", "fallen_wire", "critical", "critical"),
            ("transformer me aag lag gayi", "electricity", "transformer_issue", "critical", "critical"),
            ("street light band hai", "electricity", "street_light_failure", "medium", "medium"),
            ("khambhe me current aa raha hai", "electricity", "electrical_hazard", "critical", "critical"),

            # Roads
            ("sadak pe bada gaddha hai", "roads", "pothole", "medium", "high"),
            ("sadak bohot kharab hai", "roads", "damaged_road", "medium", "medium"),
            ("raasta band ho gaya hai", "roads", "road_blockage", "medium", "high"),
            ("footpath toota hua hai", "roads", "broken_footpath", "low", "medium"),
            ("traffic light kaam nahi kar rahi", "roads", "traffic_signal_issue", "medium", "high"),
            ("sadak pe paani bhar gaya", "roads", "road_flooding", "high", "high"),

            # Sanitation
            ("kachra nahi uthaya", "sanitation", "garbage_not_collected", "medium", "high"),
            ("dustbin bhar ke beh raha hai", "sanitation", "overflowing_bin", "medium", "medium"),
            ("gali me kachra feka hua hai", "sanitation", "illegal_dumping", "medium", "high"),
            ("toilet bohot ganda hai", "sanitation", "public_toilet_issue", "medium", "medium"),

            # Drainage
            ("naala jaam ho gaya hai", "drainage", "blocked_drain", "medium", "high"),
            ("ganda naala overflow ho raha hai", "drainage", "sewage_overflow", "high", "high"),
            ("gali me sewage ka paani beh raha hai", "drainage", "sewage_overflow", "high", "high"),
            ("barish ka paani jama ho gaya", "drainage", "waterlogging", "high", "high"),

            # Public Safety
            ("deewar girne wali hai", "public_safety", "fallen_structure", "critical", "critical"),
            ("manhole khula pada hai", "public_safety", "accident_hazard", "critical", "critical"),
            ("aag lagne ka khatra hai", "public_safety", "fire_hazard", "critical", "critical"),
        ]

        results = []
        for i in range(count):
            tpl = self.rng.choice(templates)
            text = tpl[0]
            prefix = self.rng.choice(["", "Bhaiya ", "Sir ", "Pls ", "Bohot dikkat hai ", ""])
            suffix = self.rng.choice(["", " jaldi dekhiye", " solve karo", " please", "!!", ""])
            full_text = f"{prefix}{text}{suffix}".strip()

            results.append({
                "text": full_text,
                "primary_language": "hi",
                "languages": ["hi", "en"] if any(c.isascii() and c.isalpha() for c in full_text) else ["hi"],
                "script": "roman",
                "is_code_mixed": True,
                "is_grievance": True,
                "intent": "grievance",
                "category": tpl[1],
                "subcategory": tpl[2],
                "severity": tpl[3],
                "priority": tpl[4],
                "variant_type": "short_hinglish",
                "source_type": "hard_negative_augmentation",
            })
        return results

    def generate_multi_issue_examples(self, count: int = 500) -> List[Dict[str, Any]]:
        """Group D: Multi-issue compound complaints."""
        multi_templates = [
            (
                "Road is damaged with huge potholes and rain water is collecting everywhere.",
                "roads", ["drainage"], "pothole", ["waterlogging"], "high", "high", "en"
            ),
            (
                "Water supply pipe broken on the street and road is completely flooded.",
                "water", ["roads", "drainage"], "water_leakage", ["road_flooding"], "high", "high", "en"
            ),
            (
                "Street light is not working and broken footpath makes walking dangerous at night.",
                "electricity", ["roads", "public_safety"], "street_light_failure", ["broken_footpath", "unsafe_area"], "medium", "high", "en"
            ),
            (
                "Garbage is not collected for a week and open drainage is overflowing into homes.",
                "sanitation", ["drainage"], "garbage_not_collected", ["sewage_overflow"], "high", "high", "en"
            ),
            (
                "Live electric wire has fallen on the road near the primary school, children passing.",
                "electricity", ["public_safety", "roads"], "fallen_wire", ["accident_hazard"], "critical", "critical", "en"
            ),
            # Tanglish multi-issue
            (
                "Road la periya pothole iruku and saakadai water fulla overflow aagi thengiduchu.",
                "roads", ["drainage"], "pothole", ["sewage_overflow"], "high", "high", "ta"
            ),
            (
                "Street light eriyala and area full dark ah unsafe ah iruku.",
                "electricity", ["public_safety"], "street_light_failure", ["unsafe_area"], "medium", "high", "ta"
            ),
            (
                "Kuppai edukala and blocked drain la smell romba mosam ah varudhu.",
                "sanitation", ["drainage"], "garbage_not_collected", ["blocked_drain"], "high", "high", "ta"
            ),
            # Hinglish multi-issue
            (
                "Sadak pe bada pothole hai aur barish ka paani bhar gaya hai poori gali me.",
                "roads", ["drainage"], "pothole", ["waterlogging"], "high", "high", "hi"
            ),
            (
                "Live wire khambhe se gir gaya hai sadak pe, log pass ho rahe hain urgent.",
                "electricity", ["public_safety", "roads"], "fallen_wire", ["accident_hazard"], "critical", "critical", "hi"
            ),
            (
                "Kachra sadak pe pada hai aur naala overflow ho kar gali me beh raha hai.",
                "sanitation", ["drainage"], "garbage_not_collected", ["sewage_overflow"], "high", "high", "hi"
            ),
        ]

        results = []
        for i in range(count):
            tpl = self.rng.choice(multi_templates)
            results.append({
                "text": tpl[0],
                "primary_language": tpl[7],
                "languages": [tpl[7], "en"] if tpl[7] != "en" else ["en"],
                "script": "roman",
                "is_code_mixed": (tpl[7] != "en"),
                "is_grievance": True,
                "intent": "grievance",
                "category": tpl[1],
                "subcategory": tpl[3],
                "secondary_categories": tpl[2],
                "secondary_subcategories": tpl[4],
                "severity": tpl[5],
                "priority": tpl[6],
                "variant_type": "multi_issue_compound",
                "source_type": "hard_negative_augmentation",
            })
        return results

    def generate_adversarial_inquiries(self, count: int = 350) -> List[Dict[str, Any]]:
        """Group E: Adversarial borderline inquiries vs grievances."""
        templates = [
            ("What is the water department helpline phone number?", "water", "information_request"),
            ("Can you tell me the procedure to apply for a new electricity meter?", "electricity", "procedure_request"),
            ("How to register a complaint if road maintenance is delayed?", "roads", "procedure_request"),
            ("Where is the nearest municipal sanitation office located?", "sanitation", "information_request"),
            ("When does the morning garbage collection truck usually arrive?", "sanitation", "information_request"),
            ("What are the working hours of the government primary health clinic?", "healthcare", "information_request"),
            ("What is the official bus timetable for route 21G?", "transport", "information_request"),
            ("Whom should I contact to get permission for road cutting work?", "roads", "procedure_request"),
            ("Hello good morning, want to know water bill payment online procedure.", "water", "procedure_request"),
            ("Sir can you share the phone number of local electricity board office?", "electricity", "information_request"),
            ("Thanni bill epdi online la pay panradhu?", "water", "procedure_request"),
            ("Current office contact number theriyuma?", "electricity", "information_request"),
            ("Bijli ka naya connection kaise le?", "electricity", "procedure_request"),
            ("Paani vibhaag ka helpline number kya hai?", "water", "information_request"),
            ("Hello", "other", "greeting"),
            ("Helloooo", "other", "greeting"),
            ("Good morning", "other", "greeting"),
            ("Namaste", "other", "greeting"),
            ("Vanakkam", "other", "greeting"),
        ]

        results = []
        for i in range(count):
            tpl = self.rng.choice(templates)
            results.append({
                "text": tpl[0],
                "primary_language": "ta" if any(w in tpl[0] for w in ["epdi", "panradhu", "theriyuma", "Vanakkam"]) else ("hi" if any(w in tpl[0] for w in ["kaise", "kya", "Namaste", "vibhaag"]) else "en"),
                "languages": ["en"],
                "script": "roman",
                "is_code_mixed": False,
                "is_grievance": False,
                "intent": tpl[2],
                "category": "other" if tpl[2] == "greeting" else tpl[1],
                "subcategory": "general_inquiry",
                "severity": "low",
                "priority": "low",
                "variant_type": "adversarial_inquiry",
                "source_type": "hard_negative_augmentation",
            })
        return results

    def generate_contrastive_pairs(self, count: int = 400) -> List[Dict[str, Any]]:
        """Group G: Hard-negative category contrast pairs."""
        pairs = [
            # Water supply vs Drainage waterlogging
            ("Water is not coming from the kitchen tap for 2 days.", "water", "no_water_supply", "high", "high"),
            ("Rain water is stagnant and flooding the entire road surface.", "drainage", "waterlogging", "high", "high"),
            # Road damage vs Drainage overflow
            ("Deep pothole and broken bitumen on the main street.", "roads", "pothole", "medium", "high"),
            ("Underground sewer line choked and dirty black water overflowing on road.", "drainage", "sewage_overflow", "high", "high"),
            # Road obstruction vs Electricity hazard
            ("Fallen tree branch is blocking the traffic on road.", "roads", "road_blockage", "medium", "high"),
            ("Live 440V electrical wire snapped and touching the road.", "electricity", "fallen_wire", "critical", "critical"),
            # Street infrastructure vs Electricity
            ("Street light pole is physically bent and rusty in the park.", "street_infrastructure", "broken_streetlight", "low", "medium"),
            ("Street light is not turning on because of power supply outage.", "electricity", "street_light_failure", "medium", "medium"),
            # Sanitation vs Drainage
            ("Plastic waste and food garbage dumped near roadside bin.", "sanitation", "illegal_dumping", "medium", "high"),
            ("Solid garbage has clogged the stormwater drain channel.", "drainage", "blocked_drain", "high", "high"),
        ]

        results = []
        for i in range(count):
            tpl = self.rng.choice(pairs)
            results.append({
                "text": tpl[0],
                "primary_language": "en",
                "languages": ["en"],
                "script": "roman",
                "is_code_mixed": False,
                "is_grievance": True,
                "intent": "grievance",
                "category": tpl[1],
                "subcategory": tpl[2],
                "severity": tpl[3],
                "priority": tpl[4],
                "variant_type": "contrastive_category_pair",
                "source_type": "hard_negative_augmentation",
            })
        return results
