import streamlit as st

st.header("Article, content and generator")

if "groq_key" not in st.session_state:
    st.session_state.groq_key = []

if "tavily_key" not in st.session_state:
    st.session_state.tavily_key = []

groq_api_key = st.text_input("Groq API Key")
tavily_api_key = st.text_input("Tavily API Key")

if st.button("Save API Keys"):
    st.session_state.groq_key = groq_api_key
    st.session_state.tavily_key = tavily_api_key
    st.session_state
    st.success("API keys saved successfully")

    