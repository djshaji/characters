import sys
from pathlib import Path
import sqlite3
import streamlit as st

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.engine.prompt_engine import ShakespearePersona

DB_PATH = PROJECT_ROOT / "data/processed/shakespeare.db"

st.set_page_config(
    page_title="Characters: Shakespeare Canon in Silico",
    page_icon="🎭",
    layout="wide"
)

@st.cache_data
def get_plays():
    conn = sqlite3.connect(DB_PATH)
    plays = conn.execute("SELECT play_id, title FROM plays ORDER BY title").fetchall()
    conn.close()
    return plays

@st.cache_data
def get_characters(play_id):
    conn = sqlite3.connect(DB_PATH)
    chars = conn.execute("""
        SELECT speaker_id, MAX(speaker_raw), COUNT(*) as lines
        FROM dialogue_turns
        WHERE play_id = ?
        GROUP BY speaker_id
        HAVING lines > 2
        ORDER BY lines DESC
    """, (play_id,)).fetchall()
    conn.close()
    return chars

@st.cache_data
def get_max_acts_scenes(play_id):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT act, MAX(scene) FROM scenes WHERE play_id = ? GROUP BY act", (play_id,)).fetchall()
    conn.close()
    return {act: max_sc for act, max_sc in rows}

def get_on_stage_witnesses(play_id, act, scene):
    conn = sqlite3.connect(DB_PATH)
    witnesses = conn.execute("""
        SELECT DISTINCT witness_id 
        FROM turn_witnesses 
        WHERE play_id = ? AND act = ? AND scene = ?
    """, (play_id, act, scene)).fetchall()
    conn.close()
    return [w[0] for w in witnesses]

# --- SIDEBAR CONFIGURATION ---
st.sidebar.title("🎭 Shakespeare in Silico")
st.sidebar.markdown("*Epistemic Persona Engine & Metrical Scansion*")

# Backend Selector
backend = st.sidebar.radio("Inference Backend", ["ollama", "gemini"], horizontal=True)
if backend == "ollama":
    model_name = st.sidebar.text_input("Ollama Model", value="qwen2.5:3b")
else:
    model_name = st.sidebar.text_input("Gemini Model", value="gemini-2.0-flash")

st.sidebar.divider()

# Play Selection
plays = get_plays()
play_titles = {p[1]: p[0] for p in plays}
selected_title = st.sidebar.selectbox("Select Play", list(play_titles.keys()), index=0)
selected_play_id = play_titles[selected_title]

# Character Selection
characters = get_characters(selected_play_id)
char_dict = {f"{c[1] or c[0]} ({c[2]} speeches)": c[0] for c in characters}
selected_char_label = st.sidebar.selectbox("Select Persona", list(char_dict.keys()), index=0)
selected_char_id = char_dict[selected_char_label]

# Act & Scene Sliders
act_scene_map = get_max_acts_scenes(selected_play_id)
acts = sorted(list(act_scene_map.keys())) if act_scene_map else [1]
selected_act = st.sidebar.select_slider("Act", options=acts, value=acts[0])

max_scenes = act_scene_map.get(selected_act, 1)
selected_scene = st.sidebar.slider("Scene", min_value=1, max_value=max_scenes, value=1)

st.sidebar.divider()

# Sociolect and Verse Controls
user_role = st.sidebar.selectbox(
    "Your Assigned Station", 
    ["peer", "monarch", "servant", "commoner"], 
    index=0,
    help="'peer'/'monarch' elicit respectful 'you/ye'; 'servant'/'commoner' elicit 'thou/thee'."
)
force_meter = st.sidebar.radio("Speech Medium", ["verse", "prose"], horizontal=True)

# --- MAIN CHAT PANEL ---
st.title(f"Chat with {selected_char_id.upper()}")
st.caption(f"**Play:** *{selected_title}* | **Dramatic Timeline:** Act {selected_act}, Scene {selected_scene}")

# Epistemic Inspector (Collapsible)
with st.expander("🔍 Epistemic Horizon & Stage Presence Inspector", expanded=False):
    on_stage = get_on_stage_witnesses(selected_play_id, selected_act, selected_scene)
    st.markdown(f"**Characters Recorded On Stage in this Scene:** `{', '.join(on_stage) if on_stage else 'Scene Entrance'}`")
    st.info(f"The persona of **{selected_char_id.title()}** has zero knowledge of any events, murders, reveals, or deaths occurring after **Act {selected_act}, Scene {selected_scene}**.")

# Chat History Session State
session_key = f"chat_{selected_play_id}_{selected_char_id}_{selected_act}_{selected_scene}"
if session_key not in st.session_state:
    st.session_state[session_key] = []

# Display conversation
for msg in st.session_state[session_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "scansion" in msg and msg["scansion"]:
            sc = msg["scansion"]
            st.caption(f"📐 **Scansion:** {sc.get('line_count', 0)} lines | Avg Syllables: {sc.get('avg_syllables', 0)} | Iambic Regularity: {sc.get('pentameter_regularity', 0.0):.0%}")

# Chat Input Box
if user_prompt := st.chat_input("Speak to the persona..."):
    # Render user query
    with st.chat_message("user"):
        st.markdown(user_prompt)
    st.session_state[session_key].append({"role": "user", "content": user_prompt})

    # Instantiate Persona Engine
    persona = ShakespearePersona(
        play_id=selected_play_id,
        character_id=selected_char_id,
        act=selected_act,
        scene=selected_scene,
        backend=backend,
        model=model_name
    )

    with st.chat_message("assistant"):
        with st.spinner(f"{selected_char_id.title()} deliberates..."):
            result = persona.generate_response(
                user_message=user_prompt,
                user_role=user_role,
                force_meter=force_meter
            )
            reply = result["reply"]
            scansion = result["scansion"]

            st.markdown(reply)
            if force_meter == "verse" and scansion:
                st.caption(f"📐 **Scansion:** {scansion.get('line_count', 0)} lines | Avg Syllables: {scansion.get('avg_syllables', 0)} | Iambic Regularity: {scansion.get('pentameter_regularity', 0.0):.0%}")

    st.session_state[session_key].append({
        "role": "assistant",
        "content": reply,
        "scansion": scansion
    })