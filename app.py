import streamlit as st
import os
from engine import get_chat_engine # Note the name change

st.set_page_config(page_title="Indian Tax AI", layout="wide")
st.title("🇮🇳 Indian Tax Law Advisor")

# 1. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your Tax Expert. Ask me about HRA, 80C, or Home Loans."}
    ]

# 2. Load Engine
if "engine" not in st.session_state:
    with st.spinner("Initializing Memory..."):
        st.session_state.engine = get_chat_engine()

# 3. Display Chat History (The WhatsApp style view)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle User Input
if prompt := st.chat_input("Ask a follow-up question..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    if st.session_state.engine:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # .chat() handles the history automatically
                response = st.session_state.engine.chat(prompt)
                st.markdown(response.response)
                
                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": response.response})
                
                # Optional: Show Sources in an expander
                with st.expander("View Sources"):
                    for node in response.source_nodes:
                        st.markdown(f"**Source:** {node.metadata.get('file_name', 'Unknown')}")
                        st.caption(node.get_content()[:200] + "...")