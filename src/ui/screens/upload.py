from __future__ import annotations

from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, UnidentifiedImageError

from domain.enums import WizardScreen

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
FEEDBACK_KEY = "step1_upload_feedback"
PREVIEW_KEY = "floorplan_example_preview"
ASSET_DIR = Path(__file__).resolve().parents[3] / "assets" / "icons"
EXAMPLE_FLOORPLANS = [
    {
        "path": ASSET_DIR / "floorplan suitable eng.png",
        "label": "Good example",
        "tone": "good",
        "title": "Suitable floorplan",
        "description": "Complete, clear, and easy to read.",
    },
    {
        "path": ASSET_DIR / "floorplan not suitable I.png",
        "label": "Avoid",
        "tone": "bad",
        "title": "Not suitable",
        "description": "Too incomplete or hard to interpret.",
    },
    {
        "path": ASSET_DIR / "floorplan not suitable II.png",
        "label": "Avoid",
        "tone": "bad",
        "title": "Not suitable",
        "description": "Low clarity makes detection unreliable.",
    },
]


def _selected_example_index() -> int | None:
    raw_value = st.query_params.get("floorplan_example")
    if raw_value is None:
        return None
    try:
        index = int(raw_value)
    except (TypeError, ValueError):
        return None
    if 0 <= index < len(EXAMPLE_FLOORPLANS):
        return index
    return None


def _clear_example_preview_state() -> None:
    st.session_state.pop(PREVIEW_KEY, None)
    if "floorplan_example" in st.query_params:
        try:
            del st.query_params["floorplan_example"]
        except Exception:  # noqa: BLE001
            st.query_params.clear()


def _render_large_example(example: dict) -> None:
    if example["path"].is_file():
        st.image(str(example["path"]), width="stretch")
    else:
        st.warning("Example image missing.")
    if st.button("Close preview", type="primary", use_container_width=True):
        _clear_example_preview_state()
        st.rerun()


def _show_large_example(example: dict) -> None:
    if hasattr(st, "dialog"):
        dialog = st.dialog(" ", width="large")(_render_large_example)
        dialog(example)
    else:
        st.markdown('<div class="wizard-card">', unsafe_allow_html=True)
        _render_large_example(example)
        st.markdown("</div>", unsafe_allow_html=True)


def _render_example_card(example: dict, idx: int) -> None:
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="floorplan-example-copy">
              <span class="floorplan-example-label">{example["label"]}</span>
              <div>
                <p class="floorplan-example-title">{example["title"]}</p>
                <p class="floorplan-example-description">{example["description"]}</p>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if example["path"].is_file():
            st.image(str(example["path"]), width="stretch")
        else:
            st.markdown('<div class="floorplan-example-missing">Example image missing</div>', unsafe_allow_html=True)
        if st.button("Click to enlarge", key=f"open_floorplan_example_{idx}", use_container_width=True):
            _clear_example_preview_state()
            _show_large_example(example)


