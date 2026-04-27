# Streamlit Visual Style Guide

## General Visual Direction

The app must use a premium Apple-inspired visual language.

The interface should look like a polished SaaS product, not a default Streamlit app.

Use:

- Large typography.
- Generous spacing.
- Rounded cards.
- Subtle shadows.
- Soft gradients.
- Neutral backgrounds.
- One blue accent color.
- Clear call-to-action hierarchy.
- Minimal visual noise.
- High contrast for important text.
- Calm visual rhythm.

Avoid:

- Too many colors.
- Heavy borders.
- Strong black shadows.
- Dense layouts.
- Raw widget stacking.
- Default dashboard appearance.
- Overuse of icons.
- Overuse of emojis.

---

## Page Setup

Every main page should use wide layout.

Recommended:

```python
st.set_page_config(
    page_title="Home Protection Wizard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)