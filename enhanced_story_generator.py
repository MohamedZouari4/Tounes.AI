"""
ENHANCED STORY GENERATOR
=========================
Features:
1. Rich multi-language prompts (AR/EN/FR)
2. Arabic-specific validation and post-processing
3. Retry logic with progressive prompt strengthening
4. Quality scoring system
5. Caching for performance
6. Clean error handling
"""

import json
import re
import time
from pathlib import Path
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def load_landmarks():
    """Load landmark data from JSON file."""
    data_path = Path(__file__).parent / "landmarks_data.json"
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


# ============================================
# LANGUAGE UTILITIES
# ============================================

def contains_english(text: str) -> bool:
    """Check if text contains significant English (3+ consecutive letters)."""
    english_pattern = re.compile(r'[a-zA-Z]{3,}')
    matches = english_pattern.findall(text)
    allowed = {'UNESCO', 'GPS', 'OK', 'VIP', 'WiFi', 'DNA', 'BBC', 'CNN', 'API'}
    return any(m.upper() not in allowed for m in matches)


def calculate_arabic_ratio(text: str) -> float:
    """Calculate ratio of Arabic characters (0.0 to 1.0)."""
    if not text:
        return 0.0
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    arabic_chars = sum(len(m) for m in arabic_pattern.findall(text))
    total_letters = sum(1 for c in text if c.isalpha())
    return arabic_chars / total_letters if total_letters > 0 else 0.0


def validate_arabic_story(story: str, min_arabic_ratio: float = 0.85) -> tuple:
    """
    Validate an Arabic story's quality.
    Returns: (is_valid, issues_list, arabic_ratio)
    """
    issues = []
    arabic_ratio = calculate_arabic_ratio(story)
    
    if arabic_ratio < min_arabic_ratio:
        issues.append(f"Arabic ratio too low: {arabic_ratio:.1%}")
    if contains_english(story):
        issues.append("Contains English words")
    
    word_count = len(story.split())
    if word_count < 100:
        issues.append(f"Too short: {word_count} words")
    elif word_count > 600:
        issues.append(f"Too long: {word_count} words")
    
    endings = story.count('.') + story.count('،') + story.count('؟') + story.count('!')
    if endings < 5:
        issues.append("Lacks proper sentence structure")
    
    return len(issues) == 0, issues, arabic_ratio


# ============================================
# SYSTEM PROMPTS
# ============================================

SYSTEM_PROMPTS = {
    "en": """You are Tounes (تونس), the legendary Tunisian storyteller. Your voice has echoed through medinas for generations. You have the gift of making the past come alive.

Rules:
1. Write in vivid, literary English prose
2. Use sensory details - sights, sounds, smells, textures
3. Mention the visitor's name naturally 2-3 times
4. Never use headers, bullet points, or formatting - only flowing narrative
5. Write 250-400 words of pure storytelling""",

    "fr": """Vous êtes Tounes (تونس), le légendaire conteur tunisien. Votre voix résonne dans les médinas depuis des générations. Vous avez le don de faire revivre le passé.

Règles:
1. Écrivez en français littéraire vivant
2. Utilisez des détails sensoriels - vues, sons, odeurs, textures
3. Mentionnez le nom du visiteur naturellement 2-3 fois
4. Jamais de titres, puces ou mise en forme - seulement du récit fluide
5. Écrivez 250-400 mots de narration pure""",

    "ar": """أنت "تونس"، الحكواتي التونسي الأسطوري. صوتك يتردد في المدن العتيقة منذ أجيال.

قواعد صارمة:
١. اكتب بالعربية الفصحى فقط - لا كلمات إنجليزية أو فرنسية إطلاقاً
٢. استخدم أسماء الأماكن بالعربية (قرطاج، سيدي بو سعيد، الجم)
٣. لا تستخدم أي حروف لاتينية
٤. اجعل القصة غنية بالتفاصيل الحسية والعاطفية
٥. اذكر اسم الزائر بشكل طبيعي في القصة
٦. لا تستخدم عناوين أو نقاط - فقط نثر متدفق
٧. اكتب ٢٥٠-٤٠٠ كلمة"""
}


# ============================================
# STORY MODE INSTRUCTIONS (all languages)
# ============================================

