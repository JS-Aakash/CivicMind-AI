"""
CivicMind AI — Language Variants Generator
Transforms structured scenario instances into natural citizen utterances across:
- English (en)
- Tamil native script (ta)
- Tanglish / Romanized Tamil (ta_roman)
- Hindi native script (hi)
- Hinglish / Romanized Hindi (hi_roman)
- Code-mixed / informal dialect (mixed)
"""
import random
from typing import Dict, List, Any

# Vocabulary and phrase banks for authentic regional citizen expression
VOCABULARY = {
    "water": {
        "en": ["water supply", "drinking water", "tap water", "water line"],
        "ta_native": ["குடிநீர்", "தண்ணீர் சப்ளை", "குழாய் தண்ணீர்", "வாட்டர்"],
        "ta_roman": ["thanni", "tanni", "water", "drinking water", "thanniya", "kudineer"],
        "hi_native": ["पानी", "जल आपूर्ति", "नल का पानी", "वाटर सप्लाई"],
        "hi_roman": ["paani", "pani", "water", "water supply", "jal"],
    },
    "roads": {
        "en": ["road", "pothole", "street", "pavement"],
        "ta_native": ["சாலை", "ரோடு", "குழி", "பள்ளம்"],
        "ta_roman": ["road", "roadu", "pothole", "kuzhi", "pallam", "salai"],
        "hi_native": ["सड़क", "रास्ता", "गड्ढा", "रोड"],
        "hi_roman": ["sadak", "road", "gaddha", "gaddhe", "rasta"],
    },
    "sanitation": {
        "en": ["garbage", "waste", "trash", "dustbin"],
        "ta_native": ["குப்பை", "கழிவு", "குப்பை தொட்டி"],
        "ta_roman": ["kuppai", "garbage", "trash", "dustbin", "waste"],
        "hi_native": ["कचरा", "कूड़ा", "डस्टबिन", "गंदगी"],
        "hi_roman": ["kachra", "kuda", "garbage", "dustbin", "gandagi"],
    },
    "electricity": {
        "en": ["electricity", "power", "current", "wire", "transformer"],
        "ta_native": ["மின்சாரம்", "கரண்ட்", "மின் கம்பி", "டிரான்ஸ்பார்மர்"],
        "ta_roman": ["current", "power", "kambi", "wire", "transformer", "minsaram"],
        "hi_native": ["बिजली", "करंट", "तार", "ट्रांसफार्मर"],
        "hi_roman": ["bijli", "current", "power", "taar", "transformer", "line"],
    },
    "drainage": {
        "en": ["drainage", "sewage", "gutter", "waterlogging"],
        "ta_native": ["சாக்கடை", "கழிவுநீர்", "வடிகால்", "தேங்கிய நீர்"],
        "ta_roman": ["drainage", "sakkadai", "sewage", "gutter", "kallivuneer"],
        "hi_native": ["नाली", "सीवर", "गंदा पानी", "जलभराव"],
        "hi_roman": ["naali", "sewer", "ganda pani", "drainage", "gutter"],
    },
    "transport": {
        "en": ["bus", "bus stop", "transport", "route"],
        "ta_native": ["பேருந்து", "பஸ்", "பஸ் ஸ்டாப்"],
        "ta_roman": ["bus", "busu", "bus stop", "route", "perundhu"],
        "hi_native": ["बस", "बस स्टॉप", "परिवहन"],
        "hi_roman": ["bus", "bus stop", "parivahan", "gaadi"],
    },
    "healthcare": {
        "en": ["hospital", "doctor", "medicine", "clinic"],
        "ta_native": ["மருத்துவமனை", "டாக்டர்", "மருந்து"],
        "ta_roman": ["hospital", "doctor", "marundhu", "medicine", "clinic"],
        "hi_native": ["अस्पताल", "डॉक्टर", "दवा", "इलाज"],
        "hi_roman": ["hospital", "aspatal", "doctor", "dawai", "medicine"],
    },
    "street_infrastructure": {
        "en": ["streetlight", "lamp post", "park", "footpath"],
        "ta_native": ["தெரு விளக்கு", "லைட் கம்பம்", "பூங்கா"],
        "ta_roman": ["streetlight", "theru vilakku", "pole", "lightu", "park"],
        "hi_native": ["स्ट्रीट लाइट", "खंभा", "पार्क"],
        "hi_roman": ["street light", "khamba", "park", "light"],
    },
    "public_safety": {
        "en": ["danger", "hazard", "risk", "accident"],
        "ta_native": ["ஆபத்து", "விபத்து", "பாதுகாப்பற்ற"],
        "ta_roman": ["danger", "aabathu", "risk", "accident"],
        "hi_native": ["खतरा", "दुर्घटना", "असुरक्षित"],
        "hi_roman": ["khatra", "danger", "accident", "risk"],
    },
    "other": {
        "en": ["help", "information", "office", "procedure"],
        "ta_native": ["தகவல்", "உதவி", "அலுவலகம்"],
        "ta_roman": ["thagaval", "help", "information", "office"],
        "hi_native": ["जानकारी", "मदद", "दफ्तर"],
        "hi_roman": ["jaankari", "help", "information", "office"],
    },
}

