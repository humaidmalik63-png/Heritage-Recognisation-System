"""
Heritage Monument Recognition Platform - Streamlit Cloud Web & API Application
Project No. 30: Visual Heritage Recognition & Grounded Cultural Discovery Platform (SIH 2025)
Two-Tier Hybrid Architecture with Calibrated Uncertainty Engine & 100-Site Catalogue
"""

import asyncio
import io
import json
import os
import sys
from pathlib import Path
from PIL import Image
import pandas as pd
import streamlit as st

# Ensure repository root and backend directory are in sys.path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Streamlit Page Setup
st.set_page_config(
    page_title="Indian Heritage Recognition Platform | SIH 2025",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for government/curatorial design aesthetic
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
    }
    .badge-verified { background-color: #DCFCE7; color: #15803D; border: 1px solid #86EFAC; }
    .badge-uncertain { background-color: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }
    .badge-rejected { background-color: #FEE2E2; color: #B91C1C; border: 1px solid #FCA5A5; }
    .badge-unknown { background-color: #E0E7FF; color: #4338CA; border: 1px solid #A5B4FC; }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 0.75rem;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="🏛️ Initializing Heritage AI Engine, CLIP ViT-B/32 & FAISS Vector Index...")
def get_backend_engine(api_key: str = None):
    """
    Initializes the backend resources once in memory using st.cache_resource.
    Works seamlessly on Streamlit Community Cloud.
    """
    from backend.main import initialize_backend_resources, state
    effective_key = api_key
    if not effective_key:
        try:
            if "GEMINI_API_KEY" in st.secrets:
                effective_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
    if not effective_key:
        effective_key = os.environ.get("GEMINI_API_KEY")

    initialize_backend_resources(gemini_api_key=effective_key)
    return state


# Sidebar Configuration & Telemetry
st.sidebar.image("https://img.icons8.com/color/96/temple.png", width=64)
st.sidebar.title("Heritage AI Engine")
st.sidebar.caption("SIH 2025 // SIH25052 – Project No. 30")

# API Key Resolution
secrets_key_detected = False
try:
    if "GEMINI_API_KEY" in st.secrets and len(st.secrets["GEMINI_API_KEY"].strip()) > 5:
        secrets_key_detected = True
except Exception:
    pass

env_key_detected = bool(os.environ.get("GEMINI_API_KEY"))

with st.sidebar.expander("🔑 Gemini Tier-2 Key Settings", expanded=not (secrets_key_detected or env_key_detected)):
    if secrets_key_detected:
        st.success("✅ Configured via Streamlit Secrets")
        user_key = st.secrets["GEMINI_API_KEY"]
    elif env_key_detected:
        st.success("✅ Configured via Environment")
        user_key = os.environ.get("GEMINI_API_KEY")
    else:
        st.warning("No API key found in secrets.")
        user_key = st.text_input("Enter Gemini API Key (optional):", type="password")

# Load Backend Engine
engine_state = get_backend_engine(api_key=user_key if user_key else None)

st.sidebar.divider()
st.sidebar.subheader("System Telemetry")
faiss_count = engine_state["faiss_index"].ntotal if engine_state.get("faiss_index") else 0
st.sidebar.metric("FAISS Anchors", f"{faiss_count} vectors")
st.sidebar.metric("Target Hardware", engine_state.get("device", "cpu").upper())
st.sidebar.metric("Registered Catalogue", f"{len(engine_state.get('catalogue_100', {}))} sites")
st.sidebar.metric(
    "Tier 2 VLM",
    "Active (Gemini 3.1)" if engine_state.get("gemini_configured") else "Offline Fallback"
)

# Header Section
st.markdown('<div class="main-header">🏛️ Visual Heritage Recognition & Grounded Cultural Discovery</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Two-Tier Hybrid Architecture with Calibrated Uncertainty Engine | Ministry of Culture & ASI Knowledge Grounding</div>', unsafe_allow_html=True)

# Main Interface Tabs
tab_verify, tab_catalogue, tab_curator, tab_api = st.tabs([
    "🔍 Live Verification",
    "🗺️ 100-Site Heritage Catalogue",
    "⚖️ Curator Exceptions",
    "🔌 API Docs & cURL"
])


# ==============================================================================
# TAB 1: LIVE MONUMENT VERIFICATION
# ==============================================================================
with tab_verify:
    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("1. Image Ingestion")
        input_mode = st.radio("Input Source:", ["Upload File", "Camera Capture", "Pre-loaded Sample"], horizontal=True)

        image_to_process = None
        image_name = "upload.jpg"

        if input_mode == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload architectural monument photo:",
                type=["jpg", "jpeg", "png", "webp"],
                help="Accepts high-resolution or mobile field photographs."
            )
            if uploaded_file:
                image_to_process = uploaded_file.getvalue()
                image_name = uploaded_file.name

        elif input_mode == "Camera Capture":
            camera_file = st.camera_input("Capture live heritage photo:")
            if camera_file:
                image_to_process = camera_file.getvalue()
                image_name = "camera_capture.jpg"

        else:
            # Sample Image Picker
            sample_options = {
                "Taj Mahal (Marble Mausoleum)": "backend/dataset/taj_mahal/img_1.jpg",
                "Qutub Minar (Victory Tower)": "backend/dataset/qutub_minar/img_1.jpg",
                "Ajanta Caves (Rock-cut Buddhist Cave)": "backend/dataset/ajanta_caves/img_1.jpg",
                "Konark Sun Temple (Orissan Chariot)": "backend/dataset/konark_sun_temple/img_1.jpg",
                "Non-Monument Test": None
            }
            sample_choice = st.selectbox("Choose sample photo from dataset:", list(sample_options.keys()))
            sample_path_rel = sample_options[sample_choice]
            if sample_path_rel:
                sample_path = ROOT_DIR / sample_path_rel
                if sample_path.exists():
                    with open(sample_path, "rb") as f:
                        image_to_process = f.read()
                    image_name = sample_path.name

        if image_to_process:
            pil_preview = Image.open(io.BytesIO(image_to_process))
            st.image(pil_preview, caption=f"Specimen Preview: {image_name} ({pil_preview.width}x{pil_preview.height})", use_container_width=True)
            verify_btn = st.button("🚀 Analyze & Verify Monument", type="primary", use_container_width=True)
        else:
            verify_btn = False
            st.info("👆 Upload or select an architectural specimen image to begin recognition.")

    with col_result:
        st.subheader("2. Recognition & Uncertainty Adjudication")

        if verify_btn and image_to_process:
            with st.spinner("Processing through CLIP Gatekeeper, FAISS Index, and Calibration Engine..."):
                from backend.main import process_verification_pipeline
                # Run the asynchronous verification pipeline
                result = asyncio.run(process_verification_pipeline(image_to_process, filename=image_name))

            # Display Status Badge
            status_map = {
                "VERIFIED_MATCH": ("badge-verified", "✅ VERIFIED MONUMENT MATCH"),
                "UNCERTAIN_MATCH": ("badge-uncertain", "⚠️ UNCERTAIN MATCH (CLOSE COMPETITION)"),
                "UNKNOWN_HERITAGE_SPECIMEN": ("badge-unknown", "🌐 UNKNOWN / OUT-OF-CATALOG HERITAGE"),
                "NON_MONUMENT_REJECTED": ("badge-rejected", "❌ NON-MONUMENT SPECIMEN REJECTED"),
                "REVIEW_REQUIRED": ("badge-uncertain", "📋 HUMAN CURATOR REVIEW REQUIRED"),
            }
            badge_class, badge_label = status_map.get(result.verification_status, ("badge-uncertain", result.verification_status))

            st.markdown(f'<div class="status-badge {badge_class}">{badge_label}</div>', unsafe_allow_html=True)
            st.markdown(f"### {result.monument_name or 'Unrecognized Specimen'}")

            # Confidence Metric
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Confidence Score", f"{result.confidence_score:.1f}%")
            with col_m2:
                st.metric("Verification Tier", result.verification_tier.split("//")[0].strip())

            # Key Architectural Details
            if result.is_monument:
                with st.container():
                    st.markdown("#### Architectural & Historical Identity")
                    st.write(f"📍 **Location:** {result.location or 'Pending verification'}")
                    if result.built_by_or_era:
                        st.write(f"👑 **Dynasty / Era:** {result.built_by_or_era}")
                    if result.architectural_style:
                        st.write(f"🏛️ **Architectural Style:** {result.architectural_style}")
                    if result.historical_summary:
                        st.write(f"📜 **Historical Monograph:** {result.historical_summary}")

                    if result.structural_features_detected:
                        st.markdown("**Detected Architectural Features:**")
                        features_html = " ".join([f"`{f}`" for f in result.structural_features_detected])
                        st.markdown(features_html)

                    # Geodetic Map View
                    if result.coordinates and "lat" in result.coordinates and "lng" in result.coordinates:
                        st.markdown("#### Geographic Coordinates (ASI Registered)")
                        map_df = pd.DataFrame([{"lat": result.coordinates["lat"], "lon": result.coordinates["lng"]}])
                        st.map(map_df, zoom=12)

                    # Grounded Citations
                    if result.grounded_citations:
                        with st.expander("🏛️ Legal & Preservation Citations (ASI / UNESCO)"):
                            c = result.grounded_citations
                            if c.primary_source: st.write(f"• **Primary Source:** {c.primary_source}")
                            if c.gazetteer_reference: st.write(f"• **Gazetteer Reference:** {c.gazetteer_reference}")
                            if c.unesco_whc_ref: st.write(f"• **UNESCO Reference:** {c.unesco_whc_ref}")
                            if c.legal_framework: st.write(f"• **Legal Protection:** {c.legal_framework}")
            else:
                st.error(f"Rejection Reason: {result.rejection_message or 'Image did not satisfy architectural thresholds.'}")

            # Technical Telemetry Expander
            with st.expander("⚙️ Pipeline Technical Telemetry & Evidence"):
                telem = result.pipeline_telemetry
                st.write(f"**Gatekeeper Score:** {telem.architectural_gatekeeper_score:.4f} (Threshold: 0.15)")
                st.write(f"**Decision Reason:** {telem.decision_reason}")
                st.write(f"**Margin Threshold Applied:** {telem.margin_threshold:.4f}")

                if telem.top_3_candidates:
                    st.write("**Top Unique-Monument Candidates:**")
                    cand_df = pd.DataFrame([
                        {"Monument": c.monument_name, "Key": c.monument_key, "Similarity": f"{c.cosine_similarity:.4f}"}
                        for c in telem.top_3_candidates
                    ])
                    st.dataframe(cand_df, use_container_width=True)

        elif not verify_btn:
            st.info("Analysis results and grounded architectural breakdown will render here after clicking 'Analyze & Verify Monument'.")


# ==============================================================================
# TAB 2: 100-SITE HERITAGE CATALOGUE EXPLORER
# ==============================================================================
with tab_catalogue:
    st.subheader("100-Site Extended Heritage Catalogue")
    st.caption("50 Flagship Indian Monuments + 50 International Heritage Landmarks")

    catalogue_data = engine_state.get("catalogue_100", {})
    if catalogue_data:
        search_query = st.text_input("Search monument name, dynasty, or location:", "")
        cat_items = list(catalogue_data.values()) if isinstance(catalogue_data, dict) else catalogue_data

        filtered_items = [
            m for m in cat_items
            if search_query.lower() in str(m.get("monument_name", "")).lower()
            or search_query.lower() in str(m.get("location", "")).lower()
            or search_query.lower() in str(m.get("historical_period", "")).lower()
        ]

        st.write(f"Displaying **{len(filtered_items)}** of **{len(cat_items)}** monuments.")

        # Show catalogue cards in a 2-column grid
        grid_col1, grid_col2 = st.columns(2)
        for idx, item in enumerate(filtered_items[:20]):
            target_col = grid_col1 if idx % 2 == 0 else grid_col2
            with target_col:
                with st.container():
                    st.markdown(f"### {item.get('monument_name')}")
                    st.caption(f"📍 {item.get('location')} | 🏛️ {item.get('architectural_style', 'Heritage Architecture')}")
                    st.write(f"**Period:** {item.get('historical_period', 'Historical')}")
                    st.write(f"**Description:** {item.get('verified_description', '')[:160]}...")
                    if item.get("coordinates"):
                        coords = item["coordinates"]
                        st.caption(f"Coordinates: `{coords.get('lat')}, {coords.get('lng')}`")
                    st.divider()
    else:
        st.warning("Heritage catalogue not loaded.")


# ==============================================================================
# TAB 3: CURATOR REVIEW EXCEPTIONS
# ==============================================================================
with tab_curator:
    st.subheader("Curator Audit Trail & Exceptions Register")
    st.caption("Persistent log of ambiguous scans, out-of-catalog specimens, and edge cases flagged for human review.")

    from backend.main import load_exceptions_log
    exceptions = load_exceptions_log()
    if exceptions:
        st.write(f"Total flagged items awaiting review: **{len(exceptions)}**")
        exc_rows = []
        for e in exceptions:
            exc_rows.append({
                "ID": e.get("id"),
                "Timestamp": e.get("timestamp", "")[:19],
                "Candidate": e.get("monument_name_candidate") or e.get("monument_key_candidate"),
                "Top Sim": f"{e.get('top_similarity_score', 0.0):.3f}",
                "Gatekeeper": f"{e.get('gatekeeper_score', 0.0):.3f}",
                "Status": e.get("status", "PENDING_REVIEW"),
                "Reason": e.get("reason", "")[:60]
            })
        st.dataframe(pd.DataFrame(exc_rows), use_container_width=True)
    else:
        st.success("🎉 No pending curator exceptions. All processed scans resolved with high confidence.")


# ==============================================================================
# TAB 4: API DOCUMENTATION & CURL SNIPPETS
# ==============================================================================
with tab_api:
    st.subheader("REST API Integration")
    st.write("Developers can query the live recognition backend programmatically:")

    st.markdown("#### `POST /api/verify-monument`")
    st.code(
        """curl -X POST "http://localhost:8000/api/verify-monument" \\
  -H "accept: application/json" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@/path/to/monument_photo.jpg"
""",
        language="bash"
    )

    st.markdown("#### Python Client Example")
    st.code(
        """import requests

url = "http://localhost:8000/api/verify-monument"
with open("taj_mahal.jpg", "rb") as img_file:
    response = requests.post(url, files={"file": img_file})

data = response.json()
print("Monument:", data["monument_name"])
print("Status:", data["verification_status"])
print("Confidence:", data["confidence_score"])
""",
        language="python"
    )

    st.markdown("#### Sample Verification JSON Payload")
    sample_json = {
        "is_monument": True,
        "verification_status": "VERIFIED_MATCH",
        "verification_tier": "LOCAL CLIP + FAISS EMBEDDING ANCHORS",
        "confidence_score": 98.7,
        "monument_name": "Taj Mahal",
        "location": "Agra, Uttar Pradesh, India",
        "architectural_style": "Mughal Architecture",
        "built_by_or_era": "Mughal Emperor Shah Jahan (1631–1648 CE)"
    }
    st.json(sample_json)