STORY_MODE_INSTRUCTIONS = {
    "historian": {
        "en": """Write as a knowledgeable historian sharing fascinating facts.
- Be educational but engaging
- Include specific dates, names, and historical context
- Use phrases like "Historical records tell us..." or "Archaeologists discovered..."
- Balance facts with narrative flow""",
        "fr": """Écrivez comme un historien érudit partageant des faits fascinants.
- Soyez éducatif mais captivant
- Incluez dates, noms et contexte historique
- Utilisez: "Les archives nous révèlent..." ou "Les archéologues ont découvert..." """,
        "ar": """أسلوب المؤرخ العالِم:
- اكتب كمؤرخ خبير يشارك حقائق مذهلة
- استخدم: "تُخبرنا السجلات التاريخية..."، "اكتشف علماء الآثار..."
- اذكر التواريخ والأسماء والسياق التاريخي
- اجعل التاريخ حياً ومشوقاً"""
    },
    "legend_keeper": {
        "en": """Write as a mystical storyteller sharing ancient legends and local myths.
- Create an atmosphere of mystery and wonder
- Include supernatural elements and folklore
- Use phrases like "The old ones say..." or "Legend whispers that..."
- Make the reader feel they're hearing a secret""",
        "fr": """Écrivez comme un conteur mystique partageant légendes et mythes.
- Créez une atmosphère de mystère et d'émerveillement
- Utilisez: "Les anciens racontent..." ou "La légende murmure..."
- Faites sentir au lecteur qu'il entend un secret""",
        "ar": """أسلوب حارس الأساطير:
- اكتب كحكواتي صوفي يشارك أساطير قديمة
- اخلق جواً من الغموض والسحر
- استخدم: "يُحكى في القِدَم..."، "تهمس الأسطورة..."
- اجعل القارئ يشعر أنه يسمع سراً قديماً"""
    },
    "time_traveler": {
        "en": """Write in SECOND PERSON PRESENT TENSE - the reader IS there.
- Use "You stand...", "You hear...", "You feel...", "You see..."
- Make it viscerally immersive with all five senses
- The reader is the protagonist living in that historical moment""",
        "fr": """Écrivez à la DEUXIÈME PERSONNE AU PRÉSENT - le lecteur est LÀ.
- Utilisez "Vous vous tenez...", "Vous entendez...", "Vous ressentez..."
- Rendez l'expérience immersive avec les cinq sens
- Le lecteur est le protagoniste vivant ce moment historique""",
        "ar": """أسلوب المسافر عبر الزمن:
- اكتب بضمير المخاطب في الزمن الحاضر
- استخدم: "أنت تقف حيث..."، "تسمع..."، "تشعر..."، "ترى..."
- اجعلها تجربة غامرة بكل الحواس الخمس
- القارئ هو بطل هذه اللحظة التاريخية"""
    },
    "romantic": {
        "en": """Write with poetic beauty, focusing on love and emotional resonance.
- Include romantic legends or a sense of timeless beauty
- Use lyrical, flowing language
- Focus on beauty, emotion, and human connection""",
        "fr": """Écrivez avec beauté poétique, en vous concentrant sur l'amour et l'émotion.
- Incluez des légendes romantiques ou une beauté intemporelle
- Utilisez un langage lyrique et fluide""",
        "ar": """أسلوب الرومانسي:
- اكتب بجمالية شاعرية تركز على الحب والعاطفة
- استخدم لغة شعرية متدفقة
- ركز على الجمال والمشاعر والارتباط الروحي"""
    },
    "kids_adventure": {
        "en": """Write for children ages 6-10.
- Use simple vocabulary and short sentences
- Make history feel like an exciting adventure
- Add: "Can you imagine...?" "Guess what happened next!"
- Keep it educational but FUN""",
        "fr": """Écrivez pour enfants de 6 à 10 ans.
- Vocabulaire simple et phrases courtes
- L'histoire comme une aventure excitante
- Ajoutez: "Vous imaginez...?" "Devinez ce qui s'est passé!" """,
        "ar": """أسلوب مغامرة الأطفال:
- اكتب للأطفال من سن ٦ إلى ١٠ سنوات
- استخدم كلمات بسيطة وجمل قصيرة
- أضف: "هل تتخيل...؟"، "خمّن ماذا حدث!"
- اجعلها ممتعة وتعليمية"""
    },
    "movie_director": {
        "en": """Write like a cinematic narration or movie script.
- Use visual language and dramatic pacing
- Set scenes: "The camera pans across...", "We see...", "Cut to..."
- Build tension and atmosphere""",
        "fr": """Écrivez comme une narration cinématographique.
- Utilisez un langage visuel et un rythme dramatique
- Posez les scènes: "La caméra glisse sur...", "On voit...", "Coupez à..." """,
        "ar": """أسلوب المخرج السينمائي:
- اكتب مثل سيناريو فيلم أو سرد سينمائي
- استخدم لغة بصرية وإيقاع درامي
- صِف المشاهد: "تتحرك الكاميرا..."، "نرى..."
- ابنِ التوتر والأجواء الدرامية"""
    }
}


