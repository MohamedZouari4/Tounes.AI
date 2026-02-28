"""
TOUNES.AI - Immersive Tunisian Storytelling Platform
====================================================
Enhanced with:
1. Full internationalization (EN/FR/AR) across the entire UI
2. Expanded landmark database (8 landmarks)
3. Improved vision identification with confidence scoring
4. Better error handling and user experience
5. Interactive map view of landmarks
6. Story quality indicators
7. Audio narration with Edge TTS
8. Responsive, polished design
"""

import streamlit as st
import json
import base64
import asyncio
from pathlib import Path

# Import enhanced modules
from enhanced_story_generator import (
    generate_story_with_retry,
    validate_arabic_story,
    get_story_quality_score,
    load_landmarks
)
from vision import identify_landmark, encode_image_to_base64
from audio_generator import generate_audio, TTS_VOICES

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Tounes.AI 📖 تونس",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CONSTANTS
# ============================================
LANGUAGES = {
    "ar": {"name": "العربية", "flag": "🇹🇳", "dir": "rtl"},
    "en": {"name": "English", "flag": "🇬🇧", "dir": "ltr"},
    "fr": {"name": "Français", "flag": "🇫🇷", "dir": "ltr"}
}

# ============================================
# HELPERS
# ============================================

@st.cache_data
def get_landmarks_data():
    """Load and cache landmarks data."""
    return load_landmarks()


def t(key: str, lang: str = None) -> str:
    """
    Get translated UI text.
    Falls back to English if key not found in target language.
    """
    if lang is None:
        lang = st.session_state.get('ui_language', 'ar')
    data = get_landmarks_data()
    if data and "ui_text" in data:
        text_data = data["ui_text"].get(lang, data["ui_text"].get("en", {}))
        if key in text_data:
            return text_data[key]
        # Fallback to English
        return data["ui_text"].get("en", {}).get(key, key)
    return key


def display_quality_badge(score: int) -> str:
    """Return HTML for a quality badge."""
    if score >= 90:
        return f'<span class="quality-badge quality-excellent">⭐ {score}%</span>'
    elif score >= 75:
        return f'<span class="quality-badge quality-good">✓ {score}%</span>'
    elif score >= 50:
        return f'<span class="quality-badge quality-fair">~ {score}%</span>'
    else:
        return f'<span class="quality-badge quality-poor">⚠ {score}%</span>'


