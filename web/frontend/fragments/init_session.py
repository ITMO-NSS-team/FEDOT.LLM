import streamlit as st


def init_page():
    st.set_page_config(
        page_title="FedotLLM",
        page_icon="web/frontend/static/images/logo.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.logo(
        image='web/frontend/static/images/fedot-llm-white.png',
        link='https://itmo-nss-team.github.io/'
    )
    st.title("💬 FEDOT.LLM")


def init_session_state():
    if "model" not in st.session_state.keys():
        st.session_state.model = None
    if "dataset" not in st.session_state.keys():
        st.session_state.dataset = None
    # if "fedot_ai" not in st.session_state.keys():
    #     st.session_state.fedot_ai = None
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant",
             "content": "Hello! Pick a model, upload the dataset files, send me the dataset description. "}
        ]
    if 'chat_input_disable' not in st.session_state:
        st.session_state.chat_input_disable = False
    if "fedotai_backend" not in st.session_state.keys():
        st.session_state.fedotai_backend = None
    if "model_name" not in st.session_state.keys():
        st.session_state.model_name = None
    if 'prev_graph' not in st.session_state.keys():
        st.session_state.prev_graph = None


def init_session():
    init_page()
    init_session_state()
