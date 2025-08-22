import streamlit as st
from agent_qa_automated import process_question
import requests

# Estilos personalizados (importados de app_chatbot.py)
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
    .stButton > button[data-testid="baseButton-primary"] {
        background-color: #003366 !important;
        color: #fff !important;
        border: none !important;
    }
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #002244 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Título y descripción en español, adaptado para Contact Center Grupo Piñero
st.title("💬 Chatbot Contact Center Grupo Piñero")
st.write(
    "Bienvenido al asistente conversacional para el Contact Center de Grupo Piñero. "
)

# Selector de pestañas en una sola línea
tab_names = ["CHAT", "BORRADORES"]
if "tab" not in st.session_state:
    st.session_state.tab = tab_names[0]

cols = st.columns([1, 1])  # Dos columnas iguales para los botones
for i, name in enumerate(tab_names):
    with cols[i]:
        if st.button(
            name,
            key=f"tab_{name}",
            use_container_width=True,
            type="primary" if st.session_state.tab == name else "secondary"
        ):
            st.session_state.tab = name
            st.rerun()

tab = st.session_state.tab

# Inicializar historiales separados
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "email_messages" not in st.session_state:
    st.session_state.email_messages = []

def render_chat_messages(messages, copy_enabled=False):
    with st.container():
        for idx, message in enumerate(messages):
            if message["role"] == "user":
                st.markdown(f"""
                    <div class='user-box'>
                        <span class='chat-icon'>🧑</span><b>Tú:</b><br> {message['content']}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class='assistant-box'>
                        <span class='chat-icon'>🤖</span><b>SOL:</b><br> {message['content']}
                    </div>
                """, unsafe_allow_html=True)
                if copy_enabled:
                    copy_key = f"copy_email_{idx}"
                    if st.button("Copiar borrador", key=copy_key):
                        st.session_state["copied_email_text"] = message["content"]
                        st.toast("¡Borrador copiado al portapapeles!")

if tab == "CHAT":
    render_chat_messages(st.session_state.chat_messages)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
    prompt = st.text_input("¿En qué puedo ayudarte?", "", key="chat_input")
    col1, col2 = st.columns([3,1])
    with col1:
        enviar = st.button("Enviar", use_container_width=True)
    with col2:
        detener = st.button("Detener ejecución", use_container_width=True)

    if "stop_requested" not in st.session_state:
        st.session_state["stop_requested"] = False
    if detener:
        st.session_state["stop_requested"] = True

    if enviar:
        st.session_state["stop_requested"] = False
        if prompt.strip():
            with st.spinner("Generando respuesta, por favor espera..."):
                response = process_question(prompt)
            if not st.session_state["stop_requested"]:
                st.session_state.chat_messages.append({"role": "user", "content": prompt})
                st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

elif tab == "BORRADORES":
    render_chat_messages(st.session_state.email_messages, copy_enabled=True)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
    prompt = st.text_input("Escribe el contenido para el borrador de email", "", key="email_input")
    col1, col2 = st.columns([3,1])
    with col1:
        enviar = st.button("Enviar borrador", use_container_width=True, key="enviar_email")
    with col2:
        detener = st.button("Detener ejecución borrador", use_container_width=True, key="detener_email")

    if "stop_requested_email" not in st.session_state:
        st.session_state["stop_requested_email"] = False
    if detener:
        st.session_state["stop_requested_email"] = True

    if enviar:
        st.session_state["stop_requested_email"] = False
        if prompt.strip():
            st.session_state.email_messages.append({"role": "user", "content": prompt})
            with st.spinner("Generando borrador de email..."):
                url = "https://az-email-response-assistant-dev.azurewebsites.net/drafter/email_response_assistant"
                headers = {
                    "function_key": "Ay6-egV-moko5w3knTm35bkVgEGQqirDm9aFnGpzck9YAzFucR7Q7w==",
                    "Content-Type": "application/json"
                }
                payload = {
                    "emails": [
                        {
                            "id": "1",
                            "text": prompt
                        }
                    ]
                }
                try:
                    response = requests.post(url, json=payload, headers=headers)
                    data = response.json()
                    email_text = (
                        data["results"][0]["response"]
                        if "results" in data and data["results"]
                        else "Sin respuesta"
                    )
                except Exception as e:
                    email_text = f"Error al obtener el borrador: {e}"

            if not st.session_state["stop_requested_email"]:
                st.session_state.email_messages.append({"role": "assistant", "content": email_text})
        st.rerun()
