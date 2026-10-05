"""Streamlit chat UI, deployed as a Databricks App."""
import asyncio

import streamlit as st

from agent import run_agent

st.set_page_config(page_title="Support Copilot", page_icon="🛟")
st.title("🛟 Customer Support Copilot")
st.caption("Claude Agent SDK · RAG over product docs · customer data in Unity Catalog")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Try asking")
    for example in [
        "Customer 1042 says their export keeps failing. What's wrong?",
        "Customer 1007 wants a refund on their annual plan. What should I do?",
        "Customer 1015 is getting 429 errors from the API. Why?",
        "Which identity providers support SSO?",
    ]:
        if st.button(example, use_container_width=True):
            st.session_state.pending = example
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("tool_calls"):
            with st.expander(f"🔧 {len(m['tool_calls'])} tool call(s)"):
                st.json(m["tool_calls"])

question = st.chat_input("Ask about a customer or the product...") or st.session_state.pop("pending", None)
if question:
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                out = asyncio.run(run_agent(question, history))
            except Exception as e:
                out = {"answer": f"Sorry, something went wrong: `{e}`", "tool_calls": []}
        st.markdown(out["answer"])
        if out["tool_calls"]:
            with st.expander(f"🔧 {len(out['tool_calls'])} tool call(s)"):
                st.json(out["tool_calls"])
    st.session_state.messages.append({"role": "assistant", "content": out["answer"], "tool_calls": out["tool_calls"]})
