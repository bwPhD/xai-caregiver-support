import os
import json
import joblib
import pickle
import numpy as np
import pandas as pd
import streamlit as st
import shap
import matplotlib.pyplot as plt

# ---------------------- Page & CSS ----------------------
st.set_page_config(page_title="Caregiver Stress Risk • ML Calculator", layout="wide")
st.markdown(
    """
    <style>
      /* Tidy base UI */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
      .block-container {padding-top: 1.25rem; max-width: 1080px;}
      h1, h2, h3 {font-weight: 600;}
      div[data-testid="stMetric"] {background:#f8fafc;border:1px solid #eee;border-radius:12px;padding:0.6rem 0.9rem;}
      div.stButton > button {border-radius:12px; padding:0.5rem 1.0rem;}
      .small-note {color:#6b7280; font-size:0.85rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------- Feature schema / labels / value maps ----------------------
feature_ranges = {
    "daydurG": {"type": "numerical", "min": 0.0, "max": 24,  "default": 12},     # hours/day
    "age_G"  : {"type": "numerical", "min": 0,   "max": 120, "default": 60.0},   # caregiver age
    "ageR"   : {"type": "numerical", "min": 60,   "max": 120, "default": 60.0},   # recipient age
    "caredurG": {"type": "numerical", "min": 0,  "max": 120, "default": 60.0},   # caregiving years
    "healthR": {"type": "categorical", "options": [1, 5]},
    "healthG": {"type": "categorical", "options": [1, 5]},
    "adlR"   : {"type": "categorical", "options": [0, 3]},
    "adlG"   : {"type": "categorical", "options": [0, 3]},
    "hukou_cityR": {"type": "categorical", "options": [0, 1]},
    "is_citycentre": {"type": "categorical", "options": [0, 1]},
}

VARIABLE_LABELS_DICT = {
    'daydurG': 'Daily care hours (Caregiver)',
    'healthR': 'Self-rated health (Recipient)',
    'age_G'  : 'Age (Caregiver)',
    'adlR'   : 'ADL (Recipient)',
    'caredurG': 'Duration of care (Caregiver)',
    'healthG': 'Self-rated health (Caregiver)',
    'ageR'   : 'Age (Recipient)',
    'adlG'   : 'ADL (Caregiver)',
    'hukou_cityR': 'Hukou status (Recipient)',
    'is_citycentre': 'City-center residence (Recipient)'
}

VALUE_MAPPINGS = {
    'adlG': {0: 'Intact', 1: 'Mild', 2: 'Moderate', 3: 'Severe'},
    'adlR': {0: 'Intact', 1: 'Mild', 2: 'Moderate', 3: 'Severe'},
    'healthR': {1: 'Very poor', 2: 'Poor', 3: 'Fair', 4: 'Good', 5: 'Excellent'},
    'hukou_cityR': {0: 'Rural', 1: 'Urban'},
    'is_citycentre': {0: 'No', 1: 'Yes'},
    'healthG': {1: 'Very poor', 2: 'Poor', 3: 'Fair', 4: 'Good', 5: 'Excellent'},
}

UNITS = {
    'daydurG': 'hours',
    'age_G'  : 'years',
    'ageR'   : 'years',
    'caredurG': 'years',
}

# ---------------------- Paths & model columns ----------------------
MODEL_PATH = os.getenv("MODEL_PATH", "models/xgboost.pkl")
PREPROCESSOR_PATH = os.getenv("PREPROCESSOR_PATH", "models/preprocessor.pkl")
THRESHOLD_JSON_PATH = os.getenv("THRESHOLD_JSON", "models/best_thresholds.json")
THRESHOLD_KEY = os.getenv("THRESHOLD_KEY", "XGBoost")

FINAL_FEATURES = [
    'daydurG','healthR','age_G','adlR','caredurG','healthG','ageR','adlG','hukou_cityR','is_citycentre'
]

# ---------------------- Load artifacts ----------------------
if not os.path.exists(PREPROCESSOR_PATH):
    st.error(f"Preprocessor not found: {PREPROCESSOR_PATH}")
    st.stop()
with open(PREPROCESSOR_PATH, "rb") as f:
    preprocessor = pickle.load(f)

if not os.path.exists(MODEL_PATH):
    st.error(f"Model not found: {MODEL_PATH}")
    st.stop()
try:
    model = joblib.load(MODEL_PATH)
except Exception:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)


def load_threshold(path: str, key: str, default: float = 0.5) -> float:
    if not os.path.exists(path):
        return float(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return float(d.get(key, default))
    except Exception:
        return float(default)

BEST_THRESHOLD = load_threshold(THRESHOLD_JSON_PATH, THRESHOLD_KEY, 0.5)

NUM_COLS = [k for k, cfg in feature_ranges.items() if cfg["type"] == "numerical"]
CAT_COLS = [k for k, cfg in feature_ranges.items() if cfg["type"] == "categorical"]

# ---------------------- Helpers ----------------------

def ensure_feature_dataframe(input_dict, feature_order):
    df = pd.DataFrame([input_dict])
    missing = [c for c in feature_order if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    return df[feature_order].copy()


def predict_proba(model, X: np.ndarray) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        z = model.decision_function(X)
        return 1.0 / (1.0 + np.exp(-z))
    raise RuntimeError("Model does not support probability outputs")


def risk_narrative(prob: float, thr: float) -> tuple[str, str]:
    """Return (label, paragraph) for the probability and threshold.
    Binary: prob >= thr -> High risk; else Low risk.
    """
    pct = f"{prob*100:.1f}%"
    if prob >= thr:
        label = "High stress risk"
        text = (
            f"Predicted probability of caregiver stress is {pct} (≥ threshold {thr:.2f}). "
            "This screening suggests a high risk of stress. "
        )
    else:
        label = "Low stress risk"
        text = (
            f"Predicted probability of caregiver stress is {pct} (< threshold {thr:.2f}). "
            "No immediate concern indicated by this model."
        )
    return label, text

# ---------------------- Sidebar ----------------------
st.sidebar.header("Settings")
thr = st.sidebar.slider("Classification threshold", 0.0, 1.0, float(BEST_THRESHOLD), 0.01)
show_shap = st.sidebar.checkbox("Show SHAP waterfall", value=True)
# ---------------------- Main ----------------------
st.title("Caregiver Stress Risk — ML Calculator")

st.subheader("Enter features")
with st.form("single_form"):
    left, right = st.columns(2)
    user_inputs = {}

    with left:
        st.markdown("**Continuous variables**")
        for key, cfg in feature_ranges.items():
            if cfg["type"] != "numerical":
                continue
            label = VARIABLE_LABELS_DICT.get(key, key)
            unit = UNITS.get(key)
            if unit:
                label = f"{label} ({unit})"
            min_v = float(cfg.get("min", 0.0))
            max_v = float(cfg.get("max", 1.0))
            default = float(cfg.get("default", min_v))
            all_int = float(default).is_integer() and float(min_v).is_integer() and float(max_v).is_integer()
            step = 1.0 if all_int else 0.1
            user_inputs[key] = st.number_input(
                label, value=default, min_value=min_v, max_value=max_v, step=step, format="%.4f"
            )

    with right:
        st.markdown("**Categorical / indicator variables**")
        for key, cfg in feature_ranges.items():
            if cfg["type"] != "categorical":
                continue
            label = VARIABLE_LABELS_DICT.get(key, key)
            opts_def = cfg.get("options", [0, 1])
            if isinstance(opts_def, (list, tuple)) and len(opts_def) == 2 and \
               all(isinstance(x, (int, float)) for x in opts_def):
                lo, hi = int(opts_def[0]), int(opts_def[1])
                values = list(range(lo, hi + 1))
            else:
                values = list(opts_def)
            mapping = VALUE_MAPPINGS.get(key, {})
            options = [(v, f"{v} - {mapping.get(v, str(v))}" if mapping else str(v)) for v in values]
            sel = st.selectbox(label, options=options, index=0, format_func=lambda o: o[1])
            user_inputs[key] = int(sel[0])

    submitted = st.form_submit_button("Predict")

if submitted:
    try:
        # 1) to model space
        df_single_orig = ensure_feature_dataframe(user_inputs, FINAL_FEATURES)
        X_single_model = preprocessor.transform(df_single_orig)

        # 2) predict & label
        prob = float(predict_proba(model, X_single_model))
        pred = int(prob >= thr)
        label, paragraph = risk_narrative(prob, thr)

        # 3) metrics & diagnosis
        m1, m2, m3 = st.columns(3)
        m1.metric("Probability", f"{prob*100:.2f}%")
        m2.metric("Threshold", f"{thr:.2f}")
        m3.metric("Predicted label", str(pred))

        if pred == 1:
            st.error(label)
        else:
            st.success(label)
        st.markdown(paragraph)
        st.markdown("<div class='small-note'>This is a screening aid, not a diagnosis.</div>", unsafe_allow_html=True)

        # 4) input echo (labeled)
        disp_rows = []
        for k in FINAL_FEATURES:
            label_k = VARIABLE_LABELS_DICT.get(k, k)
            v = df_single_orig.iloc[0][k]
            if k in VALUE_MAPPINGS and v in VALUE_MAPPINGS[k]:
                disp_rows.append({"Feature": label_k, "Value": f"{v} - {VALUE_MAPPINGS[k][v]}"})
            else:
                unit = UNITS.get(k)
                disp_rows.append({"Feature": label_k, "Value": f"{v} {unit}" if unit else v})
        st.markdown("**Input summary**")
        st.dataframe(pd.DataFrame(disp_rows))

        # 5) SHAP waterfall (single case)
        if show_shap:
            st.subheader("SHAP waterfall (single case)")
            # Model is CalibratedClassifierCV; unwrap to the underlying tree estimator
            tree_model = model.calibrated_classifiers_[0].estimator
            explainer = shap.TreeExplainer(tree_model, feature_perturbation="tree_path_dependent")

            _sv = explainer.shap_values(X_single_model)
            if isinstance(_sv, list):
                shap_vec = _sv[1] if len(_sv) > 1 else _sv[0]
                shap_vec = np.asarray(shap_vec).reshape(1, -1)
                base = (
                    explainer.expected_value[1]
                    if isinstance(explainer.expected_value, (list, np.ndarray)) and len(explainer.expected_value) > 1
                    else explainer.expected_value
                )
            elif hasattr(_sv, "values"):
                shap_vec = np.asarray(_sv.values).reshape(1, -1)
                base = _sv.base_values if hasattr(_sv, "base_values") else explainer.expected_value
            else:
                shap_vec = np.asarray(_sv).reshape(1, -1)
                base = explainer.expected_value

            feat_labels = [VARIABLE_LABELS_DICT.get(k, k) for k in df_single_orig.columns]
            display_vals = []
            for k, v in zip(df_single_orig.columns, df_single_orig.iloc[0].values):
                mapping = VALUE_MAPPINGS.get(k, {})
                if k in VALUE_MAPPINGS:
                    vv = int(v) if isinstance(v, (int, float)) and float(v).is_integer() else v
                    if vv in mapping:
                        display_vals.append(f"{vv} - {mapping[vv]}")
                    else:
                        unit = UNITS.get(k)
                        display_vals.append(f"{v} {unit}" if unit else v)
                else:
                    unit = UNITS.get(k)
                    display_vals.append(f"{v} {unit}" if unit else v)

            shap_ex = shap.Explanation(
                values=shap_vec[0],
                base_values=base,
                data=np.array(display_vals, dtype=object),
                feature_names=feat_labels,
            )
            fig = plt.figure(figsize=(12, 6))
            shap.plots.waterfall(shap_ex, max_display=len(feat_labels))
            st.pyplot(fig, clear_figure=True)

    except Exception as e:
        st.error(f"Prediction failed: {e}")

st.caption("© 2025 Caregiver ML — Online scoring.")