def _validate_uploaded_plan(uploaded_file) -> tuple[bool, str | None, bytes | None, bool]:
    if uploaded_file is None:
        return False, "Upload a file to continue.", None, False

    filename = (uploaded_file.name or "").strip()
    extension = filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return False, "This format is not supported. Use PDF, JPG, or PNG.", None, False

    raw_bytes = uploaded_file.getvalue()
    if not raw_bytes:
        return False, "We couldn't read this file. Try a clearer version of the floorplan.", None, False

    is_image = extension in {"png", "jpg", "jpeg"}
    if is_image:
        try:
            with Image.open(BytesIO(raw_bytes)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            return False, "We couldn't read this file. Try a clearer version of the floorplan.", None, False

    return True, None, raw_bytes, is_image


def render(controller) -> None:
    state = controller.state()
    feedback = st.session_state.pop(FEEDBACK_KEY, None)
    selected_example_index = _selected_example_index()
    if selected_example_index is not None:
        _show_large_example(EXAMPLE_FLOORPLANS[selected_example_index])

    st.markdown(
        """
        <style>
        .upload-examples-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 24px;
            padding: 1.15rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
        }
        .upload-examples-title {
            margin: 0;
            color: #111827;
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: -0.01em;
            line-height: 1.2;
        }
        .upload-examples-subtitle {
            margin: 0.45rem 0 1rem 0;
            color: #6B7280;
            font-size: 0.94rem;
            line-height: 1.45;
        }
        .floorplan-example-list {
            display: grid;
            gap: 0.85rem;
        }
        .floorplan-example-card {
            border: 1px solid #E5E7EB;
            border-radius: 18px;
            background: #FAFAFC;
            overflow: hidden;
            transition: border-color 0.16s ease, box-shadow 0.16s ease, transform 0.16s ease;
        }
        .floorplan-example-card:hover {
            border-color: rgba(0, 122, 255, 0.35);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
            transform: translateY(-1px);
        }
        .floorplan-example-card--good {
            border-color: rgba(0, 122, 255, 0.28);
            background: #F5FAFF;
        }
        .floorplan-example-card--bad {
            background: #FFFFFF;
        }
        .floorplan-example-copy {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.8rem 0.85rem 0.65rem 0.85rem;
        }
        .floorplan-example-label {
            border-radius: 999px;
            padding: 0.28rem 0.55rem;
            background: #E5F1FF;
            color: #0066CC;
            font-size: 0.72rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .floorplan-example-card--bad .floorplan-example-label {
            background: #F3F4F6;
            color: #6B7280;
        }
        .floorplan-example-title {
            margin: 0;
            color: #111827;
            font-size: 0.92rem;
            font-weight: 700;
            line-height: 1.2;
            text-align: right;
        }
        .floorplan-example-description {
            margin: 0.18rem 0 0 0;
            color: #6B7280;
            font-size: 0.78rem;
            line-height: 1.3;
            text-align: right;
        }
        .floorplan-example-missing {
            padding: 1rem;
            border-top: 1px solid #E5E7EB;
            color: #6B7280;
            font-size: 0.9rem;
            text-align: center;
        }
        @media (max-width: 900px) {
            .floorplan-example-title,
            .floorplan-example-description {
                text-align: left;
            }
            .floorplan-example-copy {
                flex-direction: column;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<main class="wizard-page-shell">', unsafe_allow_html=True)
    st.markdown(
        """
        <header class="wizard-page-header">
          <p class="wizard-step-context">Step 1 · Upload floorplan</p>
          <h1 class="wizard-page-title">Upload your floorplan.</h1>
          <p class="wizard-page-subtitle">
            We’ll read the plan, detect the important areas, and prepare a guided review. No alarm or technical knowledge needed.
          </p>
        </header>
        """,
        unsafe_allow_html=True,
    )
    if feedback == "success":
        st.success("Floorplan uploaded correctly. We’re ready to analyze it.")

    main_col, side_col = st.columns([1.5, 1], gap="large")
    with main_col:
        st.markdown('<section class="wizard-card">', unsafe_allow_html=True)
        st.markdown(
            """
            <p class="wizard-title">Add a clear PDF, JPG, or PNG</p>
            <p class="wizard-subtitle">
              The best results come from a complete, readable plan where walls, doors, and rooms are visible.
            </p>
            """,
            unsafe_allow_html=True,
        )
        if state.upload_path and state.uploaded_file_name:
            st.markdown(
                f"""
                <div class="wizard-inline-note">
                  Current floorplan: <strong>{state.uploaded_file_name}</strong><br />
                  You can continue with this file, or upload a new one to replace it.
                </div>
                """,
                unsafe_allow_html=True,
            )
            if state.review_bundle_path:
                if st.button("Continue with current floorplan", type="primary", use_container_width=True):
                    controller.go_to(WizardScreen.REVIEW)
                    st.rerun()
            elif st.button("Continue analysis", type="primary", use_container_width=True):
                controller.go_to(WizardScreen.PROCESSING)
                st.rerun()

        with st.form("wizard_step1_upload_form", clear_on_submit=False):
            st.markdown('<div class="wizard-upload-box">', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Choose your floorplan file",
                type=["pdf", "png", "jpg", "jpeg"],
                accept_multiple_files=False,
            )
            st.caption("Supported formats: PDF, JPG, PNG. Keep the plan complete and easy to read.")
            st.markdown("</div>", unsafe_allow_html=True)

            is_valid, validation_message, raw_bytes, is_image = _validate_uploaded_plan(uploaded_file)

            if uploaded_file is not None:
                if is_valid:
                    st.success("Looks good. Continue when you’re ready.")
                elif validation_message:
                    st.error(validation_message)

            if uploaded_file is not None and is_valid and raw_bytes is not None:
                if is_image:
                    st.image(raw_bytes, caption=uploaded_file.name, width="stretch")
                else:
                    st.info(f"PDF loaded: {uploaded_file.name}")

            submitted = st.form_submit_button("Analyze floorplan", type="primary", use_container_width=True)
            if submitted:
                _clear_example_preview_state()
                if not is_valid or uploaded_file is None or raw_bytes is None:
                    st.error(validation_message or "Please upload a PDF, JPG, or PNG file to continue.")
                else:
                    st.session_state["uploaded_plan"] = {
                        "name": uploaded_file.name,
                        "bytes": raw_bytes,
                        "mime": uploaded_file.type,
                    }
                    st.session_state["current_step"] = 1
                    st.session_state[FEEDBACK_KEY] = "success"
                    controller.save_upload(uploaded_file.name, raw_bytes)
                    st.rerun()
        st.markdown("</section>", unsafe_allow_html=True)

    with side_col:
        st.markdown(
            """
            <aside class="upload-examples-card">
              <p class="upload-examples-title">Use a clear floorplan</p>
              <p class="upload-examples-subtitle">
                Choose a plan that looks like the good example. Avoid files that are incomplete, blurry, or too hard to read.
              </p>
            """,
            unsafe_allow_html=True,
        )
        for idx, example in enumerate(EXAMPLE_FLOORPLANS):
            _render_example_card(example, idx)
        st.markdown(
            """
            </aside>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</main>", unsafe_allow_html=True)
