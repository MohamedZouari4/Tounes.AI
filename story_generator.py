"""
PART 4: Story Generator Module
==============================
This module handles:
1. Building rich prompts with landmark context
2. Applying different story modes (historian, legend keeper, etc.)
3. Personalizing stories with user's name
4. Supporting multiple languages
"""

import json
from pathlib import Path
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def load_landmarks():
    """Load landmark data from JSON file"""
    data_path = Path(__file__).parent / "landmarks_data.json"
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


# Story mode instructions - tells AI how to write
STORY_MODE_INSTRUCTIONS = {
    "historian": """
Write as a knowledgeable historian sharing fascinating facts.
- Be educational but engaging
- Include specific dates, names, and historical context
- Use phrases like "Historical records tell us..." or "Archaeologists discovered..."
- Balance facts with narrative flow
""",
    
    "legend_keeper": """
Write as a mystical storyteller sharing ancient legends and local myths.
- Create an atmosphere of mystery and wonder
- Include supernatural elements and folklore
- Use phrases like "The old ones say..." or "Legend whispers that..."
- Make the reader feel they're hearing a secret
""",
    
    "time_traveler": """
Write in SECOND PERSON PRESENT TENSE - the reader IS there experiencing history.
- Use "You stand...", "You hear...", "You feel...", "You see..."
- Make it viscerally immersive with all five senses
- The reader is the protagonist living in that moment
- Example: "You stand where Hannibal once stood. The wind carries whispers of elephants..."
""",
    
    "romantic": """
Write with poetic beauty, focusing on love and emotional resonance.
- Include romantic legends or create a sense of timeless beauty
- Use lyrical, flowing language
- Focus on beauty, emotion, and connection
- Make the reader feel moved
""",
    
    "kids_adventure": """
Write for children ages 6-10.
- Use simple vocabulary and short sentences
- Make history feel like an exciting adventure
- Include fun facts and questions to engage young minds
- Add excitement: "Can you imagine...?" "Guess what happened next!"
- Keep it educational but FUN
""",
    
    "movie_director": """
Write like a movie script or cinematic narration.
- Use visual language and dramatic pacing
- Set scenes like a film: "The camera pans across...", "We see...", "Cut to..."
- Build tension and atmosphere
- Make the reader visualize epic scenes
"""
}

# Language-specific instructions
LANGUAGE_INSTRUCTIONS = {
    "en": "Write in English. Use vivid, literary prose.",
    "fr": "Écrivez en français. Utilisez une prose vivante et littéraire.",
    "ar": "اكتب بالعربية الفصحى مع لمسة تونسية. استخدم نثراً أدبياً حيوياً وجميلاً."
}

# Companion context
COMPANION_CONTEXT = {
    "solo": "traveling alone, seeking personal discovery and reflection",
    "couple": "with their romantic partner, sharing this special moment together",
    "family": "with their family, including curious children",
    "friends": "with a group of friends, having an adventure together"
}


