
import streamlit as st
from agent_qa_automated import process_question

st.set_page_config(page_title="Chatbot IA", page_icon="💬", layout="centered")

# Estilos CSS para mejorar la experiencia visual
st.markdown("""
    <style>
    body {
        background-color: #f5f7fa;
    }
    .chat-container {
        max-height: 500px;
        overflow-y: auto;
        padding: 8px;
        background: #e3eafc;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .user-box {
        background: linear-gradient(90deg, #e3f2fd 60%, #bbdefb 100%);
        color: #1976d2;
        border-radius: 10px;
        padding: 10px 16px;
        margin: 8px 0 8px auto;
        max-width: 70%;
        text-align: right;
        box-shadow: 0 1px 4px rgba(25,118,210,0.08);
    }
    .assistant-box {
        background: linear-gradient(90deg, #fffde7 60%, #ffe082 100%);
        color: #6d4c41;
        border-radius: 10px;
        padding: 10px 16px;
        margin: 8px auto 8px 0;
        max-width: 70%;
        text-align: left;
        box-shadow: 0 1px 4px rgba(255,193,7,0.08);
    }
    .chat-icon {
        font-size: 1.2em;
        margin-right: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💬 Chatbot SOL")
st.markdown("<hr>", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "stop_requested" not in st.session_state:
    st.session_state["stop_requested"] = False

with st.container():
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"""
                <div class='user-box'>
                    <span class='chat-icon'>🧑</span><b>Tú:</b> {msg['content']}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='assistant-box'>
                    <span class='chat-icon'>🤖</span><b>SOL:</b> {msg['content']}
                </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
user_input = st.text_input("Escribe tu pregunta:", "", key="chat_input")
col1, col2 = st.columns([3,1])
with col1:
    enviar = st.button("Enviar", use_container_width=True)
with col2:
    detener = st.button("Detener ejecución", use_container_width=True)

if detener:
    st.session_state["stop_requested"] = True

if enviar:
    st.session_state["stop_requested"] = False
    if user_input.strip():
        with st.spinner("Generando respuesta, por favor espera..."):
            response = process_question(user_input)
        if not st.session_state["stop_requested"]:
            st.session_state["chat_history"].append({"role": "user", "content": user_input})
            st.session_state["chat_history"].append({"role": "assistant", "content": response})
    st.rerun()
