# Component Rules — Streamlit Premium UI

## Purpose

This document defines how UI components must be designed and implemented in this Streamlit project.

The goal is to make the application feel like a premium, Apple-inspired SaaS product, not like a default Streamlit dashboard.

The project uses:

- Python
- Streamlit
- Custom CSS
- `st.session_state`
- Static assets
- Simple MVP architecture

---

## 1. General Component Principles

Every component must be:

- Clear.
- Reusable when useful.
- Visually consistent.
- Desktop-first.
- Responsive-friendly.
- Accessible.
- Simple to maintain.
- Not overengineered.

Components should help the user understand:

1. Where they are.
2. What they need to do.
3. Why it matters.
4. What happens next.

Avoid components that only decorate without improving clarity.

---

## 2. Streamlit-Specific Component Rules

Use Streamlit primitives intentionally:

```python
st.container()
st.columns()
st.markdown(..., unsafe_allow_html=True)
st.button()
st.file_uploader()
st.video()
st.progress()
st.spinner()
st.radio()
st.selectbox()
st.text_input()
st.text_area()