COMPANION_CONTEXT = {
    "en": {
        "solo": "traveling alone, seeking personal discovery and reflection",
        "couple": "with their romantic partner, sharing this special moment together",
        "family": "with their family, including curious children who ask wonderful questions",
        "friends": "with a group of friends, having the adventure of a lifetime"
    },
    "fr": {
        "solo": "voyageant seul(e), en quête de découverte personnelle",
        "couple": "avec son partenaire, partageant ce moment spécial",
        "family": "avec sa famille, accompagné d'enfants curieux",
        "friends": "avec un groupe d'amis, vivant l'aventure de leur vie"
    },
    "ar": {
        "solo": "يسافر بمفرده، يبحث عن اكتشاف الذات والتأمل",
        "couple": "مع شريك حياته، يتشاركان هذه اللحظة الخاصة معاً",
        "family": "مع عائلته، بما في ذلك أطفال فضوليون يطرحون أسئلة رائعة",
        "friends": "مع مجموعة من الأصدقاء، يعيشون مغامرة لا تُنسى"
    }
}


# ============================================
# PROMPT BUILDER
# ============================================

def build_story_prompt(landmark_key: str, story_mode: str, user_name: str,
                       companion: str, language: str) -> str:
    """
    Build a detailed prompt for story generation in any supported language.
    """
    landmarks_data = load_landmarks()
    if not landmarks_data:
        return None
    
    landmark = landmarks_data["landmarks"].get(landmark_key, {})
    if not landmark:
        return None
    
    # Extract data in the target language (with fallback to English)
    lang = language
    landmark_name = landmark["name"].get(lang, landmark["name"]["en"])
    history = landmark.get("history", {}).get(lang, landmark.get("history", {}).get("en", ""))
    legends = landmark.get("legends", {}).get(lang, landmark.get("legends", {}).get("en", ""))
    atmosphere = landmark.get("atmosphere", {})
    fun_facts = landmark.get("fun_facts", {}).get(lang, [])
    
    mode_instructions = STORY_MODE_INSTRUCTIONS.get(story_mode, STORY_MODE_INSTRUCTIONS["time_traveler"])
    mode_text = mode_instructions.get(lang, mode_instructions.get("en", ""))
    
    companion_text = COMPANION_CONTEXT.get(lang, COMPANION_CONTEXT["en"]).get(companion, "exploring")
    
    # Build atmosphere description
    sights = ', '.join(atmosphere.get('sights', []))
    sounds = ', '.join(atmosphere.get('sounds', []))
    smells = ', '.join(atmosphere.get('smells', []))
    facts_text = '\n'.join(f'- {fact}' for fact in fun_facts)
    
    if lang == "ar":
        prompt = f"""## مهمتك
اكتب قصة غامرة وشخصية عن **{landmark_name}** للزائر **{user_name}**، الذي {companion_text}.

{mode_text}

## معلومات عن المعلم
**التاريخ:** {history}
**الأساطير:** {legends}
**المشاهد:** {sights}
**الأصوات:** {sounds}
**الروائح:** {smells}
**حقائق:**
{facts_text}

## متطلبات
١. اذكر اسم {user_name} بشكل طبيعي ٢-٣ مرات
٢. أشِر إلى رفقته ({companion})
٣. اجعله بطل التجربة
٤. اختم بشيء لا يُنسى
٥. ٢٥٠-٤٠٠ كلمة بالعربية فقط - لا إنجليزية
٦. سرد متدفق بدون عناوين أو نقاط

ابدأ القصة الآن:"""
    
    elif lang == "fr":
        prompt = f"""## VOTRE MISSION
Créez une histoire immersive et personnalisée sur **{landmark_name}** pour **{user_name}**, qui {companion_text}.

{mode_text}

## CONNAISSANCES DU LIEU
**Histoire:** {history}
**Légendes:** {legends}
**Vues:** {sights}
**Sons:** {sounds}
**Odeurs:** {smells}
**Faits:**
{facts_text}

## EXIGENCES
1. Mentionnez le nom de {user_name} naturellement 2-3 fois
2. Référencez leur situation ({companion})
3. Faites-en le protagoniste
4. Terminez par quelque chose de mémorable
5. 250-400 mots en français uniquement
6. Récit fluide sans titres ni puces

Commencez votre histoire maintenant:"""
    
    else:  # English
        prompt = f"""## YOUR MISSION
Create an immersive, personalized story about **{landmark_name}** for **{user_name}**, who is {companion_text}.

{mode_text}

## LANDMARK KNOWLEDGE
**History:** {history}
**Legends:** {legends}
**Sights:** {sights}
**Sounds:** {sounds}
**Smells:** {smells}
**Fun Facts:**
{facts_text}

## REQUIREMENTS
1. Include {user_name}'s name naturally 2-3 times
2. Reference their companion situation ({companion})
3. Make them the protagonist
4. End with something memorable
5. Write 250-400 words
6. Pure flowing narrative - NO headers, NO bullet points

Begin your story now:"""

    return prompt