# Conversational honorifics and prefixes
HONORIFICS = {
    "en": ["Sir", "Respected authority", "Dear team", "Hello", ""],
    "ta_native": ["ஐயா", "வணக்கம்", "அண்ணா", ""],
    "ta_roman": ["Sir", "Anna", "Madam", "Vanakkam", "Bro", ""],
    "hi_native": ["महोदय", "नमस्ते", "भाई साहब", ""],
    "hi_roman": ["Sir", "Bhaiya", "Namaste", "Madam", ""],
    "mixed": ["Sir", "Anna", "Bhaiya", "Pls help", ""],
}

# Urgent and polite suffixes
CALLS_TO_ACTION = {
    "en": ["Please take action soon.", "Kindly resolve this immediately.", "Extremely urgent!", "Please look into this."],
    "ta_native": ["தயவுசெய்து உடனே நடவடிக்கை எடுக்கவும்.", "சீக்கிரம் சரி செய்யவும்.", "ரொம்ப அவசரம்."],
    "ta_roman": ["Konjam seekiram parunga please.", "Pls action edunga.", "Romba kashtam ah iruku.", "Urgent please fix."],
    "hi_native": ["कृपया जल्द से जल्द समाधान करें।", "बहुत जरूरी है ध्यान दें।", "कृपया तुरंत कार्यवाही करें।"],
    "hi_roman": ["Kripya jald se jald theek karein.", "Bahut pareshani ho rahi hai.", "Please jaldi karo.", "Urgent hai."],
    "mixed": ["Please fix panunga asap.", "Jaldi action lo bhai.", "Very urgent pls help."],
}


