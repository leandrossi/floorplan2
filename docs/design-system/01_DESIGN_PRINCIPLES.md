# Streamlit Design Principles

## Role

Act as a Senior UI/UX Designer and Senior Python Streamlit Engineer specialized in:

- Premium desktop-first web applications.
- Guided wizard flows.
- Onboarding experiences.
- Apple-inspired product interfaces.
- High-conversion step-by-step user journeys.
- Clear interfaces for non-technical users.

This project is built with:

- Python.
- Streamlit.
- Custom CSS.
- Streamlit session state.
- Static assets.
- Simple MVP architecture.

The goal is to make Streamlit feel like a premium product experience, not like a default data dashboard or a quick prototype.

---

## Product Context

This application is a guided wizard that helps users design the right protection system for a property.

The end user may not understand:

- Alarm systems.
- Sensors.
- Floorplans.
- Security design.
- Technical security language.
- Installation logic.

Therefore, the interface must:

- Explain each step clearly.
- Reduce cognitive load.
- Avoid technical jargon.
- Create confidence.
- Guide the user one decision at a time.
- Make the experience feel simple, controlled, and professional.

---

## Core UX Principles

### 1. Clarity over complexity

Every screen must be easy to understand in less than 5 seconds.

The user should immediately understand:

- Where they are.
- What they need to do.
- Why it matters.
- What happens next.

Avoid unnecessary explanations, dense text, or complex UI patterns.

---

### 2. One main task per screen

Each wizard screen should focus on one primary task.

Examples:

- Watch introduction or start.
- Choose the objective.
- Upload the floorplan.
- Review detected areas.
- Confirm vulnerable zones.
- Review recommended devices.
- Confirm final solution.

Do not combine too many decisions in the same screen.

---

### 3. One primary action per screen

Every screen must have one clear primary CTA.

Good examples:

- Start guided setup
- Continue
- Upload floorplan
- Confirm entrance
- Generate recommendation
- Review protection plan
- Finish setup

Avoid vague labels like:

- OK
- Submit
- Next
- Go
- Done

Use action-specific button labels.

---

### 4. Desktop-first by default

This application will be used mainly on desktop or laptop.

The design must prioritize:

- Wide layouts.
- Two-column structures when useful.
- Large visual areas.
- Clear cards.
- Visible CTAs.
- Minimal vertical scroll.
- Strong use of horizontal space.

The application must still work on mobile, but desktop is the primary target.

---

### 5. Premium but simple

The app should feel polished and high quality, but not overdesigned.

Use:

- Clean layouts.
- Large typography.
- White space.
- Rounded cards.
- Soft shadows.
- Subtle gradients.
- One accent color.
- Controlled animations if possible.

Avoid:

- Excessive colors.
- Heavy shadows.
- Dense borders.
- Too many icons.
- Dashboard clutter.
- Raw Streamlit default appearance.

---

### 6. Progressive disclosure

Only show the user what they need at the current moment.

Do not expose advanced options too early.

Use helper text, expandable explanations, or contextual guidance only when needed.

The user should not feel overwhelmed.

---

### 7. Trust through guidance

The user must feel that the system is intelligent and safe.

Use trust indicators such as:

- Guided process
- No technical knowledge required
- Takes 5–7 minutes
- You can go back anytime
- Your information is safe
- Review before confirming

Trust indicators should be subtle and not exaggerated.

---

### 8. Human language

Use simple, human, non-technical language.

Bad:

“Upload source artifact for segmentation pipeline.”

Good:

“Upload your floorplan so we can detect the important areas.”

Bad:

“Validation failed.”

Good:

“Please upload a PDF, JPG, or PNG file to continue.”

---

### 9. Avoid raw Streamlit look

Streamlit is the technology, but the user should not feel they are using a raw Streamlit prototype.

Avoid:

- Default full-width widgets without layout.
- Random vertical stacking.
- Dense forms.
- Unstyled sections.
- Too many visible Streamlit controls.
- Dashboard-like screens unless the screen is truly analytical.

Use CSS, containers, columns, and cards to create a premium product layer.

---

### 10. Keep MVP implementation simple

Do not overengineer.

Use:

- `st.session_state` for navigation and persistence.
- `st.columns()` for layout.
- `st.container()` for grouping.
- `st.markdown(..., unsafe_allow_html=True)` for custom visual cards.
- Native Streamlit widgets for inputs.
- A central CSS file.

Avoid:

- Complex routing libraries.
- Heavy frontend frameworks.
- Unnecessary custom components.
- Complex state managers.
- Excessive abstractions.

---

## Product Feeling

The interface should feel:

- Premium.
- Calm.
- Intelligent.
- Guided.
- Trustworthy.
- Minimal.
- Elegant.
- Clear.
- Modern.
- Professional.

The interface should not feel:

- Like a data science notebook.
- Like a generic dashboard.
- Like a basic form.
- Like an internal admin panel.
- Like an unfinished MVP.
- Like a technical tool for experts only.

---

## Streamlit Reality

Streamlit has layout limitations.

The design must work with Streamlit’s strengths instead of fighting the framework.

Use:

- `st.set_page_config(layout="wide")`
- `st.columns()`
- `st.container()`
- `st.markdown()` with custom HTML/CSS
- `st.video()`
- `st.file_uploader()`
- `st.button()`
- `st.progress()`
- `st.spinner()`
- `st.session_state`

Do not try to force Streamlit to behave exactly like React.

The goal is to create a clean, premium interface using practical Streamlit patterns.