# ============================================
# STORY GENERATION WITH RETRY
# ============================================

class StoryGenerationError(Exception):
    """Custom exception for story generation errors."""
    pass


def generate_story_with_retry(api_key: str, landmark_key: str, story_mode: str,
                               user_name: str, companion: str, language: str,
                               max_retries: int = 3) -> tuple:
    """
    Generate a story with automatic retry on failure or quality issues.
    
    Returns:
        tuple: (story_text, error_message, attempts_made)
    """
    if language != "ar":
        # Non-Arabic: generate directly (validation is simpler)
        return _generate_story(api_key, landmark_key, story_mode,
                               user_name, companion, language)
    
    # Arabic: use validated generation with retries
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            story, error = _generate_story_single(
                api_key, landmark_key, story_mode, user_name, companion, language,
                strengthen=(attempt > 1)  # Stronger prompt on retries
            )
            
            if error:
                last_error = error
                continue
            
            # Validate Arabic quality
            is_valid, issues, arabic_ratio = validate_arabic_story(story)
            
            if is_valid:
                return story, None, attempt
            
            last_error = f"Quality issues: {', '.join(issues)}"
            time.sleep(0.3)
            
        except Exception as e:
            last_error = str(e)
            time.sleep(0.3)
    
    return None, f"Failed after {max_retries} attempts. {last_error}", max_retries


def _generate_story(api_key: str, landmark_key: str, story_mode: str,
                    user_name: str, companion: str, language: str) -> tuple:
    """Generate story for non-Arabic languages (single attempt)."""
    story, error = _generate_story_single(
        api_key, landmark_key, story_mode, user_name, companion, language
    )
    return story, error, 1


def _generate_story_single(api_key: str, landmark_key: str, story_mode: str,
                           user_name: str, companion: str, language: str,
                           strengthen: bool = False) -> tuple:
    """
    Single story generation attempt.
    
    Args:
        strengthen: If True, add extra emphasis on language purity (for retries)
    """
    try:
        client = Groq(api_key=api_key or GROQ_API_KEY)
        
        prompt = build_story_prompt(landmark_key, story_mode, user_name, companion, language)
        if not prompt:
            return None, "Could not build prompt - check landmarks data"
        
        system_prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])
        
        # Strengthen prompt on retry
        if strengthen and language == "ar":
            system_prompt += """

تحقق قبل إنهاء الإجابة:
إذا وُجد أي حرف غير عربي في النص، أعد كتابة القصة بالكامل حتى تصبح عربية خالصة مائة بالمائة.

"""
        
        lang_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.75 if language == "ar" else 0.8,
            max_tokens=1500
        )
        
        story = response.choices[0].message.content.strip()
        
        # Post-process Arabic
        if language == "ar":
            story = _clean_arabic_text(story)
        
        return story, None
        
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return None, "Rate limit reached. Please wait a moment and try again."
        elif "invalid_api_key" in error_msg.lower() or "401" in error_msg:
            return None, "Invalid API key. Please check your Groq API key."
        else:
            return None, f"Story Generation Error: {error_msg}"