def build_story_prompt(landmark_key: str, story_mode: str, user_name: str, 
                       companion: str, language: str):
    """
    Build a detailed prompt for story generation.
    
    This is the most important function - good prompts = good stories!
    
    Args:
        landmark_key: e.g., "carthage", "sidi_bou_said"
        story_mode: e.g., "historian", "time_traveler"
        user_name: The user's name to include in story
        companion: Who they're traveling with
        language: "en", "fr", or "ar"
        
    Returns:
        str: Complete prompt for the LLM
    """
    
    # Load landmark data
    landmarks_data = load_landmarks()
    if not landmarks_data:
        return None
    
    landmark = landmarks_data["landmarks"].get(landmark_key, {})
    mode_info = landmarks_data["story_modes"].get(story_mode, {})
    
    # Extract landmark information in the requested language
    landmark_name = landmark["name"].get(language, landmark["name"]["en"])
    history = landmark.get("history", {}).get(language, landmark.get("history", {}).get("en", ""))
    legends = landmark.get("legends", {}).get(language, landmark.get("legends", {}).get("en", ""))
    atmosphere = landmark.get("atmosphere", {})
    fun_facts = landmark.get("fun_facts", {}).get(language, [])
    
    # Build the prompt
    prompt = f"""You are Rawi (راوي), the legendary Tunisian storyteller. Your voice has echoed through medinas for generations. You have the gift of making the past come alive.

## YOUR MISSION
Create an immersive, personalized story about **{landmark_name}** for **{user_name}**, who is {COMPANION_CONTEXT.get(companion, 'exploring')}.

## STORY MODE: {mode_info.get('emoji', '')} {mode_info.get('name', {}).get('en', story_mode)}
{STORY_MODE_INSTRUCTIONS.get(story_mode, '')}

## LANDMARK KNOWLEDGE
Use this information to enrich your story:

**Historical Facts:**
{history}

**Legends & Myths:**
{legends}

**Atmosphere - What {user_name} experiences:**
- Sights: {', '.join(atmosphere.get('sights', []))}
- Sounds: {', '.join(atmosphere.get('sounds', []))}
- Smells: {', '.join(atmosphere.get('smells', []))}

**Fun Facts:**
{chr(10).join(f'- {fact}' for fact in fun_facts)}

## LANGUAGE
{LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS['en'])}

## PERSONALIZATION RULES
1. Include {user_name}'s name naturally 2-3 times in the story
2. Reference their companion situation ({companion})
3. Make them feel like the protagonist
4. End with something memorable they can take with them

## OUTPUT REQUIREMENTS
- Write 250-400 words
- Pure flowing narrative - NO headers, NO bullet points
- Make it emotional, sensory, and unforgettable
- Transport the reader to this place

Begin your story now:"""

    return prompt


def generate_story(api_key: str, landmark_key: str, story_mode: str,
                   user_name: str, companion: str, language: str):
    """
    Generate a personalized story using Groq LLM.
    
    Args:
        api_key: Groq API key
        landmark_key: Which landmark (e.g., "carthage")
        story_mode: Story style (e.g., "time_traveler")
        user_name: User's name for personalization
        companion: Who they're with
        language: Output language
        
    Returns:
        tuple: (story_text, error_message)
    """
    try:
        # Initialize Groq client
        client = Groq(api_key=GROQ_API_KEY)
        
        # Build the prompt
        prompt = build_story_prompt(
            landmark_key, story_mode, user_name, companion, language
        )
        
        if not prompt:
            return None, "Could not build prompt - check landmarks data"
        
        # Language names for system message
        lang_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        
        # Call Groq LLM
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Best model for storytelling
            messages=[
                {
                    "role": "system",
                    "content": f"You are Rawi, a master Tunisian storyteller. You speak in {lang_names.get(language, 'English')}. Your stories transport people through time and space. You never use headers, bullet points, or formatting - only beautiful flowing prose."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.8,   # Higher = more creative
            max_tokens=1500    # Enough for ~400 words
        )
        
        # Extract the story
        story = response.choices[0].message.content.strip()
        
        return story, None
        
    except Exception as e:
        return None, f"Story Generation Error: {str(e)}"


# ============================================
# TEST THIS MODULE
# ============================================
if __name__ == "__main__":
    """
    Test the story generator standalone.
    
    To test:
    1. Set your API key below
    2. Run: python story_generator.py
    """
    
    TEST_API_KEY = GROQ_API_KEY # This will be loaded from .env
    
    print("🎭 Testing Story Generator...\n")
    
    story, error = generate_story(
        api_key=TEST_API_KEY,
        landmark_key="carthage",
        story_mode="time_traveler",
        user_name="Ahmed",
        companion="alone",
        language="ar"
    )
    
    if error:
        print(f"❌ Error: {error}")
    else:
        print("✅ Generated Story:\n")
        print("-" * 50)
        print(story)
        print("-" * 50)