# ============================================
# CUSTOM CSS
# ============================================
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');
        
        /* ===== HEADER ===== */
        .main-header {
            text-align: center;
            padding: 2.5rem 2rem;
            background: linear-gradient(135deg, #0a0a23 0%, #1a1a4e 40%, #2d1b69 70%, #1a3a5c 100%);
            border-radius: 24px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 12px 40px rgba(0,0,0,0.35);
            position: relative;
            overflow: hidden;
        }
        .main-header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(233,69,96,0.08) 0%, transparent 60%);
            animation: pulse 8s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 1; }
        }
        .main-header h1 {
            font-family: 'Playfair Display', serif;
            font-size: 3.2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #e94560, #ffbd69, #e94560);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shimmer 3s linear infinite;
            position: relative;
        }
        @keyframes shimmer {
            to { background-position: 200% center; }
        }
        .main-header p { position: relative; }
        
        /* ===== STORY CARD ===== */
        .story-card {
            background: linear-gradient(135deg, #fdf6e3 0%, #fff8e7 50%, #fef9ef 100%);
            padding: 2.5rem;
            border-radius: 24px;
            border: 2px solid #d4a373;
            margin: 1.5rem 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.08);
            font-family: 'Playfair Display', Georgia, serif;
            line-height: 2;
            font-size: 1.12rem;
            color: #2c2c2c;
        }
        .story-card-rtl {
            direction: rtl;
            text-align: right;
            font-family: 'Amiri', serif;
            font-size: 1.4rem;
            line-height: 2.4;
        }
        .story-title {
            font-size: 1.8rem;
            font-weight: bold;
            color: #1a1a2e;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #d4a37355;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        /* ===== BADGES ===== */
        .quality-badge {
            display: inline-block;
            padding: 0.25rem 0.7rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .quality-excellent { background: #28a745; color: white; }
        .quality-good { background: #17a2b8; color: white; }
        .quality-fair { background: #ffc107; color: #333; }
        .quality-poor { background: #dc3545; color: white; }
        
        /* ===== LANDMARK CARDS ===== */
        .landmark-info {
            /* Enhanced landmark flash card: warmer, textured gradient */
            background: linear-gradient(135deg, #fffaf0 0%, #fff1e6 60%, #fff8f0 100%);
            padding: 1.2rem;
            border-radius: 16px;
            border: 1px solid #f5d6a0;
            margin: 0.5rem 0;
            box-shadow: 0 6px 18px rgba(245,214,160,0.12);
            color: #2b2b2b;
        }
        
        /* ===== MODE SELECTOR ===== */
        .mode-card {
            text-align: center;
            padding: 1rem 0.5rem;
            border-radius: 16px;
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .mode-card:hover { border-color: #e94560; transform: translateY(-2px); }
        .mode-card.active { 
            border-color: #e94560; 
            background: linear-gradient(135deg, #fff0f3 0%, #ffe8ec 100%);
        }
        .mode-emoji { font-size: 2rem; }
        .mode-label { font-size: 0.85rem; font-weight: 600; margin-top: 0.3rem; }
        
        /* ===== FUN FACTS ===== */
        .fun-fact {
            /* Enhanced Did You Know card: warm peach with gold accent */
            background: linear-gradient(135deg, #fffaf0 0%, #fff1e6 60%, #fff8f0 100%);
            padding: 1rem 1.2rem;
            border-radius: 12px;
            border-left: 6px solid #f59e0b;
            margin: 0.5rem 0;
            font-size: 0.98rem;
            color: #8B6F47;
            box-shadow: 0 6px 18px rgba(245,214,160,0.12);
            font-family: 'Roboto', sans-serif;
        }
        
        /* ===== SHARE CARD ===== */
        .share-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 24px;
            color: white;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(102,126,234,0.3);
        }
        
        /* ===== BUTTONS ===== */
        .stButton > button {
            background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
            color: white;
            border: none;
            padding: 0.8rem 2rem;
            font-size: 1.05rem;
            border-radius: 30px;
            font-weight: 600;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
        }
        .stButton > button:hover {
            transform: scale(1.03);
            box-shadow: 0 6px 24px rgba(233, 69, 96, 0.4);
        }
        
        /* ===== STATUS BOXES ===== */
        .error-box {
            background: #fff3f3; border: 2px solid #dc3545;
            border-radius: 12px; padding: 1rem 1.2rem; margin: 1rem 0;
        }
        .success-box {
            background: #f0fff0; border: 2px solid #28a745;
            border-radius: 12px; padding: 1rem 1.2rem; margin: 1rem 0;
        }
        
        /* ===== LOADING ===== */
        .loading-text {
            text-align: center;
            font-size: 1.2rem;
            color: #666;
            padding: 2rem;
        }
        
        /* ===== MAP CONTAINER ===== */
        .map-container {
            border-radius: 16px;
            overflow: hidden;
            border: 2px solid #e0e0e0;
            margin: 1rem 0;
        }
        
        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {
            /* Enhanced sidebar: deeper, richer gradient with light text for contrast */
            background: linear-gradient(180deg, #0f172a 0%, #1a3a5c 60%, #284b6a 100%);
            color: #f8fafc;
            box-shadow: inset 0 6px 20px rgba(0,0,0,0.25);
            padding: 1rem 0.8rem;
        }
        /* Ensure sidebar text elements inherit the light color */
        section[data-testid="stSidebar"] * {
            color: inherit !important;
        }
        
        /* ===== MISC ===== */
        .step-header {
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 1.15rem;
            color: #1a1a2e;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================
# DISPLAY COMPONENTS
# ============================================

def display_story(story, landmark_key, language, mode_emoji, quality_score=None):
    """Display the generated story in a styled card."""
    landmarks_data = get_landmarks_data()
    landmark = landmarks_data["landmarks"].get(landmark_key, {})
    landmark_name = landmark["name"].get(language, landmark["name"]["en"])
    
    rtl_class = "story-card-rtl" if language == "ar" else ""
    quality_html = ""
    if quality_score:
        quality_html = display_quality_badge(quality_score.get('overall_score', 0))
    
    # Escape story text for HTML
    story_html = story.replace('\n', '<br>')
    
    st.markdown(f"""
    <div class="story-card {rtl_class}">
        <div class="story-title">
            <span>{mode_emoji} {landmark_name}</span>
            {quality_html}
        </div>
        <p>{story_html}</p>
    </div>
    """, unsafe_allow_html=True)


def display_landmark_map(landmarks_data):
    """Display an interactive map of all landmarks."""
    import pandas as pd
    
    map_data = []
    for key, data in landmarks_data.get("landmarks", {}).items():
        coords = data.get("coordinates", [0, 0])
        map_data.append({
            "lat": coords[0],
            "lon": coords[1],
            "name": data["name"]["en"]
        })
    
    if map_data:
        df = pd.DataFrame(map_data)
        st.map(df, latitude="lat", longitude="lon", zoom=6)


# ============================================
# MAIN APPLICATION
# ============================================

def main():
    inject_css()
    landmarks_data = get_landmarks_data()
    
    if not landmarks_data:
        st.error("❌ Could not load landmarks data. Please check landmarks_data.json.")
        return
    
    # ---- Initialize session state ----
    defaults = {
        'ui_language': 'ar',
        'selected_mode': 'time_traveler',
        'generated_story': None,
        'audio_data': None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    
    ui_lang = st.session_state['ui_language']
    
    # ---- Header ----
    logo_path = Path("Logo.png")
    if logo_path.exists():
        st.image(str(logo_path), width=120)
    st.markdown(f"""
        <div class="main-header">
        <h1>📖 Tounes.AI تونس</h1>
        <p style="font-size: 1.3rem; opacity: 0.9;">{t('app_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ---- Sidebar ----
    with st.sidebar:
        st.markdown(f"## {t('settings')}")
        
        # UI Language selector
        ui_lang_choice = st.selectbox(
            "🌐 Interface Language",
            list(LANGUAGES.keys()),
            format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}",
            index=list(LANGUAGES.keys()).index(st.session_state['ui_language'])
        )
        if ui_lang_choice != st.session_state['ui_language']:
            st.session_state['ui_language'] = ui_lang_choice
            st.rerun()
        
        st.markdown("---")
        
        # API Key
        api_key = st.text_input(
            t('api_key_label'),
            type="password",
            help=t('api_key_help')
        )
        
        if not api_key:
            st.warning(t('enter_api_key'))
            st.markdown(t('how_to_get_key'))
        else:
            st.success(t('api_ready'))
        
        st.markdown("---")
        
        # Quality settings
        st.markdown(f"### {t('quality_settings')}")
        auto_retry = st.checkbox(t('auto_retry'), value=True)
        show_quality = st.checkbox(t('show_quality'), value=True)
        
        st.markdown("---")
        
        # About
        st.markdown(f"### {t('about_title')}")
        st.markdown(t('about_text'))
        
        # Landmark map
        st.markdown("---")
        st.markdown("### 🗺️ Landmarks Map")
        display_landmark_map(landmarks_data)
    
    # ---- Main Content ----
    col1, col2 = st.columns([1, 1], gap="large")
    
    selected_landmark = None
    
    with col1:
        st.markdown(f"### {t('step1')}")
        
        input_method = st.radio(
            " ",
            [t('upload_photo'), t('choose_from_list')],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if input_method == t('upload_photo'):
            uploaded_file = st.file_uploader(
                t('upload_prompt'),
                type=["jpg", "jpeg", "png", "webp"]
            )
            
            if uploaded_file:
                st.image(uploaded_file, use_container_width=True)
                
                if api_key:
                    with st.spinner("🔍 ..."):
                        image_base64 = encode_image_to_base64(uploaded_file)
                        image_type = f"image/{uploaded_file.type.split('/')[-1]}"
                        
                        landmark_key, confidence, error = identify_landmark(
                            api_key, image_base64, image_type
                        )
                        
                        if error:
                            st.error(f"❌ {error}")
                        elif landmark_key == "unknown":
                            st.warning(t('unknown_landmark'))
                            _landmark_options = {
                                v["name"].get(ui_lang, v["name"]["en"]): k
                                for k, v in landmarks_data["landmarks"].items()
                            }
                            selected_name = st.selectbox(
                                t('choose_landmark'),
                                list(_landmark_options.keys())
                            )
                            selected_landmark = _landmark_options[selected_name]
                        else:
                            ln = landmarks_data["landmarks"][landmark_key]["name"]
                            display_name = ln.get(ui_lang, ln["en"])
                            conf = confidence.get('confidence', '') if confidence else ''
                            st.success(f"{t('identified')}: **{display_name}** ({conf})")
                            selected_landmark = landmark_key
                else:
                    st.info(t('enter_api_key'))
        else:
            _landmark_options = {
                v["name"].get(ui_lang, v["name"]["en"]): k
                for k, v in landmarks_data["landmarks"].items()
            }
            selected_name = st.selectbox(
                t('choose_landmark'),
                list(_landmark_options.keys())
            )
            selected_landmark = _landmark_options[selected_name]
            
            # Show landmark info
            landmark = landmarks_data["landmarks"][selected_landmark]
            ln = landmark["name"]
            name_display = f"{ln.get(ui_lang, ln['en'])}"
            if ui_lang != "en":
                name_display += f" ({ln['en']})"
            
            tags = []
            if landmark.get("unesco"):
                tags.append("🏛️ UNESCO")
            tags.append(f"📍 {landmark.get('region', '')}")
            tags.append(f"⏱️ ~{landmark.get('visit_duration_hours', '?')}h")
            
            st.markdown(f"""
            <div class="landmark-info">
                <strong>{name_display}</strong><br>
                <small>{'  •  '.join(tags)}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"### {t('step2')}")
        
        user_name = st.text_input(
            t('your_name'),
            placeholder=t('name_placeholder')
        )
        
        # Companion
        companions_text = t('companions')
        if isinstance(companions_text, dict):
            companion = st.selectbox(
                t('companion_label'),
                list(companions_text.keys()),
                format_func=lambda x: companions_text[x]
            )
        else:
            companion = st.selectbox(
                t('companion_label'),
                ["solo", "couple", "family", "friends"]
            )
        
        # Story language
        language = st.selectbox(
            t('language_label'),
            list(LANGUAGES.keys()),
            format_func=lambda x: f"{LANGUAGES[x]['flag']} {LANGUAGES[x]['name']}",
            index=0
        )
    
    # ---- Story Mode Selection ----
    st.markdown("---")
    st.markdown(f"### {t('step3')}")
    
    modes = landmarks_data.get("story_modes", {})
    mode_cols = st.columns(len(modes))
    
    for i, (mode_key, mode_data) in enumerate(modes.items()):
        with mode_cols[i]:
            mode_name = mode_data.get("name", {}).get(ui_lang, mode_key)
            is_active = st.session_state['selected_mode'] == mode_key
            
            if st.button(
                f"{mode_data['emoji']}\n{mode_name}",
                key=f"mode_{mode_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state['selected_mode'] = mode_key
                st.rerun()
    
    selected_mode = st.session_state['selected_mode']
    mode_info = modes.get(selected_mode, {})
    mode_desc = mode_info.get("description", {}).get(ui_lang, "")
    if mode_desc:
        st.caption(f"{mode_info.get('emoji', '')} {mode_desc}")
    
    # ---- Generate Button ----
    st.markdown("---")
    
    can_generate = api_key and selected_landmark and user_name
    
    if not can_generate:
        missing = []
        if not api_key:
            missing.append(t('api_key_label'))
        if not selected_landmark:
            missing.append(t('step1'))
        if not user_name:
            missing.append(t('your_name'))
    
    if st.button(t('generate_btn'), disabled=not can_generate, use_container_width=True):
        progress = st.empty()
        
        with st.spinner(""):
            progress.markdown(f"""
            <div class="loading-text">
                {t('generating')}<br>
                <small>⏳ ~30s</small>
            </div>
            """, unsafe_allow_html=True)
            
            max_retries = 3 if auto_retry else 1
            
            story, error, attempts = generate_story_with_retry(
                api_key=api_key,
                landmark_key=selected_landmark,
                story_mode=selected_mode,
                user_name=user_name,
                companion=companion,
                language=language,
                max_retries=max_retries
            )
            
            progress.empty()
            
            if error:
                st.markdown(f"""
                <div class="error-box">
                    <h4>❌ Error</h4>
                    <p>{error}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Save to session state
                st.session_state['generated_story'] = story
                st.session_state['story_landmark'] = selected_landmark
                st.session_state['story_language'] = language
                st.session_state['story_mode'] = selected_mode
                st.session_state['story_user'] = user_name
                st.session_state['generation_attempts'] = attempts
                
                if show_quality:
                    quality = get_story_quality_score(story, language)
                    st.session_state['story_quality'] = quality
                
                st.rerun()
    
    # ---- Display Generated Story ----
    if st.session_state.get('generated_story'):
        st.markdown("---")
        st.markdown(f"## {t('your_story')}")
        
        story = st.session_state['generated_story']
        landmark_key = st.session_state.get('story_landmark', '')
        lang = st.session_state.get('story_language', 'en')
        mode = st.session_state.get('story_mode', 'time_traveler')
        quality = st.session_state.get('story_quality')
        
        mode_emoji = modes.get(mode, {}).get("emoji", "📖")
        
        display_story(story, landmark_key, lang, mode_emoji, quality)
        
        # Quality details
        if quality and show_quality:
            with st.expander(t('quality_details')):
                qc1, qc2, qc3, qc4 = st.columns(4)
                with qc1:
                    st.metric("🏆 Overall", f"{quality['overall_score']}%")
                with qc2:
                    st.metric(f"📏 {t('word_count')}", f"{quality['details']['word_count']}")
                with qc3:
                    st.metric(f"🔤 {t('language_purity')}", f"{quality['language_purity']}%")
                with qc4:
                    st.metric(f"📐 {t('structure')}", f"{quality['structure_score']}%")
        
        # ---- Audio Narration ----
        st.markdown(f"### {t('listen_title')}")
        
        if st.button(t('generate_audio_btn'), use_container_width=True):
            with st.spinner(t('recording')):
                audio_data, error = generate_audio(story, lang)
                if error:
                    st.warning(f"⚠️ {error}")
                else:
                    st.session_state['audio_data'] = audio_data
        
        if st.session_state.get('audio_data'):
            st.audio(st.session_state['audio_data'], format="audio/mp3")
        
        # Share card removed per request; keep landmark/user variables for later sections
        landmark = landmarks_data["landmarks"].get(landmark_key, {})
        landmark_name = landmark.get("name", {}).get(lang, landmark.get("name", {}).get("en", ""))
        user = st.session_state.get('story_user', '')
        
        # ---- Fun Facts ----
        st.markdown(f"### {t('fun_facts_title')}")
        fun_facts = landmark.get("fun_facts", {}).get(lang, landmark.get("fun_facts", {}).get("en", []))
        for fact in fun_facts:
            st.markdown(f'<div class="fun-fact">💡 {fact}</div>', unsafe_allow_html=True)
        
        # ---- Download & Reset ----
        dl_col, reset_col = st.columns(2)
        with dl_col:
            st.download_button(
                t('download_btn'),
                story,
                file_name=f"tounes_story_{landmark_key}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with reset_col:
            if st.button(t('new_story_btn'), use_container_width=True):
                for key in ['generated_story', 'audio_data', 'story_landmark',
                           'story_language', 'story_mode', 'story_user', 
                           'story_quality', 'generation_attempts']:
                    st.session_state.pop(key, None)
                st.rerun()


if __name__ == "__main__":
    main()