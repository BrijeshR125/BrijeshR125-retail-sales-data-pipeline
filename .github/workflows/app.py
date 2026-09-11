"""
Streamlit UI for the natural-language sales query agent.
Run with: streamlit run app.py
"""
import streamlit as st
from agent import ask

st.set_page_config(page_title="Sales Data Q&A Agent", page_icon="📊")

st.title("📊 Natural-Language Sales Query Agent")
st.caption("Ask questions about the sales database in plain English — powered by Claude.")

question = st.text_input(
    "Ask a question",
    placeholder="e.g. What were the top 3 products by revenue in June 2026?"
)

if st.button("Ask") and question:
    with st.spinner("Generating SQL and fetching results..."):
        sql, df, summary = ask(question)

    st.subheader("Answer")
    st.write(summary)

    with st.expander("See generated SQL"):
        st.code(sql, language="sql")

    if df is not None and not df.empty:
        st.subheader("Raw results")
        st.dataframe(df)

st.divider()
st.markdown(
    "**Example questions to try:**\n"
    "- What were total sales in June 2026?\n"
    "- Which city had the highest revenue?\n"
    "- Show me the top 5 products by quantity sold\n"
    "- What's the average order value by product category?"
)
