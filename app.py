"""
PART 6: Main Application - Tounes.AI
===================================
This is the main Streamlit app that brings together:
- Vision (landmark identification)
- Story Generator (personalized stories)
- Audio Generator (text-to-speech)

Run with: streamlit run app.py
"""

import streamlit as st
import json
from pathlib import Path

# Import our modules (from Parts 3, 4, 5)
from vision import encode_image_to_base64, identify_landmark, load_landmarks
from story_generator import generate_story
from audio_generator import generate_audio
import warnings
warnings.filterwarnings("ignore", message="missing ScriptRunContext")


# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Tounes.AI",
    page_icon="📖",
    layout="wide"
)


# ============================================
# CUSTOM CSS STYLING
# ============================================
st.markdown("""
<style>
    /* Import beautiful fonts */
    @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Playfair+Display:wght@400;700&family=Roboto:wght@400;700&display=swap');
    
    /* Main header styling */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
    }
    
    .main-header h1 {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        background: linear-gradient(90deg, #e94560, #ffbd69);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Story card styling */
    .story-card {
        background: linear-gradient(135deg, #fdf6e3 0%, #fff8e7 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 3px solid #d4a373;
        font-family: 'Roboto', 'Playfair Display', Georgia, serif;
        line-height: 1.8;
        font-size: 1.1rem;
        color: #8B6F47;
    }
    
    /* Arabic text styling (right-to-left) */
    .story-card-rtl {
        direction: rtl;
        text-align: right;
        font-family: 'Amiri', serif;
        font-size: 1.3rem;
        line-height: 2;
    }
    
    /* Fun fact box */
    .fun-fact {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
        color: #8B6F47;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        border-radius: 30px;
        font-weight: 600;
    }
    
    /* Share card */
    .share-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# LANGUAGE CONFIGURATION
# ============================================
LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "fr": {"name": "Français", "flag": "🇫🇷"},
    "ar": {"name": "العربية", "flag": "🇹🇳"}
}


# ============================================
# HELPER FUNCTIONS
# ============================================
def get_landmarks_data():
    """Load and cache landmarks data"""
    return load_landmarks()


def display_story(story: str, landmark_key: str, language: str, mode_emoji: str):
    """Display the generated story beautifully"""
    
    landmarks_data = get_landmarks_data()
    landmark = landmarks_data["landmarks"].get(landmark_key, {})
    landmark_name = landmark["name"].get(language, landmark["name"]["en"])
    
    # Add RTL class for Arabic
    rtl_class = "story-card-rtl" if language == "ar" else ""
    
    st.markdown(f"""
    <div class="story-card {rtl_class}">
        <h2>{mode_emoji} {landmark_name}</h2>
        <p>{story}</p>
    </div>
    """, unsafe_allow_html=True)


def display_share_card(landmark_name: str, user_name: str, mode_emoji: str):
    """Display shareable card"""
    st.markdown(f"""
    <div class="share-card">
        <div style="font-size: 4rem;">{mode_emoji}</div>
        <h2>{user_name}'s Journey to {landmark_name}</h2>
        <p style="opacity: 0.8;">Created with Tounes.AI </p>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# MAIN APPLICATION
# ============================================
def main():
    # Load landmarks data
    landmarks_data = get_landmarks_data()
    
    # ==================
    # HEADER
    # ==================
    st.markdown("""
    <div class="main-header">
        <h1>📖 Tounes.AI</h1>
        <p style="font-size: 1.3rem; opacity: 0.9;">Transform Tunisian Landmarks into Immersive Stories</p>
        <p style="font-size: 1rem; opacity: 0.7;">حوّل المعالم التونسية إلى قصص غامرة</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================
    # SIDEBAR - API KEY
    # ==================
    with st.sidebar:
        st.markdown("## ⚙️ Setup")
        
        api_key = st.text_input(
            "Groq API Key (Free!)",
            type="password",
            help="Get your free key at console.groq.com"
        )
        
        if not api_key:
            st.warning("👆 Enter your API key to start")
            st.markdown("""
            **Get your FREE key:**
            1. Go to [console.groq.com](https://console.groq.com)
            2. Sign up with Google
            3. Copy your API key
            """)
        else:
            st.success("✅ Ready!")
        
        st.markdown("---")
        st.markdown("### About tounes.ai")
        st.markdown("""
        **Tounes**  means "storyteller" in Arabic.
        
        Built for **AINC'26** 🇹🇳
        """)
    
    # ==================
    # MAIN CONTENT
    # ==================
    col1, col2 = st.columns([1, 1])
    
    # ------------------
    # LEFT COLUMN: Landmark Selection
    # ------------------
    with col1:
        st.markdown("### 📸 Step 1: Choose Your Landmark")
        
        input_method = st.radio(
            "How would you like to select?",
            ["📷 Upload Photo", "📍 Select from List"],
            horizontal=True
        )
        
        selected_landmark = None
        
        if input_method == "📷 Upload Photo":
            uploaded_file = st.file_uploader(
                "Upload a photo of a Tunisian landmark",
                type=["jpg", "jpeg", "png", "webp"]
            )
            
            if uploaded_file:
                st.image(uploaded_file, caption="Your photo", use_container_width=True)
                
                if api_key:
                    with st.spinner("🔍 Identifying landmark..."):
                        image_base64 = encode_image_to_base64(uploaded_file)
                        image_type = f"image/{uploaded_file.type.split('/')[-1]}"
                        
                        landmark_key, error = identify_landmark(api_key, image_base64, image_type)
                        
                        if error:
                            st.error(f"Error: {error}")
                        elif landmark_key == "unknown":
                            st.warning("🤔 Couldn't identify. Please select manually:")
                            landmark_options = {v["name"]["en"]: k for k, v in landmarks_data["landmarks"].items()}
                            selected_name = st.selectbox("Select landmark", list(landmark_options.keys()))
                            selected_landmark = landmark_options[selected_name]
                        else:
                            landmark_name = landmarks_data["landmarks"][landmark_key]["name"]["en"]
                            st.success(f"✅ Identified: **{landmark_name}**")
                            selected_landmark = landmark_key
        else:
            # Select from list
            landmark_options = {v["name"]["en"]: k for k, v in landmarks_data["landmarks"].items()}
            selected_name = st.selectbox("Choose a landmark", list(landmark_options.keys()))
            selected_landmark = landmark_options[selected_name]
            
            # Show info
            landmark = landmarks_data["landmarks"][selected_landmark]
            st.info(f"📍 {landmark['name']['en']} ({landmark['name']['ar']})")
    
    # ------------------
    # RIGHT COLUMN: Personalization
    # ------------------
    with col2:
        st.markdown("### 👤 Step 2: Personalize Your Story")
        
        user_name = st.text_input(
            "Your Name",
            placeholder="Enter your name..."
        )
        
        companion = st.selectbox(
            "Who are you with?",
            ["solo", "couple", "family", "friends"],
            format_func=lambda x: {
                "solo": "🚶 Traveling Solo",
                "couple": "💑 With My Partner",
                "family": "👨‍👩‍👧‍👦 With Family",
                "friends": "👥 With Friends"
            }[x]
        )
        
        language = st.selectbox(
            "Story Language",
            list(LANGUAGES.keys()),
            format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}"
        )
    
    # ==================
    # STORY MODE SELECTION
    # ==================
    st.markdown("---")
    st.markdown("### 🎭 Step 3: Choose Your Story Style")
    
    modes = landmarks_data.get("story_modes", {})
    mode_cols = st.columns(6)
    
    # Default mode
    if 'selected_mode' not in st.session_state:
        st.session_state['selected_mode'] = 'time_traveler'
    
    for i, (mode_key, mode_data) in enumerate(modes.items()):
        with mode_cols[i]:
            if st.button(
                f"{mode_data['emoji']}\n{mode_data['name']['en']}",
                key=f"mode_{mode_key}",
                use_container_width=True
            ):
                st.session_state['selected_mode'] = mode_key
    
    selected_mode = st.session_state['selected_mode']
    mode_info = modes[selected_mode]
    st.info(f"**Selected:** {mode_info['emoji']} {mode_info['name'][language]}")
    
    # ==================
    # GENERATE BUTTON
    # ==================
    st.markdown("---")
    
    can_generate = api_key and selected_landmark and user_name
    
    if st.button("✨ Generate My Story", disabled=not can_generate, use_container_width=True):
        
        with st.spinner("📖 Tounes is crafting your story..."):
            story, error = generate_story(
                api_key=api_key,
                landmark_key=selected_landmark,
                story_mode=selected_mode,
                user_name=user_name,
                companion=companion,
                language=language
            )
            
            if error:
                st.error(f"Error: {error}")
            else:
                # Save to session state
                st.session_state['generated_story'] = story
                st.session_state['story_landmark'] = selected_landmark
                st.session_state['story_language'] = language
                st.session_state['story_mode'] = selected_mode
                st.session_state['story_user'] = user_name
    
    # ==================
    # DISPLAY GENERATED STORY
    # ==================
    if 'generated_story' in st.session_state:
        st.markdown("---")
        st.markdown("## 📖 Your Story")
        
        story = st.session_state['generated_story']
        landmark_key = st.session_state['story_landmark']
        lang = st.session_state['story_language']
        mode = st.session_state['story_mode']
        
        mode_emoji = modes[mode]["emoji"]
        
        # Display the story
        display_story(story, landmark_key, lang, mode_emoji)
        
        # ------------------
        # AUDIO SECTION
        # ------------------
        st.markdown("### 🔊 Listen to Your Story")
        
        if st.button("🎧 Generate Audio Narration", use_container_width=True):
            with st.spinner("🎙️ Recording narration..."):
                audio_data, error = generate_audio(story, lang)
                
                if error:
                    st.warning(f"Audio note: {error}")
                else:
                    st.session_state['audio_data'] = audio_data
        
        if 'audio_data' in st.session_state:
            st.audio(st.session_state['audio_data'], format="audio/mp3")
        
        # ------------------
        # SHARE CARD
        # ------------------
        st.markdown("### 📤 Share Your Experience")
        landmark = landmarks_data["landmarks"][landmark_key]
        landmark_name = landmark["name"].get(lang, landmark["name"]["en"])
        display_share_card(landmark_name, st.session_state['story_user'], mode_emoji)
        
        # ------------------
        # FUN FACTS
        # ------------------
        st.markdown("### 💡 Did You Know?")
        fun_facts = landmark.get("fun_facts", {}).get(lang, landmark.get("fun_facts", {}).get("en", []))
        for fact in fun_facts:
            st.markdown(f'<div class="fun-fact">💡 {fact}</div>', unsafe_allow_html=True)
        
        # ------------------
        # DOWNLOAD
        # ------------------
        st.download_button(
            "📥 Download Story",
            story,
            file_name=f"Tounes{landmark_key}.txt",
            mime="text/plain"
        )
        
        # ------------------
        # NEW STORY BUTTON
        # ------------------
        if st.button("🔄 Create Another Story"):
            for key in ['generated_story', 'audio_data', 'story_landmark', 
                       'story_language', 'story_mode', 'story_user']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()


# ============================================
# RUN THE APP
# ============================================
if __name__ == "__main__":
    main()