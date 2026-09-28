import streamlit as st
from google import genai
from google.genai import types

# Page Config for mobile-friendly layout
st.set_page_config(
    page_title="Daily Study Chatbot",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "streak" not in st.session_state:
    st.session_state.streak = 0

if "streak_marked_today" not in st.session_state:
    st.session_state.streak_marked_today = False

try:
    # Safely retrieve the Gemini API key from Streamlit secrets
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("⚠️ GEMINI_API_KEY not found in Streamlit Secrets! Please add it in your Cloud App settings.")
    client = None

# Model selection
MODEL_ID = "gemini-2.5-flash"

with st.sidebar:
    st.image("https://placehold.co/400x150/4f46e5/ffffff?text=Daily+Study+Coach", use_container_width=True)
    st.title("⚙️ Study Settings")
    
    # Student Class Selector (1 to 12)
    student_class = st.selectbox("Select Your Class", [str(i) for i in range(1, 13)], index=8) # Default Class 9
    
    # Subject Input
    subject = st.text_input("Current Subject / Topic", value="Mathematics")
    
    # Study Time Available
    study_time = st.selectbox("Study Time Available", ["30 min", "1 hr", "2 hr"], index=1)
    
    st.divider()
    
    # Streak & Daily Completion
    st.subheader("🔥 Study Streak")
    st.metric(label="Current Streak", value=f"{st.session_state.streak} Days")
    
    if not st.session_state.streak_marked_today:
        if st.button("✅ Mark Today's Study Done", use_container_width=True):
            st.session_state.streak += 1
            st.session_state.streak_marked_today = True
            st.success("Great job! Streak increased!")
            st.rerun()
    else:
        st.info("🎉 Streak already logged for today!")

    st.divider()
    
    # Quick Action Buttons
    st.subheader("⚡ Quick Actions")
    plan_button = st.button("📅 Make Today's Study Plan", use_container_width=True)
    quiz_button = st.button("📝 Quick Quiz (3 Questions)", use_container_width=True)
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

system_instruction = (
    f"You are a friendly, encouraging study coach helping a student in Class {student_class} "
    f"studying {subject}. Explain concepts simply with relatable examples, keep your answers short and punchy, "
    "and always end your response with one simple check-understanding question to test their knowledge."
)

def generate_gemini_response(prompt_history, custom_system_prompt):
    """Streams the response from Gemini using the google-genai SDK."""
    if not client:
        yield "API Key is missing. Please configure GEMINI_API_KEY in Streamlit Secrets."
        return

    # Format history for the Gemini API call
    contents = []
    for msg in prompt_history:
        contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )

    config = types.GenerateContentConfig(
        system_instruction=custom_system_prompt,
        temperature=0.7,
    )

    try:
        response_stream = client.models.generate_content_stream(
            model=MODEL_ID,
            contents=contents,
            config=config
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as err:
        yield f"⚠️ An error occurred: {err}"

if plan_button:
    plan_prompt = f"Create a short, structured {study_time} study timetable for today focusing on {subject} for a Class {student_class} student, including short breaks."
    st.session_state.messages.append({"role": "user", "content": plan_prompt})
    st.rerun()

if quiz_button:
    quiz_prompt = f"Give me a quick 3-question multiple choice or short answer quiz on {subject} suitable for a Class {student_class} student. Ask one question at a time or present all three clearly."
    st.session_state.messages.append({"role": "user", "content": quiz_prompt})
    st.rerun()

st.title("📚 Daily Study Chatbot")
st.caption(f"Your personal AI coach for Class {student_class} — Focused on **{subject}** ({study_time} session)")

# Display prior chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input(f"Ask anything about {subject}..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate and stream assistant reply
    with st.chat_message("assistant"):
        response_stream_container = st.empty()
        full_response = ""
        
        # Stream chunks into UI
        for chunk in generate_gemini_response(st.session_state.messages, system_instruction):
            full_response += chunk
            response_stream_container.markdown(full_response + "▌")
            
        response_stream_container.markdown(full_response)
        
    # Append assistant response to session state history
    st.session_state.messages.append({"role": "assistant", "content": full_response})