from uuid import uuid4

import streamlit as st
from agents import Runner, SQLiteSession
from agents.exceptions import AgentsException
from openai import OpenAIError

from agent import agent
from export_pdf import export_itinerary_pdf


st.set_page_config(page_title="AI Travel Planner", page_icon="✈️")
st.title("AI Travel Planner")
st.caption("Plan a trip in Roman Urdu, Urdu, or English.")

if "trip_id" not in st.session_state:
    st.session_state.trip_id = str(uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.subheader("Trip")
    if st.button("New trip", use_container_width=True):
        st.session_state.trip_id = str(uuid4())
        st.session_state.messages = []
        st.rerun()

    last_reply = next(
        (message["content"] for message in reversed(st.session_state.messages) if message["role"] == "assistant"),
        "",
    )
    if last_reply:
        st.download_button(
            "Download plan as PDF",
            data=export_itinerary_pdf(last_reply),
            file_name="travel-plan.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.button("Download plan as PDF", disabled=True, use_container_width=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Where would you like to travel?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Planning your trip..."):
            session = SQLiteSession(f"travel-planner-{st.session_state.trip_id}", "travel_history.db")
            try:
                result = Runner.run_sync(agent, prompt, session=session)
                reply = result.final_output
            except (AgentsException, OpenAIError) as exc:
                reply = f"Sorry, I couldn't complete that response ({type(exc).__name__}). Please try again."
            st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
