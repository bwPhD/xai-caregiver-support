import os
import json
import math
import pickle
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import shap
import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams["font.family"] = "DejaVu Sans"
matplotlib.rcParams["font.size"] = 12


# =============================================================================
# Page config
# =============================================================================
st.set_page_config(
    page_title="CareRisk Clinical Dashboard",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# Claude-like warm light UI + compact minimalist treatment
# =============================================================================
st.markdown(
    """
<style>
:root{
  --bg: #f7f6f3;
  --bg-soft: #fbfaf7;
  --panel: #ffffff;
  --panel-soft: #f8f7f4;
  --line: #e6e1d8;
  --line-strong: #d5cfc4;
  --text: #232323;
  --text-soft: #66645f;
  --muted: #8a867d;
  --accent: #111827;
  --accent-soft: #f0efe9;
  --blue: #4f7cff;
  --blue-soft: #edf3ff;
  --green: #13795b;
  --green-soft: #ebf8f2;
  --red: #c2415c;
  --red-soft: #fdeef1;
  --amber: #b7791f;
  --amber-soft: #fff7e8;
  --shadow: 0 8px 22px rgba(30, 30, 30, 0.045);
  --radius: 18px;
  --radius-sm: 12px;
}

html, body, [data-testid="stAppViewContainer"], .main {
  background: linear-gradient(180deg, #fbfaf8 0%, #f7f6f3 100%) !important;
  color: var(--text) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Helvetica, Arial, sans-serif !important;
  font-size: 18px !important;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
  font-size: 1.02rem !important;
  line-height: 1.55 !important;
}

#MainMenu, footer, header {visibility: hidden;}

.block-container {
  max-width: 1380px;
  padding-top: 0.85rem;
  padding-bottom: 1.6rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #f5f3ee !important;
  border-right: 1px solid var(--line) !important;
}

section[data-testid="stSidebar"] * {
  color: var(--text) !important;
}

section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] p {
  color: var(--text-soft) !important;
  font-size: 0.94rem !important;
}

/* Typography */
h1, h2, h3, h4 {
  letter-spacing: -0.01em;
}

label {
  color: var(--text) !important;
  font-weight: 800 !important;
  font-size: 1.0rem !important;
}

/* Inputs */
[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stSlider"] [role="slider"] {
  color: var(--text) !important;
}

[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  background: #fcfcfb !important;
  -webkit-text-fill-color: var(--text) !important;
  border: 1px solid var(--line-strong) !important;
  border-radius: 12px !important;
  min-height: 44px !important;
  font-size: 1.0rem !important;
}

[data-testid="stNumberInput"] input::placeholder {
  color: #97938a !important;
  opacity: 1 !important;
}

[data-testid="stSelectbox"] div[data-baseweb="select"] * {
  color: var(--text) !important;
  font-size: 1.0rem !important;
}

[data-testid="stNumberInput"] button {
  background: #efeae2 !important;
  color: var(--text) !important;
  border-color: var(--line-strong) !important;
}

[data-testid="stNumberInput"] button:hover {
  background: #e5dfd5 !important;
}

[data-testid="stNumberInput"] svg,
[data-testid="stSelectbox"] svg {
  fill: #666 !important;
}

[data-testid="stNumberInput"] input:focus,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
  border-color: #9aa4b2 !important;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.08) !important;
}

/* Inline code / code pills */
code, pre code {
  background: #6b7280 !important;
  color: #ffffff !important;
  border-radius: 10px !important;
}

code {
  padding: 0.18rem 0.46rem !important;
  font-size: 0.92rem !important;
}

/* Header */
.top-shell {
  display: grid;
  grid-template-columns: 1.35fr auto;
  gap: 1rem;
  align-items: center;
  background: linear-gradient(180deg, #ffffff 0%, #fbfaf7 100%);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 0.9rem 1.05rem;
  box-shadow: var(--shadow);
  margin-bottom: 0.85rem;
}

.eyebrow {
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
  font-weight: 800;
  margin-bottom: 0.18rem;
}

.brand-title {
  font-size: 1.55rem;
  font-weight: 900;
  color: var(--text);
  margin: 0;
  letter-spacing: -0.02em;
}

.brand-subtitle {
  font-size: 0.95rem;
  color: var(--text-soft);
  margin-top: 0.08rem;
}

.top-meta {
  display: flex;
  gap: 0.48rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.34rem;
  padding: 0.38rem 0.62rem;
  border-radius: 999px;
  background: var(--panel-soft);
  border: 1px solid var(--line);
  color: var(--text);
  font-size: 0.80rem;
  font-weight: 760;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #2fb67c;
  box-shadow: 0 0 0 4px rgba(47, 182, 124, 0.12);
}

/* Panels */
.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 20px;
  box-shadow: var(--shadow);
  overflow: hidden;
  margin-bottom: 0.85rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.65rem;
  padding: 0.68rem 0.9rem;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(180deg, #ffffff 0%, #faf8f4 100%);
}

.panel-title {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 900;
  color: var(--text);
  letter-spacing: -0.01em;
  line-height: 1.15;
}

.panel-subtitle {
  margin: 0.08rem 0 0;
  font-size: 0.82rem;
  color: var(--text-soft);
  line-height: 1.25;
}

.panel-body {
  padding: 0.86rem;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 0.32rem;
  padding: 0.25rem 0.52rem;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--panel-soft);
  color: var(--text-soft);
  font-size: 0.74rem;
  font-weight: 850;
}

.form-note {
  font-size: 0.90rem;
  color: var(--text-soft);
  line-height: 1.55;
  background: #fbfaf7;
  border: 1px dashed var(--line-strong);
  border-radius: 14px;
  padding: 0.72rem 0.84rem;
  margin-top: 0.65rem;
}

/* Compact panel for Risk Gauge */
.panel.compact .panel-header {
  padding: 0.55rem 0.82rem !important;
  min-height: auto !important;
}

.panel.compact .panel-title {
  font-size: 0.94rem !important;
  line-height: 1.12 !important;
  margin: 0 !important;
}

.panel.compact .panel-subtitle {
  font-size: 0.76rem !important;
  line-height: 1.18 !important;
  margin-top: 0.04rem !important;
}

.panel.compact .panel-body {
  padding: 0.52rem 0.62rem 0.65rem 0.62rem !important;
}

/* Alert banner */
.alert-banner {
  border-radius: 15px;
  padding: 0.82rem 0.95rem;
  border: 1px solid;
  font-size: 0.94rem;
  line-height: 1.52;
  font-weight: 650;
}

.alert-banner.high {
  background: var(--red-soft);
  border-color: #efc4ce;
  color: #8e3046;
}

.alert-banner.low {
  background: var(--green-soft);
  border-color: #c9eadc;
  color: #0e5d46;
}

.risk-note {
  margin-top: 0.58rem;
  color: var(--text-soft);
  font-size: 0.88rem;
  line-height: 1.45;
}

/* Result layout */
.result-layout {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 0.9rem;
  margin-top: 0;
}

/* Summary table */
.summary-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0 0.36rem;
}

.summary-table td {
  background: #fbfaf7;
  padding: 0.64rem 0.75rem;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  font-size: 0.95rem;
}

.summary-table td:first-child {
  border-left: 1px solid var(--line);
  border-radius: 12px 0 0 12px;
  color: var(--text-soft);
  font-weight: 760;
}

.summary-table td:last-child {
  border-right: 1px solid var(--line);
  border-radius: 0 12px 12px 0;
  color: var(--text);
  font-weight: 860;
  text-align: right;
}

/* Footer */
.footer-note {
  margin-top: 1rem;
  padding-top: 0.85rem;
  text-align: center;
  color: var(--text-soft);
  font-size: 0.84rem;
  border-top: 1px solid var(--line);
}

/* Responsive */
@media (max-width: 980px) {
  .top-shell {
    grid-template-columns: 1fr;
  }
  .top-meta {
    justify-content: flex-start;
  }
  .result-layout {
    grid-template-columns: 1fr;
  }
}

/* =========================================================
   Predict button · Streamlit form_submit_button forced style
   Default: dark button + clearly visible white text.
   Hover: light frosted button + dark text.
   ========================================================= */

div[data-testid="stFormSubmitButton"] button,
div[data-testid="stFormSubmitButton"] button[type="submit"],
[data-testid="stFormSubmitButton"] button {
  background:
    linear-gradient(180deg, rgba(24, 30, 42, 0.98), rgba(12, 18, 28, 0.96)) !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  border: 1px solid rgba(255, 255, 255, 0.24) !important;
  border-radius: 16px !important;
  min-height: 48px !important;
  padding: 0.62rem 1.45rem !important;
  box-shadow:
    0 10px 26px rgba(17, 24, 39, 0.18),
    inset 0 1px 0 rgba(255,255,255,0.22) !important;
  backdrop-filter: blur(14px) saturate(1.25) !important;
  -webkit-backdrop-filter: blur(14px) saturate(1.25) !important;
  transition: all 0.18s ease !important;
}

/* Force every inner text node in form submit button */
div[data-testid="stFormSubmitButton"] button *,
div[data-testid="stFormSubmitButton"] button p,
div[data-testid="stFormSubmitButton"] button span,
div[data-testid="stFormSubmitButton"] button div,
[data-testid="stFormSubmitButton"] button *,
[data-testid="stFormSubmitButton"] button p,
[data-testid="stFormSubmitButton"] button span,
[data-testid="stFormSubmitButton"] button div {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  font-weight: 900 !important;
  opacity: 1 !important;
}

/* Hover: light frosted + dark text */
div[data-testid="stFormSubmitButton"] button:hover,
div[data-testid="stFormSubmitButton"] button[type="submit"]:hover,
[data-testid="stFormSubmitButton"] button:hover {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.96), rgba(236,232,224,0.86)) !important;
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  border-color: rgba(17, 24, 39, 0.28) !important;
  transform: translateY(-1px);
  box-shadow:
    0 14px 30px rgba(17, 24, 39, 0.14),
    inset 0 1px 0 rgba(255,255,255,0.96) !important;
}

div[data-testid="stFormSubmitButton"] button:hover *,
div[data-testid="stFormSubmitButton"] button:hover p,
div[data-testid="stFormSubmitButton"] button:hover span,
div[data-testid="stFormSubmitButton"] button:hover div,
[data-testid="stFormSubmitButton"] button:hover *,
[data-testid="stFormSubmitButton"] button:hover p,
[data-testid="stFormSubmitButton"] button:hover span,
[data-testid="stFormSubmitButton"] button:hover div {
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
  opacity: 1 !important;
}

div[data-testid="stFormSubmitButton"] button:active,
[data-testid="stFormSubmitButton"] button:active {
  transform: translateY(0px);
  box-shadow:
    0 6px 16px rgba(17, 24, 39, 0.10),
    inset 0 1px 0 rgba(255,255,255,0.90) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# Extra button color fallback
# =============================================================================
st.markdown(
    """
<style>
div[data-testid="stFormSubmitButton"] button p {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  opacity: 1 !important;
  font-weight: 900 !important;
}
div[data-testid="stFormSubmitButton"] button:hover p {
  color: #111827 !important;
  -webkit-text-fill-color: #111827 !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# Embedded uWrap.js helper
# =============================================================================
def inject_uwrap_js():
    components.html(
        """
<script>
(function () {
  function applyUWrap(doc) {
    if (!doc) return;
    const selectors = [
      "code",
      ".summary-table td",
      ".form-note",
      "[data-testid='stCaptionContainer'] p",
      "[data-testid='stMarkdownContainer'] p",
      ".stAlert p"
    ];
    selectors.forEach((selector) => {
      doc.querySelectorAll(selector).forEach((el) => {
        el.style.overflowWrap = "anywhere";
        el.style.wordBreak = "break-word";
      });
    });
  }

  function run() {
    try {
      const parentDoc = window.parent.document;
      applyUWrap(parentDoc);
    } catch (e) {}
  }

  run();
  const observer = setInterval(run, 1200);
  setTimeout(() => clearInterval(observer), 15000);
})();
</script>
""",
        height=0,
        scrolling=False,
    )


inject_uwrap_js()


# =============================================================================
# Feature schema
# =============================================================================
CAREGIVER_NUM = {
    "daydurG": {
        "min": 0.0,
        "max": 24.0,
        "default": 12.0,
        "label": "Daily Care Hours",
        "unit": "hrs",
        "step": 1.0,
    },
    "age_G": {
        "min": 18.0,
        "max": 120.0,
        "default": 60.0,
        "label": "Caregiver Age",
        "unit": "yrs",
        "step": 1.0,
    },
}

CAREGIVER_CAT = {
    "healthG": {
        "options": [1, 5],
        "default": 3,
        "label": "Self-Rated Health",
        "map": {
            1: "Very poor",
            2: "Poor",
            3: "Fair",
            4: "Good",
            5: "Excellent",
        },
    },
}

RECIPIENT_NUM = {
    "ageR": {
        "min": 60.0,
        "max": 120.0,
        "default": 60.0,
        "label": "Recipient Age",
        "unit": "yrs",
        "step": 1.0,
    },
}

RECIPIENT_CAT = {
    "healthR": {
        "options": [1, 5],
        "default": 3,
        "label": "Self-Rated Health",
        "map": {
            1: "Very poor",
            2: "Poor",
            3: "Fair",
            4: "Good",
            5: "Excellent",
        },
    },
    "adlR": {
        "options": [0, 3],
        "default": 2,
        "label": "ADL Disability",
        "help": "ADL level based on the Barthel Index: 0 intact (100), 1 mild (65–95), 2 moderate (45–60), 3 severe (≤40).",
        "map": {
            0: "Intact",
            1: "Mild",
            2: "Moderate",
            3: "Severe",
        },
    },
    "is_citycentre": {
        "options": [0, 1],
        "default": 1,
        "label": "City-Centre Residence",
        "map": {
            0: "No",
            1: "Yes",
        },
    },
}

VARIABLE_LABELS_DICT = {
    "adlR": "ADL Disability (Recipient)",
    "ageR": "Age (Recipient)",
    "age_G": "Age (Caregiver)",
    "daydurG": "Daily Care Hours (Caregiver)",
    "healthG": "Self-Rated Health (Caregiver)",
    "healthR": "Self-Rated Health (Recipient)",
    "is_citycentre": "City-Centre Residence (Recipient)",
}

VALUE_MAPPINGS = {
    "adlR": {
        0: "Intact",
        1: "Mild",
        2: "Moderate",
        3: "Severe",
    },
    "healthG": {
        1: "Very poor",
        2: "Poor",
        3: "Fair",
        4: "Good",
        5: "Excellent",
    },
    "healthR": {
        1: "Very poor",
        2: "Poor",
        3: "Fair",
        4: "Good",
        5: "Excellent",
    },
    "is_citycentre": {
        0: "No",
        1: "Yes",
    },
}

UNITS = {
    "daydurG": "hours",
    "age_G": "years",
    "ageR": "years",
}

FINAL_FEATURES = [
    "adlR",
    "ageR",
    "age_G",
    "daydurG",
    "healthG",
    "healthR",
    "is_citycentre",
]


# =============================================================================
# Model paths
# =============================================================================
MODEL_PATH = os.getenv("MODEL_PATH", "models/xgboost.pkl")
PREPROCESSOR_PATH = os.getenv("PREPROCESSOR_PATH", "models/preprocessor.pkl")
THRESHOLD_JSON_PATH = os.getenv("THRESHOLD_JSON", "models/best_thresholds.json")
THRESHOLD_KEY = os.getenv("THRESHOLD_KEY", "XGBoost")


# =============================================================================
# Cached loaders
# =============================================================================
@st.cache_resource(show_spinner=False)
def load_artifacts():
    with open(PREPROCESSOR_PATH, "rb") as f:
        preprocessor = pickle.load(f)

    try:
        model = joblib.load(MODEL_PATH)
    except Exception:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)

    return preprocessor, model


def load_threshold(path, key, default=0.5):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return float(d.get(key, default))
    except Exception:
        return default


# =============================================================================
# Utility functions
# =============================================================================
def ensure_feature_dataframe(feature_dict, ordered_features):
    df = pd.DataFrame([feature_dict])
    missing_cols = [c for c in ordered_features if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required features: {missing_cols}")
    return df[ordered_features].copy()


def predict_proba_single(model, X):
    if hasattr(model, "predict_proba"):
        return float(model.predict_proba(X)[:, 1][0])
    if hasattr(model, "decision_function"):
        z = float(np.asarray(model.decision_function(X)).ravel()[0])
        return 1.0 / (1.0 + np.exp(-z))
    raise RuntimeError("The model does not provide probability output.")


def get_transformed_feature_names(preprocessor, fallback_features):
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        return list(fallback_features)


def get_tree_model_for_shap(model):
    if hasattr(model, "calibrated_classifiers_") and len(model.calibrated_classifiers_) > 0:
        clf = model.calibrated_classifiers_[0]
        if hasattr(clf, "estimator"):
            return clf.estimator
        if hasattr(clf, "base_estimator"):
            return clf.base_estimator
    return model


def build_gauge_svg(prob, thr):
    prob = max(0.0, min(1.0, float(prob)))
    thr = max(0.0, min(1.0, float(thr)))
    pct = prob * 100

    if prob < thr * 0.60:
        color = "#13795b"
        level = "Lower risk"
    elif prob < thr:
        color = "#b7791f"
        level = "Borderline"
    else:
        color = "#c2415c"
        level = "Elevated risk"

    r = 82
    circumference = math.pi * r
    dash = circumference * prob
    gap = circumference - dash

    tick_x = 26 + 168 * thr
    tick_y = 102 - math.sin(math.pi * thr) * 84

    return f"""
<!doctype html>
<html>
<head>
<style>
  html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Helvetica, Arial, sans-serif;
  }}
  .gwrap {{
    width: 100%;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #fff;
    border-radius: 14px;
    box-sizing: border-box;
  }}
</style>
</head>
<body>
  <div class="gwrap">
    <svg width="310" height="170" viewBox="0 0 220 145" role="img" aria-label="Risk gauge">
      <path d="M 26 102 A 84 84 0 0 1 194 102" fill="none"
            stroke="#ece7de" stroke-width="16" stroke-linecap="round"/>
      <path d="M 26 102 A 84 84 0 0 1 194 102" fill="none"
            stroke="{color}" stroke-width="16" stroke-linecap="round"
            stroke-dasharray="{dash:.1f} {gap:.1f}"
            style="filter: drop-shadow(0 6px 10px {color}20);"/>
      <circle cx="{tick_x:.1f}" cy="{tick_y:.1f}" r="5" fill="#111827" stroke="#ffffff" stroke-width="2"/>
      <text x="110" y="74" text-anchor="middle" font-family="Inter, sans-serif"
            font-size="34" font-weight="850" fill="{color}">{pct:.1f}%</text>
      <text x="110" y="97" text-anchor="middle" font-family="Inter, sans-serif"
            font-size="10" font-weight="800" fill="#737067" letter-spacing="1.1">PREDICTED RISK</text>
      <text x="110" y="113" text-anchor="middle" font-family="Inter, sans-serif"
            font-size="11" font-weight="800" fill="{color}">{level}</text>
      <text x="26" y="130" font-size="10" font-weight="700" fill="#99948a" font-family="Inter">0%</text>
      <text x="174" y="130" font-size="10" font-weight="700" fill="#99948a" font-family="Inter">100%</text>
    </svg>
  </div>
</body>
</html>
"""


def render_cat_input(key, cfg):
    lo, hi = cfg["options"]
    values = list(range(int(lo), int(hi) + 1))
    mapping = cfg.get("map", {})
    options = [(v, f"{v} - {mapping[v]}" if v in mapping else str(v)) for v in values]

    default_value = cfg.get("default", values[len(values) // 2])
    default_idx = values.index(default_value) if default_value in values else 0

    selected = st.selectbox(
        cfg["label"],
        options=options,
        index=default_idx,
        format_func=lambda x: x[1],
        key=f"cat_{key}",
        help=cfg.get("help"),
    )
    return int(selected[0])


def render_num_input(key, cfg):
    return st.number_input(
        f'{cfg["label"]} ({cfg["unit"]})',
        min_value=float(cfg["min"]),
        max_value=float(cfg["max"]),
        value=float(cfg["default"]),
        step=float(cfg.get("step", 1.0)),
        format="%.0f",
        key=f"num_{key}",
    )


def format_feature_value(key, value):
    mapping = VALUE_MAPPINGS.get(key, {})
    try:
        if float(value).is_integer():
            iv = int(value)
            if iv in mapping:
                return f"{iv} - {mapping[iv]}"
    except Exception:
        pass

    unit = UNITS.get(key)
    if unit:
        if isinstance(value, (int, float, np.number)):
            return f"{float(value):g} {unit}"
        return f"{value} {unit}"

    return str(value)


def format_shap_feature_value(key, value):
    mapping = VALUE_MAPPINGS.get(key, {})

    try:
        if float(value).is_integer():
            iv = int(value)
            if iv in mapping:
                return str(mapping[iv])
    except Exception:
        pass

    unit = UNITS.get(key)
    if unit:
        try:
            return f"{float(value):g} {unit}"
        except Exception:
            return f"{value} {unit}"

    return str(value)


def build_summary_html(user_inputs):
    rows = []
    for key in FINAL_FEATURES:
        label = VARIABLE_LABELS_DICT.get(key, key)
        value = format_feature_value(key, user_inputs[key])
        rows.append(f"<tr><td>{label}</td><td>{value}</td></tr>")
    return '<table class="summary-table">' + "".join(rows) + "</table>"


def plot_compact_shap_bar(
    shap_vec,
    feature_names,
    display_values=None,
    max_display=7,
):
    shap_vec = np.asarray(shap_vec, dtype=float).ravel()
    feature_names = list(feature_names)

    if display_values is None:
        display_values = [""] * len(feature_names)
    else:
        display_values = list(display_values)

    df = pd.DataFrame({
        "feature": feature_names,
        "value": display_values,
        "shap": shap_vec,
        "abs_shap": np.abs(shap_vec),
    })

    df = (
        df.sort_values("abs_shap", ascending=False)
        .head(max_display)
        .sort_values("shap", ascending=True)
        .reset_index(drop=True)
    )

    labels = []
    for _, row in df.iterrows():
        value_text = str(row["value"]).strip()
        if value_text:
            labels.append(f"{value_text} = {row['feature']}")
        else:
            labels.append(str(row["feature"]))

    colors = ["#c2415c" if v > 0 else "#3b82c4" for v in df["shap"]]

    fig, ax = plt.subplots(figsize=(8.8, 3.35))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    y_pos = np.arange(len(df))
    ax.barh(y_pos, df["shap"], color=colors, alpha=0.95, height=0.58)

    max_abs = max(float(df["abs_shap"].max()), 0.12)
    x_pad = max_abs * 0.28
    x_left = -max_abs - x_pad
    x_right = max_abs + x_pad
    ax.set_xlim(x_left, x_right)

    ax.axvline(0, color="#b8b3aa", linewidth=1.1)

    inside_threshold = max_abs * 0.20
    text_pad_inside = max_abs * 0.04
    text_pad_outside = max_abs * 0.03

    for i, v in enumerate(df["shap"]):
        label = f"{v:+.2f}"
        if abs(v) >= inside_threshold:
            if v >= 0:
                x_text = v - text_pad_inside
                ha = "right"
            else:
                x_text = v + text_pad_inside
                ha = "left"

            ax.text(
                x_text,
                i,
                label,
                va="center",
                ha=ha,
                fontsize=10.5,
                fontweight="800",
                color="white",
            )
        else:
            if v >= 0:
                x_text = v + text_pad_outside
                ha = "left"
            else:
                x_text = v - text_pad_outside
                ha = "right"

            ax.text(
                x_text,
                i,
                label,
                va="center",
                ha=ha,
                fontsize=10.5,
                fontweight="800",
                color="#2b2b2b",
            )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10.5, color="#2b2b2b")
    ax.tick_params(axis="x", labelsize=10.2, colors="#5f5a52")
    ax.tick_params(axis="y", length=0)

    ax.set_xlabel(
        "SHAP contribution to model output",
        fontsize=10.3,
        color="#5f5a52",
        labelpad=8,
    )

    ax.set_title(
        "Top feature contributions for this case",
        fontsize=12.5,
        fontweight="850",
        color="#2b2b2b",
        pad=8,
    )

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#d8d2c8")

    ax.grid(axis="x", color="#eee9e1", linestyle="--", linewidth=0.8, alpha=0.85)
    ax.set_axisbelow(True)

    fig.tight_layout()
    return fig


# =============================================================================
# Sidebar controls
# =============================================================================
with st.sidebar:
    st.markdown("### Model Controls")
    st.caption("Research-use deployment interface")

    default_thr = load_threshold(THRESHOLD_JSON_PATH, THRESHOLD_KEY, 0.642)

    threshold = st.slider(
        "Classification threshold",
        min_value=0.000,
        max_value=1.000,
        value=float(default_thr),
        step=0.001,
        format="%.3f",
    )

    show_shap = st.toggle("Show SHAP contribution chart", value=True)

    st.divider()
    st.markdown("### Intended Use")
    st.caption(
        "This dashboard is intended for caregiver stress screening support in a research or pilot deployment setting. "
        "It is not a standalone diagnostic system."
    )


# =============================================================================
# Load artefacts
# =============================================================================
missing = []
for label, path in [("Model", MODEL_PATH), ("Preprocessor", PREPROCESSOR_PATH)]:
    if not os.path.exists(path):
        missing.append((label, path))

if missing:
    st.error("Required files are missing. Please check your deployment paths.")
    for label, path in missing:
        st.code(f"{label}: {path}")
    st.stop()

preprocessor, model = load_artifacts()
TRANSFORMED_FEATURE_NAMES = get_transformed_feature_names(preprocessor, FINAL_FEATURES)


# =============================================================================
# Session state for persistent results
# =============================================================================
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None


# =============================================================================
# Header
# =============================================================================
st.markdown(
    f"""
<div class="top-shell">
  <div>
    <div class="eyebrow">CareRisk Clinical Dashboard</div>
    <div class="brand-title">Caregiver Stress Risk Screening</div>
    <div class="brand-subtitle">Single-page clinical deployment interface with model output and explainability</div>
  </div>
  <div class="top-meta">
    <span class="meta-chip"><span class="dot"></span> Model online</span>
    <span class="meta-chip">Threshold {threshold:.3f}</span>
    <span class="meta-chip">{datetime.now().strftime("%Y-%m-%d %H:%M")}</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# =============================================================================
# Input form
# =============================================================================
st.markdown(
    """
<div class="panel">
  <div class="panel-header">
    <div>
      <div class="panel-title">Enter Features</div>
    </div>
    <span class="tag">Input</span>
  </div>
  <div class="panel-body">
""",
    unsafe_allow_html=True,
)

with st.form("prediction_form"):
    left_col, right_col = st.columns(2, gap="large")
    user_inputs = {}

    with left_col:
        st.markdown("**Caregiver information**")
        user_inputs["daydurG"] = render_num_input("daydurG", CAREGIVER_NUM["daydurG"])
        user_inputs["age_G"] = render_num_input("age_G", CAREGIVER_NUM["age_G"])
        user_inputs["healthG"] = render_cat_input("healthG", CAREGIVER_CAT["healthG"])

        st.markdown(
            '<div class="form-note">Care duration and caregiver self-rated health are useful contextual signals for stress screening.</div>',
            unsafe_allow_html=True,
        )

    with right_col:
        st.markdown("**Recipient information**")
        user_inputs["ageR"] = render_num_input("ageR", RECIPIENT_NUM["ageR"])
        user_inputs["healthR"] = render_cat_input("healthR", RECIPIENT_CAT["healthR"])
        user_inputs["adlR"] = render_cat_input("adlR", RECIPIENT_CAT["adlR"])
        user_inputs["is_citycentre"] = render_cat_input("is_citycentre", RECIPIENT_CAT["is_citycentre"])

        st.markdown(
            '<div class="form-note">ADL limitation, recipient health status, and living context help contextualise caregiving burden.</div>',
            unsafe_allow_html=True,
        )

    submitted = st.form_submit_button("Predict", use_container_width=False)

st.markdown("</div></div>", unsafe_allow_html=True)


# =============================================================================
# Prediction execution
# =============================================================================
if submitted:
    try:
        df_input = ensure_feature_dataframe(user_inputs, FINAL_FEATURES)
        X_transformed = preprocessor.transform(df_input)
        prob = predict_proba_single(model, X_transformed)
        pred = int(prob >= threshold)

        st.session_state.prediction_result = {
            "user_inputs": user_inputs,
            "df_input": df_input,
            "X_transformed": X_transformed,
            "prob": prob,
            "pred": pred,
            "threshold": threshold,
        }

    except Exception as e:
        st.error(f"Prediction failed: {e}")


# =============================================================================
# Result display - single page
# =============================================================================
result = st.session_state.prediction_result

if result is not None:
    prob = result["prob"]
    pred = result["pred"]
    thr = result["threshold"]
    user_inputs = result["user_inputs"]
    df_input = result["df_input"]
    X_transformed = result["X_transformed"]

    risk_class = "high" if pred == 1 else "low"
    risk_label = "High stress risk" if pred == 1 else "Lower stress risk"

    banner_text = (
        f"Predicted probability of caregiver stress is {prob * 100:.1f}% (≥ threshold {thr:.3f}). "
        f"This screening suggests a high risk of stress."
        if pred == 1
        else
        f"Predicted probability of caregiver stress is {prob * 100:.1f}% (< threshold {thr:.3f}). "
        f"This screening suggests a lower risk of stress."
    )

    st.markdown(
        """
<div class="panel">
  <div class="panel-header">
    <div>
      <div class="panel-title">Clinical Risk Output</div>
    </div>
    <span class="tag">Prediction</span>
  </div>
  <div class="panel-body">
""",
        unsafe_allow_html=True,
    )

    # Gauge + summary
    st.markdown('<div class="result-layout">', unsafe_allow_html=True)
    gauge_col, summary_col = st.columns([0.95, 1.45], gap="large")

    with gauge_col:
        st.markdown(
            """
<div class="panel compact">
  <div class="panel-header">
    <div>
      <div class="panel-title">Risk Gauge</div>
      <div class="panel-subtitle">Probability relative to threshold</div>
    </div>
  </div>
  <div class="panel-body">
""",
            unsafe_allow_html=True,
        )

        components.html(build_gauge_svg(prob, thr), height=208, scrolling=False)

        st.markdown(
            """
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="alert-banner {risk_class}">
  <strong>{risk_label}</strong><br>
  {banner_text}
</div>
<div class="risk-note">
  This is a screening aid, not a diagnosis.
</div>
""",
            unsafe_allow_html=True,
        )

    with summary_col:
        st.markdown(
            """
<div class="panel">
  <div class="panel-header">
    <div>
      <div class="panel-title">Input Summary</div>
    </div>
    <span class="tag">Case</span>
  </div>
  <div class="panel-body">
"""
            + build_summary_html(user_inputs)
            + """
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # SHAP contribution chart
    if show_shap:
        st.markdown(
            """
<div class="panel">
  <div class="panel-header">
    <div>
      <div class="panel-title">SHAP Contribution Summary</div>
    </div>
    <span class="tag">Explainability</span>
  </div>
  <div class="panel-body">
""",
            unsafe_allow_html=True,
        )

        try:
            base_model = get_tree_model_for_shap(model)
            explainer = shap.TreeExplainer(
                base_model,
                feature_perturbation="tree_path_dependent",
            )

            shap_values = explainer.shap_values(X_transformed)

            if isinstance(shap_values, list):
                shap_vec = np.asarray(
                    shap_values[1] if len(shap_values) > 1 else shap_values[0]
                ).reshape(1, -1)
            elif hasattr(shap_values, "values"):
                shap_vec = np.asarray(shap_values.values).reshape(1, -1)
            else:
                shap_vec = np.asarray(shap_values).reshape(1, -1)

            raw_input_dict = df_input.iloc[0].to_dict()

            display_data = []
            display_names = []

            for feat in TRANSFORMED_FEATURE_NAMES:
                original_key = feat.split("__")[-1]
                display_names.append(VARIABLE_LABELS_DICT.get(original_key, original_key))
                display_data.append(
                    format_shap_feature_value(
                        original_key,
                        raw_input_dict.get(original_key, ""),
                    )
                )

            fig = plot_compact_shap_bar(
                shap_vec=shap_vec[0],
                feature_names=display_names,
                display_values=display_data,
                max_display=min(7, len(display_names)),
            )

            st.pyplot(fig, clear_figure=True)

            st.caption(
                "Positive SHAP values increase predicted stress risk; "
                "negative SHAP values decrease predicted stress risk."
            )

        except Exception as shap_error:
            st.warning(f"SHAP explanation could not be rendered: {shap_error}")

        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("</div></div>", unsafe_allow_html=True)


# =============================================================================
# Footer
# =============================================================================
st.markdown(
    """
<div class="footer-note">
  © 2026 CareRisk Clinical Dashboard
</div>
""",
    unsafe_allow_html=True,
)