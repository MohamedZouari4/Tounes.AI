"""
STORY GENERATOR MODULE (Backward-Compatible Wrapper)
=====================================================
This module maintains backward compatibility while delegating
to the enhanced story generator for actual generation.
"""

import json
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


# Language-specific instructions
LANGUAGE_INSTRUCTIONS = {
    "en": "Write in English. Use vivid, literary prose.",
    "fr": "Écrivez en français. Utilisez une prose vivante et littéraire.",
    "ar": "اكتب بالعربية الفصحى مع لمسة تونسية. استخدم نثراً أدبياً حيوياً وجميلاً."
}

COMPANION_CONTEXT = {
    "solo": "traveling alone, seeking personal discovery and reflection",
    "couple": "with their romantic partner, sharing this special moment together",
    "family": "with their family, including curious children",
    "friends": "with a group of friends, having an adventure together"
}


def generate_story(api_key: str, landmark_key: str, story_mode: str,
                   user_name: str, companion: str, language: str):
    """
    Generate a personalized story using Groq LLM.
    
    This function is maintained for backward compatibility.
    For new code, use enhanced_story_generator.generate_story_with_retry().
    """
    try:
        from enhanced_story_generator import generate_story_with_retry
        story, error, _attempts = generate_story_with_retry(
            api_key=api_key or GROQ_API_KEY,
            landmark_key=landmark_key,
            story_mode=story_mode,
            user_name=user_name,
            companion=companion,
            language=language,
            max_retries=1
        )
        return story, error
    except ImportError:
        # Fallback: use basic generation
        return _basic_generate(api_key, landmark_key, story_mode,
                               user_name, companion, language)


def _basic_generate(api_key, landmark_key, story_mode, user_name, companion, language):
    """Basic story generation fallback."""
    try:
        client = Groq(api_key=api_key or GROQ_API_KEY)
        landmarks_data = load_landmarks()
        
        if not landmarks_data:
            return None, "Could not load landmarks data"
        
        landmark = landmarks_data["landmarks"].get(landmark_key, {})
        landmark_name = landmark["name"].get(language, landmark["name"]["en"])
        history = landmark.get("history", {}).get(language, "")
        
        lang_names = {"en": "English", "fr": "French", "ar": "Arabic"}
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"You are Tounes, a master Tunisian storyteller. Write in {lang_names.get(language, 'English')}. Only flowing prose, no formatting."
                },
                {
                    "role": "user",
                    "content": f"Write a 300-word immersive story about {landmark_name} for {user_name} who is {COMPANION_CONTEXT.get(companion, 'exploring')}. History: {history}"
                }
            ],
            temperature=0.8,
            max_tokens=1500
        )
        
        return response.choices[0].message.content.strip(), None
        
    except Exception as e:
        return None, f"Story Generation Error: {str(e)}"


if __name__ == "__main__":
    print("🎭 Story Generator Module (backward-compatible wrapper)")
    print("For production use, import from enhanced_story_generator instead.")