def _clean_arabic_text(text: str) -> str:
    """Post-process Arabic text to remove English artifacts."""
    # Remove isolated English words between Arabic text
    text = re.sub(r'(?<=[\u0600-\u06FF\s])[a-zA-Z]{3,}(?=[\u0600-\u06FF\s])', '', text)
    # Remove markdown artifacts
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'#+\s*', '', text)
    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()


# ============================================
# QUALITY METRICS
# ============================================

def get_story_quality_score(story: str, language: str) -> dict:
    """
    Calculate quality metrics for a generated story.
    
    Returns dict with overall_score, length_score, language_purity, 
    structure_score, and details.
    """
    scores = {}
    
    # Length score (ideal: 250-400 words)
    word_count = len(story.split())
    if 250 <= word_count <= 400:
        scores['length_score'] = 100
    elif 150 <= word_count < 250 or 400 < word_count <= 500:
        scores['length_score'] = 75
    elif 100 <= word_count < 150 or 500 < word_count <= 600:
        scores['length_score'] = 50
    else:
        scores['length_score'] = 25
    
    # Language purity
    if language == "ar":
        scores['language_purity'] = int(calculate_arabic_ratio(story) * 100)
    else:
        scores['language_purity'] = 95 if not contains_english(story) or language == "en" else 80
    
    # Structure score
    sentence_count = (story.count('.') + story.count('،') + 
                      story.count('؟') + story.count('!') + story.count('?'))
    if sentence_count >= 10:
        scores['structure_score'] = 100
    elif sentence_count >= 7:
        scores['structure_score'] = 75
    elif sentence_count >= 5:
        scores['structure_score'] = 50
    else:
        scores['structure_score'] = 25
    
    # Overall (weighted)
    scores['overall_score'] = int(
        scores['length_score'] * 0.3 +
        scores['language_purity'] * 0.4 +
        scores['structure_score'] * 0.3
    )
    
    scores['details'] = {
        'word_count': word_count,
        'sentence_count': sentence_count,
        'arabic_ratio': calculate_arabic_ratio(story) if language == "ar" else None
    }
    
    return scores


# ============================================
# CACHING
# ============================================

_story_cache = {}

def get_cached_story(cache_key: str) -> str:
    return _story_cache.get(cache_key)

def cache_story(cache_key: str, story: str, max_cache_size: int = 100):
    if len(_story_cache) >= max_cache_size:
        oldest_key = next(iter(_story_cache))
        del _story_cache[oldest_key]
    _story_cache[cache_key] = story


# ============================================
# TEST
# ============================================
if __name__ == "__main__":
    print("🧪 Testing Enhanced Story Generator\n")
    
    test_ar = "هذه قصة باللغة العربية عن قرطاج القديمة وتاريخها العريق"
    test_mixed = "هذه قصة about قرطاج the ancient city"
    
    print("Arabic validation:")
    print(f"  Pure Arabic: {not contains_english(test_ar)} ✓")
    print(f"  Mixed text detected: {contains_english(test_mixed)} ✓")
    print(f"  Arabic ratio (pure): {calculate_arabic_ratio(test_ar):.1%}")
    print(f"  Arabic ratio (mixed): {calculate_arabic_ratio(test_mixed):.1%}")
    
    print("\nPrompt building:")
    prompt = build_story_prompt("carthage", "time_traveler", "أحمد", "solo", "ar")
    print(f"  Arabic prompt built: {'✓' if prompt else '✗'} ({len(prompt)} chars)")
    
    prompt_en = build_story_prompt("dougga", "historian", "Sarah", "couple", "en")
    print(f"  English prompt built: {'✓' if prompt_en else '✗'} ({len(prompt_en)} chars)")