class LanguageVariantGenerator:
    """Generates varied multilingual utterances for a scenario."""

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate_variant(self, scenario: Dict[str, Any], target_language: str, variant_type: str = "neutral") -> Dict[str, Any]:
        """
        Generate a single training example for a scenario in `target_language`.
        target_language options: 'en', 'ta', 'ta_roman', 'hi', 'hi_roman', 'mixed'
        """
        cat = scenario["category"]
        prob = scenario["problem"]
        loc = scenario["location_name"]
        dur = scenario["duration_text"]
        is_g = scenario["is_grievance"]

        # Synthesize text based on language and variant type
        text = self._build_utterance(cat, prob, loc, dur, is_g, target_language, variant_type)

        # Determine language metadata
        primary_lang, script, is_code_mixed, detected_langs = self._get_lang_meta(target_language)

        return {
            "text": text,
            "primary_language": primary_lang,
            "languages": detected_langs,
            "script": script,
            "is_code_mixed": is_code_mixed,
            "is_grievance": scenario["is_grievance"],
            "category": scenario["category"],
            "subcategory": scenario["subcategory"],
            "severity": scenario["severity"],
            "priority": scenario["priority"],
            "duration_days": scenario["duration_days"],
            "affected_population": "street_residents" if is_g else "none",
            "safety_risk": scenario["safety_risk"],
            "location_type": scenario["location_type"],
            "department": scenario["department"],
            "scenario_id": scenario["scenario_id"],
            "variant_type": variant_type,
            "source_type": "synthetic_controlled",
        }

    def _get_lang_meta(self, target_language: str):
        if target_language == "en":
            return "en", "roman", False, ["en"]
        elif target_language == "ta":
            return "ta", "native", False, ["ta"]
        elif target_language == "ta_roman":
            return "ta", "roman", True, ["ta", "en"]
        elif target_language == "hi":
            return "hi", "native", False, ["hi"]
        elif target_language == "hi_roman":
            return "hi", "roman", True, ["hi", "en"]
        else:  # mixed
            return "ta" if self.rng.random() > 0.5 else "hi", "roman", True, ["ta", "hi", "en"]

    def _build_utterance(self, cat: str, prob: str, loc: str, dur: str, is_g: bool, lang: str, vtype: str) -> str:
        h = self.rng.choice(HONORIFICS.get(lang, [""]))
        cta = self.rng.choice(CALLS_TO_ACTION.get(lang, [""]))

        if not is_g:
            return self._build_non_grievance_text(cat, prob, loc, lang, vtype)

        # Grievance templates
        if lang == "en":
            templates = [
                f"{h} In {loc}, {prob} {dur}. {cta}",
                f"{loc}: {prob} {dur}. Please resolve.",
                f"Reporting an issue at {loc}. {prob.capitalize()} {dur}.",
                f"Severe civic problem in {loc} — {prob}.",
                f"{prob} at {loc} {dur}!",
            ]
        elif lang == "ta":
            templates = [
                f"{h} {loc} பகுதியில் {dur} {self._translate_prob_ta_native(cat, prob)}. {cta}",
                f"{loc}: {self._translate_prob_ta_native(cat, prob)} {dur}. நடவடிக்கை எடுக்கவும்.",
                f"{loc} மெயின் ரோட்டில் {dur} பெரும் பிரச்சனை: {self._translate_prob_ta_native(cat, prob)}.",
            ]
        elif lang == "ta_roman":
            templates = [
                f"{h} {loc} la {dur} {self._translate_prob_tanglish(cat, prob)}. {cta}",
                f"{loc} area la {self._translate_prob_tanglish(cat, prob)} {dur}. Romba kashtam.",
                f"Anna {loc} la {dur} {self._translate_prob_tanglish(cat, prob)}, please fix it soon.",
                f"{loc}: {self._translate_prob_tanglish(cat, prob)} {dur}!",
            ]
        elif lang == "hi":
            templates = [
                f"{h} {loc} में {dur} {self._translate_prob_hi_native(cat, prob)}। {cta}",
                f"{loc}: {dur} {self._translate_prob_hi_native(cat, prob)}। कृपया ध्यान दें।",
                f"{loc} क्षेत्र में भारी समस्या है, {self._translate_prob_hi_native(cat, prob)} {dur}।",
            ]
        elif lang == "hi_roman":
            templates = [
                f"{h} {loc} me {dur} {self._translate_prob_hinglish(cat, prob)}. {cta}",
                f"{loc} area me {dur} {self._translate_prob_hinglish(cat, prob)}. Bahut dikkat ho rahi hai.",
                f"Bhaiya {loc} me {self._translate_prob_hinglish(cat, prob)} {dur}, please jaldi dekhiye.",
                f"{loc}: {self._translate_prob_hinglish(cat, prob)} {dur}!",
            ]
        else:  # mixed / code-mixed edge
            templates = [
                f"Sir {loc} la {self._translate_prob_tanglish(cat, prob)} {dur} and road totally blocked.",
                f"{loc} me live wire/pipe problem {dur} ah iruku please send emergency team.",
                f"Anna {loc} la {self._translate_prob_tanglish(cat, prob)} {dur}, koi sun nahi raha!",
                f"{loc} area issue: {prob} {dur}, kids passing daily very dangerous!",
            ]

        res = self.rng.choice(templates).strip()
        # Clean up double spaces
        return " ".join(res.split())

    def _build_non_grievance_text(self, cat: str, prob: str, loc: str, lang: str, vtype: str) -> str:
        if lang == "en":
            return prob
        elif lang == "ta":
            return f"வணக்கம், {loc} பகுதியில் {cat} தொடர்பான தகவல் மற்றும் நடைமுறை விவரங்கள் அறிய விரும்புகிறேன்."
        elif lang == "ta_roman":
            return f"Hello, {loc} la {cat} department enquiry number and procedure theriyuma please?"
        elif lang == "hi":
            return f"नमस्ते, {loc} में {cat} विभाग से संबंधित जानकारी और प्रक्रिया क्या है कृपया बताएं।"
        elif lang == "hi_roman":
            return f"Hello, {loc} me {cat} helpline number aur bill payment procedure kya hai batayein."
        else:
            return f"Hi sir, can you tell the {cat} contact info for {loc} ward office? Thank you."

    def _translate_prob_ta_native(self, cat: str, prob: str) -> str:
        mapping = {
            "water": "குடிநீர் விநியோகம் முற்றிலும் நின்றுவிட்டது",
            "roads": "சாலையில் ஆபத்தான பள்ளங்கள் ஏற்பட்டு விபத்துகள் நடக்கின்றன",
            "sanitation": "குப்பைகள் பல நாட்களாக அள்ளப்படாமல் நாற்றமடிக்கிறது",
            "electricity": "மின் இணைப்பு துண்டிக்கப்பட்டு தெரு முழுவதும் இருட்டாக உள்ளது",
            "drainage": "சாக்கடை நீர் சாலையில் வழிந்தோடி தெருவில் தேங்கியுள்ளது",
            "transport": "பேருந்துகள் குறிப்பிட்ட நேரத்தில் வராமல் பயணிகள் தவிக்கின்றனர்",
            "healthcare": "மருத்துவமனையில் மருந்து மற்றும் மருத்துவர்கள் கிடைக்கவில்லை",
            "street_infrastructure": "தெருவிளக்குகள் எரியாமல் உடைந்து விழுந்துள்ளன",
            "public_safety": "மின்கம்பி அறுந்து விழுந்து பொதுமக்கள் உயிருக்கு ஆபத்தாக உள்ளது",
            "other": "பொதுமக்கள் சேவை குறைபாடு உள்ளது",
        }
        return mapping.get(cat, "பொது சேவை குறைபாடு ஏற்பட்டுள்ளது")

    def _translate_prob_tanglish(self, cat: str, prob: str) -> str:
        mapping = {
            "water": "water supply varala thanni romba scarcity ah iruku",
            "roads": "road la periya pothole iruku bikes slip aagi viluranga",
            "sanitation": "kuppai van vandhu 3 days aachu waste fulla overflow aagudhu",
            "electricity": "power cut aagi full street dark ah iruku current illa",
            "drainage": "drainage block aagi road la black sewage odudhu",
            "transport": "regular bus time ku varama wait panni tired aagudhu",
            "healthcare": "clinic la doctor illa medicines stock illa",
            "street_infrastructure": "street light eriyala pole broken condition",
            "public_safety": "live wire cut aagi keela kedakku romba dangerous",
            "other": "civic issue romba worst ah iruku",
        }
        return mapping.get(cat, "civic problem romba perusa iruku")

    def _translate_prob_hi_native(self, cat: str, prob: str) -> str:
        mapping = {
            "water": "पीने का पानी बिल्कुल नहीं आ रहा है",
            "roads": "सड़क पर गहरे गड्ढे हैं जिससे गाड़ियां फिसल रही हैं",
            "sanitation": "कचरा नहीं उठाया गया है और भारी बदबू आ रही है",
            "electricity": "बिजली गुल है और पूरा इलाका अंधेरे में डूबा है",
            "drainage": "सीवर का गंदा पानी सड़क पर बह रहा है",
            "transport": "बसें समय पर नहीं आ रही हैं और यात्री परेशान हैं",
            "healthcare": "अस्पताल में दवाईयां उपलब्ध नहीं हैं",
            "street_infrastructure": "स्ट्रीट लाइट खराब है और खंभा झुका हुआ है",
            "public_safety": "बिजली का चालू तार टूटकर सड़क पर पड़ा है भारी खतरा",
            "other": "नागरिक सुविधा में बड़ी खराबी है",
        }
        return mapping.get(cat, "नागरिक समस्या बनी हुई है")

    def _translate_prob_hinglish(self, cat: str, prob: str) -> str:
        mapping = {
            "water": "water supply nahi aa rahi paani ki bahut problem hai",
            "roads": "road pe bohot bada gaddha hai daily accidents ho rahe hain",
            "sanitation": "kachra uthane wali gaadi nahi aayi dustbin overflow hai",
            "electricity": "power cut ho gaya hai bijli nahi aa rahi",
            "drainage": "sewer drain block hai ganda paani road pe beh raha hai",
            "transport": "bus time pe nahi aati commuters stranded hain",
            "healthcare": "dispensary me dawai nahi mil rahi doctor absent hai",
            "street_infrastructure": "street light band padi hai khamba toot gaya hai",
            "public_safety": "live wire toota pada hai bahut bada accident risk hai",
            "other": "problem bahut serious ho gayi hai",
        }
        return mapping.get(cat, "problem solve nahi hui hai")
