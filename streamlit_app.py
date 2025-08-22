import streamlit as st
from openai import OpenAI
import requests

# Título y descripción en español, adaptado para Contact Center Grupo Piñero
st.title("💬 Chatbot Contact Center Grupo Piñero")
st.write(
    "Bienvenido al asistente conversacional para el Contact Center de Grupo Piñero. "
)

# Campo para la API Key, desaparece tras rellenarse
if "openai_api_key" not in st.session_state:
    openai_api_key = st.text_input("Clave API de OpenAI", type="password")
    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        st.rerun()
    else:
        st.info("Por favor, añade tu clave API de OpenAI para continuar.", icon="🗝️")
        st.stop()
else:
    openai_api_key = st.session_state.openai_api_key

# Estilos personalizados para los botones primarios (azul oscuro)
st.markdown("""
    <style>
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

# Selector de pestañas en una sola línea
tab_names = ["CHAT", "BORRADORES EMAIL"]
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

# Inicializar mensajes
if "messages" not in st.session_state:
    st.session_state.messages = []

if tab == "CHAT":
    # Cliente OpenAI
    client = OpenAI(api_key=openai_api_key)

    # Mostrar mensajes previos
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de chat
    if prompt := st.chat_input("¿En qué puedo ayudarte?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Mensaje de carga mientras se genera la respuesta
        with st.chat_message("assistant"):
            with st.spinner("Generando respuesta..."):
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

elif tab == "BORRADORES EMAIL":
    # Mostrar mensajes previos
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada de borrador
    if prompt := st.chat_input("Escribe el contenido para el borrador de email"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Mensaje de carga mientras se genera el borrador
        with st.chat_message("assistant"):
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
                    # Extraer el campo 'response' de 'results'
                    email_text = (
                        data["results"][0]["response"]
                        if "results" in data and data["results"]
                        else "Sin respuesta"
                    )
                except Exception as e:
                    email_text = f"Error al obtener el borrador: {e}"

                st.markdown(email_text)
        st.session_state.messages.append({"role": "assistant", "content": email_text})
