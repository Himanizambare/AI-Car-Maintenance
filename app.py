# streamlit_app_with_server_tts.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import threading
import json

# Try to import pyttsx3; if unavailable, disable server TTS gracefully
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    pyttsx3 = None
    TTS_AVAILABLE = False

# small helper to embed raw html/js
from streamlit.components.v1 import html as st_html

# ------------------ PAGE CONFIG & STYLE ------------------ #
st.set_page_config(
    page_title="AI Car Maintenance Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --bg: #0b1220; --card:#0f1724; --muted:#9aa5b1; --accent:#6C63FF; --panel-text: #e6eef8; --muted-2: #9aa5b1; }
    /* page background */
    .main { background: linear-gradient(135deg,#111827, #0b1220); color: var(--panel-text); }

    /* spacing */
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }

    /* KPI card — keep light styling but adapt for dark theme */
    .kpi-card { background: rgba(255,255,255,0.04); border-radius: 16px; padding: 16px 20px; box-shadow: 0 8px 18px rgba(2,6,23,0.6); color: var(--panel-text); }

    /* Panels (changed to dark card) */
    .panel { background: var(--card); color: var(--panel-text); border-radius: 18px; padding: 22px 26px; box-shadow: 0 10px 22px rgba(2,6,23,0.7); }

    .tag-pill { border-radius: 999px; padding: 4px 14px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    .tag-online { background: rgba(34,197,94,0.08); color: #16a34a; border: 1px solid rgba(34,197,94,0.25); }
    .tag-critical { background: rgba(254,226,226,0.06); color: #fca5a5; border: 1px solid rgba(254,202,202,0.12); }

    .agent-chip { border-radius: 999px; background: rgba(255,255,255,0.02); padding: 4px 10px; font-size: 0.75rem; margin-right: 6px; margin-bottom: 4px; display: inline-block; color: var(--panel-text); }
    .timeline-row { font-size: 0.85rem; padding: 6px 0; border-bottom: 1px dashed rgba(255,255,255,0.03); color: var(--panel-text); }

    .fab { position: fixed; right: 18px; bottom: 20px; z-index:99999; }
    .fab button { background: linear-gradient(90deg,#6C63FF, #3da8ff); color:white; border:none; padding:12px 14px; border-radius:999px; font-weight:700; box-shadow:0 12px 30px rgba(0,0,0,0.35); }

    /* FIXED CHAT BUBBLES — dark translucent background + white text */
    .user-bubble {
        background: rgba(255, 255, 255, 0.06);
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        color: #ffffff !important;
        font-weight: 500;
        border: 1px solid rgba(255,255,255,0.03);
    }

    .assistant-bubble {
        background: rgba(255, 255, 255, 0.08);
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        color: #ffffff !important;
        font-weight: 500;
        border: 1px solid rgba(255,255,255,0.04);
    }

    /* Make bubble text readable even if nested elements are added */
    .user-bubble p,
    .assistant-bubble p,
    .user-bubble span,
    .assistant-bubble span,
    .user-bubble b,
    .assistant-bubble b {
        color: #ffffff !important;
    }

    /* Streamlit default input / textarea adjustments for dark look */
    textarea, input[type="text"], input[type="number"], .stTextInput > div > input, .stTextArea > div > textarea {
        background: rgba(255,255,255,0.02) !important;
        color: #e6eef8 !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        border-radius: 8px !important;
    }

    /* smaller captions / notes */
    .css-1f6l7lp, .stCaption, .stMarkdown p {
        color: var(--muted-2) !important;
    }

    /* make sidebar match dark theme */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b0f14, #0b1016);
        color: var(--panel-text);
    }

    /* reduce contrast on code blocks inside panels */
    .panel code {
        background: rgba(255,255,255,0.02);
        padding: 4px 6px;
        border-radius: 6px;
        color: #e6eef8;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------ SYNTHETIC DATA (expanded to 20 vehicles) ------------------ #
def build_synthetic_vehicles():
    base_year = datetime.now().year
    vehicles = [
        {"id": "V001", "make": "Hero", "model": "Xtreme 160R", "year": base_year-1, "city": "Mumbai", "segment": "2W", "avg_km_per_day": 38},
        {"id": "V002", "make": "Hero", "model": "Splendor Plus", "year": base_year-3, "city": "Pune", "segment": "2W", "avg_km_per_day": 32},
        {"id": "V003", "make": "Hero", "model": "Glamour", "year": base_year-2, "city": "Delhi", "segment": "2W", "avg_km_per_day": 45},
        {"id": "V004", "make": "Hero", "model": "Maestro Edge", "year": base_year-4, "city": "Nagpur", "segment": "2W", "avg_km_per_day": 25},
        {"id": "V005", "make": "Mahindra", "model": "XUV700", "year": base_year-1, "city": "Bengaluru", "segment": "4W", "avg_km_per_day": 52},
        {"id": "V006", "make": "Mahindra", "model": "Scorpio N", "year": base_year-5, "city": "Chennai", "segment": "4W", "avg_km_per_day": 40},
        {"id": "V007", "make": "Mahindra", "model": "Thar", "year": base_year-3, "city": "Jaipur", "segment": "4W", "avg_km_per_day": 30},
        {"id": "V008", "make": "Mahindra", "model": "Bolero Neo", "year": base_year-6, "city": "Lucknow", "segment": "4W", "avg_km_per_day": 34},
        {"id": "V009", "make": "Hero", "model": "Xpulse 200", "year": base_year-2, "city": "Hyderabad", "segment": "2W", "avg_km_per_day": 48},
        {"id": "V010", "make": "Mahindra", "model": "XUV300", "year": base_year-4, "city": "Indore", "segment": "4W", "avg_km_per_day": 29},
        # extra vehicles to reach up to 20
        {"id": "V011", "make": "Hero", "model": "Destini 125", "year": base_year-2, "city": "Surat", "segment": "2W", "avg_km_per_day": 28},
        {"id": "V012", "make": "Mahindra", "model": "Bolero", "year": base_year-7, "city": "Ranchi", "segment": "4W", "avg_km_per_day": 36},
        {"id": "V013", "make": "Tata", "model": "Nexon EV", "year": base_year-1, "city": "Kolkata", "segment": "4W", "avg_km_per_day": 44},
        {"id": "V014", "make": "Tata", "model": "Harrier", "year": base_year-3, "city": "Ahmedabad", "segment": "4W", "avg_km_per_day": 31},
        {"id": "V015", "make": "Maruti", "model": "Swift", "year": base_year-2, "city": "Bengaluru", "segment": "4W", "avg_km_per_day": 38},
        {"id": "V016", "make": "Hyundai", "model": "i20", "year": base_year-1, "city": "Pune", "segment": "4W", "avg_km_per_day": 29},
        {"id": "V017", "make": "Kia", "model": "Seltos", "year": base_year-4, "city": "Chennai", "segment": "4W", "avg_km_per_day": 33},
        {"id": "V018", "make": "Honda", "model": "CB Shine", "year": base_year-2, "city": "Lucknow", "segment": "2W", "avg_km_per_day": 26},
        {"id": "V019", "make": "RoyalEnfield", "model": "Classic 350", "year": base_year-3, "city": "Jaipur", "segment": "2W", "avg_km_per_day": 22},
        {"id": "V020", "make": "Mahindra", "model": "Marazzo", "year": base_year-5, "city": "Delhi", "segment": "4W", "avg_km_per_day": 27},
    ]
    return pd.DataFrame(vehicles)

def build_maintenance_logs():
    random.seed(42)
    vehicles = [f"V{str(i).zfill(3)}" for i in range(1, 21)]
    components = ["Brakes", "Battery", "Engine", "Tyres", "Suspension"]
    issues = {
        "Brakes": "Brake pad wear",
        "Battery": "Cranking issue",
        "Engine": "Overheating",
        "Tyres": "Uneven wear",
        "Suspension": "Noise on bumps",
    }
    rca_tags = {
        "Brakes": "City stop-go traffic",
        "Battery": "Short trips / accessories",
        "Engine": "Low coolant / oil quality",
        "Tyres": "Improper alignment",
        "Suspension": "Bad roads",
    }
    capa_actions = {
        "Brakes": "Upgrade pad material; better cooling slots",
        "Battery": "Higher CCA rating; smart alternator profile",
        "Engine": "Improved cooling routing; sensor calibration",
        "Tyres": "Factory alignment spec update",
        "Suspension": "Reinforced bushings",
    }

    rows = []
    today = datetime.now().date()
    for _ in range(200):  # more synthetic records for larger dataset
        comp = random.choice(components)
        v = random.choice(vehicles)
        when = today - timedelta(days=random.randint(1, 730))  # broader date range
        severity = random.randint(1, 5)
        cost = random.randint(800, 20000)
        rows.append(
            {
                "vehicle_id": v,
                "date": when,
                "component": comp,
                "issue": issues[comp],
                "severity": severity,
                "cost": cost,
                "rca_tag": rca_tags[comp],
                "capa_action": capa_actions[comp],
            }
        )
    return pd.DataFrame(rows)

VEHICLES_DF = build_synthetic_vehicles()
MAINT_DF = build_maintenance_logs()

# ------------------ SIMPLE VOICE AGENT (SERVER TTS) ------------------ #
class VoiceAgentServer:
    def __init__(self, rate: int = 150, speak_enabled: bool = True):
        self.speak_enabled = speak_enabled and TTS_AVAILABLE
        self.engine = None
        if self.speak_enabled:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", rate)
            except Exception as e:
                print("pyttsx3 init failed:", e)
                self.speak_enabled = False

    def _runner(self, text: str):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print("TTS speak failed:", e)

    def speak_async(self, text: str):
        if not self.speak_enabled:
            # fallback print for debug
            print("[VOICE DISABLED] " + text)
            return
        t = threading.Thread(target=self._runner, args=(text,), daemon=True)
        t.start()

    def speak(self, text: str):
        if not self.speak_enabled:
            print("[VOICE DISABLED] " + text)
            return
        self._runner(text)

voice_agent = VoiceAgentServer(speak_enabled=True)

# ------------------ SIMPLE SCHEDULER (demo) ------------------ #
class SchedulingAgentSimple:
    def __init__(self):
        pass

    def book_service(self, vehicle_id: str, issue: str, city: str = "Unknown"):
        today = datetime.now().date()
        slot = (today + timedelta(days=2)).strftime("%d %b %Y") + " – 10:00 AM"
        return {"status": "booked", "slot": slot, "vehicle_id": vehicle_id, "issue": issue}

sched_agent_simple = SchedulingAgentSimple()

# ------------------ AGENTIC AI LAYER ------------------ #
class UebaMonitor:
    def __init__(self):
        self.baseline_access = {
            "DataAnalysisAgent": {"telematics_stream", "maintenance_db"},
            "DiagnosisAgent": {"analysis_results"},
            "CustomerEngagementAgent": {"customer_profile", "analysis_results"},
            "SchedulingAgent": {"scheduler_api", "customer_profile"},
            "FeedbackAgent": {"feedback_db", "customer_profile"},
            "ManufacturingInsightsAgent": {"maintenance_db", "rca_capa_db"},
        }
        self.actions_log = []

    def log_action(self, agent, action, resource, meta=None):
        meta = meta or {}
        timestamp = datetime.now().strftime("%H:%M:%S")
        allowed = resource in self.baseline_access.get(agent, set())
        anomaly = not allowed
        self.actions_log.append(
            {
                "time": timestamp,
                "agent": agent,
                "action": action,
                "resource": resource,
                "anomaly": anomaly,
                "meta": meta,
            }
        )

    def anomalies(self):
        return [a for a in self.actions_log if a["anomaly"]]

class DataAnalysisAgent:
    def __init__(self, ueba: UebaMonitor):
        self.ueba = ueba

    def analyze(self, input_payload, maint_df: pd.DataFrame):
        self.ueba.log_action("DataAnalysisAgent", "read", "telematics_stream")
        self.ueba.log_action("DataAnalysisAgent", "read", "maintenance_db")

        engine = input_payload["engine_temp"]
        brake = input_payload["brake_health"]
        battery = input_payload["battery_health"]
        tyre = input_payload["tyre_pressure"]
        mileage = input_payload["mileage"]
        year = input_payload["year"]

        now_year = datetime.now().year
        age_factor = max(0, now_year - year) / 10.0
        mileage_factor = min(1.0, mileage / 150000)
        engine_factor = max(0, (engine - 195) / 60)
        brake_factor = max(0, (60 - brake) / 40)
        battery_factor = max(0, (55 - battery) / 40)
        tyre_factor = max(0, abs(32 - tyre) / 12)

        raw_score = (
            0.20 * age_factor
            + 0.25 * mileage_factor
            + 0.20 * engine_factor
            + 0.15 * brake_factor
            + 0.10 * battery_factor
            + 0.10 * tyre_factor
        )
        risk_score = float(max(0.0, min(1.0, raw_score)))

        if risk_score < 0.25:
            risk_band = "Low"
        elif risk_score < 0.5:
            risk_band = "Moderate"
        elif risk_score < 0.75:
            risk_band = "High"
        else:
            risk_band = "Critical"

        likely_components = []
        if engine_factor > 0.3:
            likely_components.append("Engine cooling / oil circuit")
        if brake_factor > 0.25:
            likely_components.append("Brake pads & brake fluid")
        if battery_factor > 0.2:
            likely_components.append("Battery & charging system")
        if tyre_factor > 0.3:
            likely_components.append("Tyre pressure & wheel alignment")
        if not likely_components:
            likely_components.append("Routine check only – no acute risk")

        base_daily = int(len(VEHICLES_DF) * 0.4)
        x_days = np.arange(30)
        seasonality = 4 * np.sin(x_days / 6)
        forecast = pd.DataFrame(
            {
                "date": [datetime.now().date() + timedelta(days=int(d)) for d in x_days],
                "expected_jobs": [
                    max(1, int(base_daily + seasonality[i] + random.randint(-2, 3)))
                    for i in range(30)
                ],
            }
        )

        return {
            "risk_score": risk_score,
            "risk_band": risk_band,
            "likely_components": likely_components,
            "forecast": forecast,
        }

class DiagnosisAgent:
    def __init__(self, ueba: UebaMonitor):
        self.ueba = ueba

    def diagnose(self, analysis_output):
        self.ueba.log_action("DiagnosisAgent", "read", "analysis_results")
        score = analysis_output["risk_score"]
        band = analysis_output["risk_band"]
        components = analysis_output["likely_components"]

        if band == "Low":
            sla_days = 30
        elif band == "Moderate":
            sla_days = 15
        elif band == "High":
            sla_days = 7
        else:
            sla_days = 2

        eta_date = datetime.now().date() + timedelta(days=sla_days)

        est_cost = 1500 + int(score * 15000)
        potential_saving = int(est_cost * 0.35)

        summary = f"Risk is **{band}** with score {score:.2f}. Recommended to visit within **{sla_days} days** (by {eta_date})."
        return {
            "sla_days": sla_days,
            "target_date": eta_date,
            "estimated_cost": est_cost,
            "potential_saving": potential_saving,
            "summary": summary,
            "components": components,
        }

class SchedulingAgent:
    def __init__(self, ueba: UebaMonitor):
        self.ueba = ueba

    def schedule(self, city, diagnosis_output):
        self.ueba.log_action("SchedulingAgent", "read", "scheduler_api")
        self.ueba.log_action(
            "SchedulingAgent", "read", "telematics_stream",
            meta={"reason": "suspicious cross-access for demo"},
        )

        today = datetime.now().date()
        sla_days = diagnosis_output["sla_days"]

        slots = []
        for d in range(1, 8):
            date = today + timedelta(days=d)
            label_base = date.strftime("%d %b")
            slots.append({"date": date, "slot": f"{label_base} – 09:30 AM"})
            slots.append({"date": date, "slot": f"{label_base} – 01:30 PM"})
            slots.append({"date": date, "slot": f"{label_base} – 05:30 PM"})

        eligible = [s for s in slots if s["date"] <= today + timedelta(days=sla_days)]
        proposed = eligible[0] if eligible else slots[0]

        return {
            "proposed_slot": proposed["slot"],
            "city": city,
            "all_slots": [s["slot"] for s in eligible],
        }

class CustomerEngagementAgent:
    def __init__(self, ueba: UebaMonitor):
        self.ueba = ueba

    def build_voice_script(self, owner_name, make, model, diagnosis_output, schedule_output):
        self.ueba.log_action("CustomerEngagementAgent", "read", "customer_profile")
        self.ueba.log_action("CustomerEngagementAgent", "read", "analysis_results")

        band = diagnosis_output["summary"]
        cost = diagnosis_output["estimated_cost"]
        saving = diagnosis_output["potential_saving"]
        slot = schedule_output["proposed_slot"]
        components = diagnosis_output["components"]

        script = f"""
Hi {owner_name}, this is your virtual service advisor from Hero ✕ Mahindra.

I’ve just completed a health scan of your {make} {model} using the latest telematics
and service history.

• Current health status: {band}
• Likely attention areas: {", ".join(components)}
• Estimated service cost if ignored: around ₹{cost:,}
• You can save almost ₹{saving:,} by fixing this proactively.

I recommend a preventive service visit. I’ve reserved a priority slot for you on
{slot} at your nearest authorised workshop.

Shall I go ahead and confirm this booking for you now?
"""
        return script.strip()

class FeedbackAgent:
    def __init__(self, ueba: UebaMonitor):
        self.ueba = ueba

    def plan_feedback(self, slot):
        self.ueba.log_action("FeedbackAgent", "write", "feedback_db")
        text = f"SMS + in-app survey will be triggered 6 hours after completion of service scheduled at **{slot}**."
        return text

class ManufacturingInsightsAgent:
    def __init__(self, ueba: UebaMonitor):
        self.ueba = ueba

    def insights(self, maint_df: pd.DataFrame):
        self.ueba.log_action("ManufacturingInsightsAgent", "read", "maintenance_db")
        self.ueba.log_action("ManufacturingInsightsAgent", "read", "rca_capa_db")

        grouped = (
            maint_df.groupby("component")
            .agg(
                avg_severity=("severity", "mean"),
                avg_cost=("cost", "mean"),
                count=("component", "count"),
            )
            .reset_index()
            .sort_values("avg_severity", ascending=False)
        )

        top3 = grouped.head(3)
        bullets = []
        for _, row in top3.iterrows():
            comp = row["component"]
            matching = maint_df[maint_df["component"] == comp]
            common_rca = (
                matching["rca_tag"]
                .value_counts()
                .idxmax()
                if not matching.empty
                else "NA"
            )
            sample_capa = (
                matching["capa_action"].iloc[0] if not matching.empty else ""
            )
            bullets.append(
                f"• **{comp}** – Avg severity {row['avg_severity']:.1f}, "
                f"avg cost ₹{row['avg_cost']:.0f} over {int(row['count'])} cases. "
                f"Top RCA: _{common_rca}_. Suggested CAPA: _{sample_capa}_"
            )

        summary = (
            "These patterns are fed back to the manufacturing quality team every week. "
            "Components with rising severity or cost automatically trigger a CAPA ticket and design review."
        )
        return bullets, summary

# ------------------ MASTER ORCHESTRATOR ------------------ #
def master_orchestrate(input_payload):
    ueba = UebaMonitor()
    data_agent = DataAnalysisAgent(ueba)
    diag_agent = DiagnosisAgent(ueba)
    sched_agent = SchedulingAgent(ueba)
    voice_agent_local = CustomerEngagementAgent(ueba)
    fb_agent = FeedbackAgent(ueba)
    mfg_agent = ManufacturingInsightsAgent(ueba)

    analysis_out = data_agent.analyze(input_payload, MAINT_DF)
    diag_out = diag_agent.diagnose(analysis_out)
    sched_out = sched_agent.schedule(input_payload["city"], diag_out)
    voice_script = voice_agent_local.build_voice_script(
        input_payload["owner_name"],
        input_payload["make"],
        input_payload["model"],
        diag_out,
        sched_out,
    )
    fb_plan = fb_agent.plan_feedback(sched_out["proposed_slot"])
    mfg_bullets, mfg_summary = mfg_agent.insights(MAINT_DF)

    return {
        "analysis": analysis_out,
        "diagnosis": diag_out,
        "schedule": sched_out,
        "voice_script": voice_script,
        "feedback_plan": fb_plan,
        "manufacturing": {
            "bullets": mfg_bullets,
            "summary": mfg_summary,
        },
        "ueba": {
            "log": ueba.actions_log,
            "anomalies": ueba.anomalies(),
        },
    }

# ------------------ SESSION METRICS ------------------ #
if "total_analyses" not in st.session_state:
    st.session_state.total_analyses = 156
if "issues_detected" not in st.session_state:
    st.session_state.issues_detected = 24
if "potential_savings" not in st.session_state:
    st.session_state.potential_savings = 1250_00
if "avg_health" not in st.session_state:
    st.session_state.avg_health = 87
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "bookings" not in st.session_state:
    st.session_state.bookings = []
if "ai_history" not in st.session_state:
    st.session_state.ai_history = []
if "last_payload" not in st.session_state:
    st.session_state.last_payload = {}

# ------------------ HEADER ------------------ #
col_logo, col_title, col_status = st.columns([0.6, 2.2, 1])

with col_title:
    st.markdown("### 🚗 AI Car Maintenance Dashboard")
    st.caption("Autonomous Predictive Maintenance • Voice-First Engagement • Manufacturing Feedback Loop")

with col_status:
    st.markdown('<span class="tag-pill tag-online">● System Online</span>', unsafe_allow_html=True)

st.markdown("")

# ------------------ KPI CARDS ------------------ #
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.metric("Total Analyses", st.session_state.total_analyses)
    st.caption("Vehicles monitored so far")
    st.markdown("</div>", unsafe_allow_html=True)

with k2:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.metric("Avg. Health Score", f"{st.session_state.avg_health} / 100")
    st.caption("Fleet-wide rolling index")
    st.markdown("</div>", unsafe_allow_html=True)

with k3:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.metric("Issues Detected", st.session_state.issues_detected)
    st.caption("Early warnings in last 7 days")
    st.markdown("</div>", unsafe_allow_html=True)

with k4:
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    st.metric("Potential Savings (₹)", f"{int(st.session_state.potential_savings/100):,}")
    st.caption("Avoided unplanned repair spend")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# ------------------ MAIN LAYOUT TABS ------------------ #
tab_single, tab_forecast, tab_ueba = st.tabs(
    ["🔍 Analyze Vehicle", "📈 Fleet Demand & RCA", "🛡 UEBA Monitor"]
)

# ---------- TAB 1: SINGLE VEHICLE ANALYSIS ----------
with tab_single:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Analyze Your Vehicle")

    # --------- VEHICLE INPUTS (non-form) to remove Streamlit form hint ----------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        makes = sorted(VEHICLES_DF["make"].unique().tolist())
        make = st.selectbox("Vehicle Make", makes)

    with c2:
        # show models filtered by selected make; allow manual entry
        models_for_make = sorted(VEHICLES_DF[VEHICLES_DF["make"] == make]["model"].unique().tolist())
        models_with_other = models_for_make + ["Other / type manually"]
        selected_model_choice = st.selectbox("Model (choose or type)", models_with_other)
        if selected_model_choice == "Other / type manually":
            model = st.text_input("Model (manual entry)", value="")
        else:
            model = selected_model_choice

    with c3:
        year = st.number_input("Year", min_value=2010, max_value=datetime.now().year, value=2022, step=1)
    with c4:
        mileage = st.number_input("Odometer (km)", min_value=0, max_value=300000, value=45000, step=500)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        engine_temp = st.number_input("Engine Temp (°F)", min_value=150, max_value=260, value=195)
    with c6:
        brake_health = st.slider("Brake Health (%)", 0, 100, 80)
    with c7:
        battery_health = st.slider("Battery Health (%)", 0, 100, 75)
    with c8:
        tyre_pressure = st.number_input("Tyre Pressure (PSI)", min_value=20, max_value=45, value=32)

    c9, c10 = st.columns([1.2, 1])
    with c9:
        owner_name = st.text_input("Owner Name (for voice agent)", "Himani")
    with c10:
        cities = sorted(VEHICLES_DF["city"].unique().tolist())
        city = st.selectbox("City / Service Hub", cities)

    # regular button (not a form submit) — no "please press to submit the form" hint
    analyze_btn = st.button("Analyze Vehicle", key="analyze_vehicle_btn", use_container_width=True)

    if analyze_btn:
        payload = {
            "make": make,
            "model": model if isinstance(model, str) and model.strip() else "Unknown",
            "year": int(year),
            "mileage": int(mileage),
            "engine_temp": engine_temp,
            "brake_health": brake_health,
            "battery_health": battery_health,
            "tyre_pressure": tyre_pressure,
            "owner_name": owner_name if owner_name.strip() else "Owner",
            "city": city,
            # include vehicle_id placeholder to reuse
            "vehicle_id": f"{make[:2].upper()}-{random.randint(100,999)}",
        }
        # save payload so voice flow can reuse it
        st.session_state.last_payload = payload

        result = master_orchestrate(payload)
        st.session_state.last_result = result

        st.session_state.total_analyses += 1
        st.session_state.issues_detected += 1
        st.session_state.potential_savings += result["diagnosis"]["potential_saving"]
        # record assistant reply in chat history
        assistant_reply = f"Analysis done — Risk {result['analysis']['risk_band']}; suggested slot {result['schedule']['proposed_slot']}."
        st.session_state.ai_history.append(("assistant", assistant_reply))
        # speak reply
        if TTS_AVAILABLE:
            voice_agent.speak_async(assistant_reply)
        else:
            st_html(f"<script>const u=new SpeechSynthesisUtterance({json.dumps(assistant_reply)}); u.lang='en-IN'; window.speechSynthesis.speak(u);</script>", height=0)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("")

    # Show results if any
    if st.session_state.last_result:
        res = st.session_state.last_result
        col_left, col_right = st.columns([1.4, 1])

        # ---- LEFT: Technical diagnostics ---- #
        with col_left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("#### 🔧 Predictive Diagnosis")

            risk = res["analysis"]["risk_score"]
            band = res["analysis"]["risk_band"]
            diag = res["diagnosis"]

            band_badge_class = "tag-critical" if band in ["High", "Critical"] else "tag-online"
            st.markdown(
                f'<span class="tag-pill {band_badge_class}">Risk Band: {band}</span>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            st.write(diag["summary"])
            st.write("**Likely attention areas:**")
            for c in diag["components"]:
                st.write(f"- {c}")

            cdiag1, cdiag2, cdiag3 = st.columns(3)
            with cdiag1:
                st.metric("Risk Score", f"{risk:.2f}")
            with cdiag2:
                st.metric("Est. Repair Cost", f"₹{diag['estimated_cost']:,}")
            with cdiag3:
                st.metric("Potential Saving", f"₹{diag['potential_saving']:,}")

            st.markdown("---")
            st.markdown("**Service Slot Reserved (suggested):**")
            st.write(res["schedule"]["proposed_slot"])
            st.caption("Customer can reschedule via app or voice agent.")

            st.markdown("</div>", unsafe_allow_html=True)

        # ---- RIGHT: Voice agent & follow-up (with server-side TTS controls) ---- #
        with col_right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("#### 🗣 Voice Agent Conversation Script")
            st.caption("Exactly what the voice bot will say to the vehicle owner.")
            st.text_area(
                "Script (for demo)",
                value=res["voice_script"],
                height=260,
            )

            st.markdown("---")
            st.markdown("#### 📲 Post-Service Feedback Flow")
            st.write(res["feedback_plan"])
            st.caption("Responses update the vehicle profile and train future prediction models.")

            # TTS playback & booking controls
            st.markdown("---")
            st.markdown("**Agent actions**")

            col_play, col_confirm, col_decline = st.columns([1.2, 1, 1])
            with col_play:
                if st.button("Play Voice Script (server TTS)"):
                    if TTS_AVAILABLE:
                        voice_agent.speak_async(res["voice_script"])
                        st.info("Playing voice script from server (your machine).")
                    else:
                        # fallback to client TTS
                        speak_js = f"<script>const u=new SpeechSynthesisUtterance({json.dumps(res['voice_script'])}); u.lang='en-IN'; u.rate=1; window.speechSynthesis.speak(u);</script>"
                        st_html(speak_js, height=0)
                        st.info("Playing voice from browser (fallback).")

            with col_confirm:
                if st.button("Confirm booking (customer agrees)"):
                    vehicle_id_for_booking = st.session_state.get("last_payload", {}).get("vehicle_id", f"{make[:2].upper()}-{random.randint(100,999)}")
                    booking = sched_agent_simple.book_service(vehicle_id_for_booking, "Proactive service", city=city)
                    st.session_state.bookings.append(booking)
                    st.success(f"Booking confirmed: {booking['slot']}")
                    # speak confirmation
                    reply = f"Booking confirmed for {booking['slot']}. Thank you."
                    if TTS_AVAILABLE:
                        voice_agent.speak_async(reply)
                    else:
                        st_html(f"<script>const u=new SpeechSynthesisUtterance({json.dumps(reply)}); u.lang='en-IN'; window.speechSynthesis.speak(u);</script>", height=0)
                    st.session_state.ai_history.append(("assistant", reply))

            with col_decline:
                if st.button("Decline booking (customer says No)"):
                    st.info("Customer declined the suggested booking. Will retry later.")
                    reply = "Understood. I will remind you again tomorrow."
                    if TTS_AVAILABLE:
                        voice_agent.speak_async(reply)
                    else:
                        st_html(f"<script>const u=new SpeechSynthesisUtterance({json.dumps(reply)}); u.lang='en-IN'; window.speechSynthesis.speak(u);</script>", height=0)
                    st.session_state.ai_history.append(("assistant", reply))

            st.markdown("</div>", unsafe_allow_html=True)

# ---------- TAB 2: FLEET DEMAND & RCA ----------
with tab_forecast:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("Forecasting Service Demand")

    if st.session_state.last_result:
        forecast_df = st.session_state.last_result["analysis"]["forecast"]
    else:
        forecast_df = DataAnalysisAgent(UebaMonitor()).analyze(
            {
                "engine_temp": 195,
                "brake_health": 80,
                "battery_health": 75,
                "tyre_pressure": 32,
                "mileage": 45000,
                "year": 2022,
            },
            MAINT_DF,
        )["forecast"]

    st.line_chart(
        forecast_df.set_index("date")["expected_jobs"],
        height=260,
    )
    st.caption("Expected workshop load over the next 30 days – used by the Scheduling Agent to avoid over-booking.")

    st.markdown("---")
    st.subheader("RCA / CAPA – Manufacturing Feedback Loop")

    mfg_agent_demo = ManufacturingInsightsAgent(UebaMonitor())
    bullets, summary = mfg_agent_demo.insights(MAINT_DF)

    for b in bullets:
        st.markdown(b)

    st.markdown("")
    st.info(summary)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- TAB 3: UEBA MONITOR ----------
with tab_ueba:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("UEBA – Agent Behaviour Monitor")

    if st.session_state.last_result is None:
        st.warning("Run at least one vehicle analysis to populate the UEBA logs.")
    else:
        ueba_info = st.session_state.last_result["ueba"]
        log_df = pd.DataFrame(ueba_info["log"])
        if not log_df.empty:
            log_df_display = log_df[["time", "agent", "action", "resource", "anomaly"]]
            st.dataframe(log_df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No agent activity logged yet.")

        anomalies = ueba_info["anomalies"]
        st.markdown("---")
        st.markdown("#### ⚠️ Anomalies Detected")

        if not anomalies:
            st.success("No abnormal behaviour detected. All agents operating within baseline.")
        else:
            for a in anomalies:
                st.markdown(
                    f"<div class='timeline-row'>"
                    f"🔴 <b>{a['agent']}</b> accessed <code>{a['resource']}</code> at {a['time']} "
                    f"(action: {a['action']}). This is outside its normal access pattern."
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.caption(
                "These events trigger alerts, automatic throttling, or policy review to prevent mis-use of autonomous agents."
            )

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Floating single AI Agent button (talk-only)
# -------------------------
st.markdown("""<div class="fab"><button id="fab_single">🎙 Talk to AI</button></div>""", unsafe_allow_html=True)

# JS overlay: opens voice modal & writes ?voice=... param (so Streamlit can read it)
# Note: auto_listen=true will start recognition immediately when overlay opens.
voice_overlay_js = r"""
<script>
function renderVoiceOverlay() {
  // if overlay exists, show it again
  if (document.getElementById('voice_overlay_box')) {
    document.getElementById('voice_overlay_box').style.display = 'flex';
    // attempt to start listening if supported
    if (window._voice_recog && typeof window._voice_recog.start === 'function') {
      try { window._voice_recog.start(); document.getElementById('voice_start').innerText='Listening...'; } catch(e) {}
    }
    return;
  }

  const overlay = document.createElement('div');
  overlay.id = 'voice_overlay_box';
  overlay.style = 'position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(2,6,23,0.85);z-index:999999;display:flex;align-items:center;justify-content:center;padding:12px;';
  overlay.innerHTML = `
    <div style="width:100%;max-width:720px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:12px;padding:18px;color:white;display:flex;flex-direction:column;gap:10px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="font-weight:800;font-size:18px;">🎙 AutoAI (voice)</div>
        <button id="voice_close_btn" style="background:transparent;border:none;color:white;font-size:18px;">✕</button>
      </div>
      <div style="color:#cbd5e1;font-size:14px;">Speak now — say "analyze vehicle" or "book slot". If your browser doesn't support voice, type the request in the box below.</div>
      <div style="display:flex;gap:8px;">
        <button id="voice_start" style="flex:1;padding:12px;border-radius:10px;background:#10b981;border:none;font-weight:700;">Start Listening</button>
        <button id="voice_stop" style="flex:1;padding:12px;border-radius:10px;background:#374151;border:none;font-weight:700;">Stop</button>
      </div>
      <textarea id="voice_area" rows="4" style="width:100%;border-radius:8px;padding:10px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.04);color:white;"></textarea>
      <div style="display:flex;justify-content:flex-end;gap:8px;">
        <button id="voice_send" style="padding:10px 14px;border-radius:8px;background:#6C63FF;border:none;color:white;font-weight:700;">Send</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  document.getElementById('voice_close_btn').onclick = () => { 
    try { if (window._voice_recog) window._voice_recog.stop(); } catch(e) {}
    overlay.style.display = 'none'; 
  };

  const startBtn = document.getElementById('voice_start');
  const stopBtn = document.getElementById('voice_stop');
  const area = document.getElementById('voice_area');
  const sendBtn = document.getElementById('voice_send');

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  let recog = null;
  if (SpeechRecognition) {
    recog = new SpeechRecognition();
    window._voice_recog = recog; // expose for later control
    recog.lang = 'en-IN';
    recog.interimResults = true;
    recog.continuous = true;
    recog.onresult = (ev) => {
      let transcript = '';
      for (let i=ev.resultIndex;i<ev.results.length;i++){
        transcript += ev.results[i][0].transcript;
      }
      area.value = transcript;
    };
    recog.onerror = (e) => { console.warn('recog err', e); };
    // start automatically
    try { recog.start(); startBtn.innerText = 'Listening...'; } catch(e) {}
  } else {
    startBtn.disabled = true;
    startBtn.innerText = 'Voice not supported';
  }

  startBtn.onclick = () => {
    if (recog) { area.value = ''; try { recog.start(); startBtn.innerText='Listening...'; } catch(e) {} }
    else { area.focus(); }
  };
  stopBtn.onclick = () => {
    if (recog) { try { recog.stop(); startBtn.innerText='Start Listening'; } catch(e) {} }
  };

  sendBtn.onclick = () => {
    const t = area.value || '';
    if (!t.trim()) { alert('Please speak or type a request.'); return; }
    const encoded = encodeURIComponent(t);
    const ts = Date.now();
    const newUrl = window.location.origin + window.location.pathname + '?voice=' + encoded + '&ts=' + ts;
    // use replaceState so browser back doesn't spam
    window.history.replaceState(null, '', newUrl);
    // reload the page so Streamlit picks up query param
    window.location.reload();
  };
}

// bind after a short delay (Streamlit may re-render)
setTimeout(() => {
  const btn = document.getElementById('fab_single');
  if (btn) btn.onclick = renderVoiceOverlay;
}, 600);
</script>
"""
st_html(voice_overlay_js, height=0)

# -------------------------
# Read query params to get voice text (if any)
# -------------------------
# Use the stable API st.query_params and st.set_query_params
params = st.query_params
if "voice" in params:
    raw_voice = params.get("voice", [""])[0]
    # remove query params now so clicking again won't reuse
    try:
        # clear query params (stable API)
        st.set_query_params()
    except Exception:
        # older Streamlit may not support set_query_params; ignore if fails
        pass
    voice_text = raw_voice.strip()
    if voice_text:
        st.session_state.ai_history.append(("user", voice_text))
        qlow = voice_text.lower()

        # Basic NLU routing
        if any(k in qlow for k in ["analyze", "scan", "diagnos", "health", "check"]):
            # use saved payload if present, else fall back to defaults
            payload = st.session_state.get("last_payload", {
                "make": "Mahindra",
                "model": "XUV700",
                "year": 2022,
                "mileage": 45000,
                "engine_temp": 195,
                "brake_health": 80,
                "battery_health": 75,
                "tyre_pressure": 32,
                "owner_name": "Owner",
                "city": "Mumbai",
                "vehicle_id": "V001"
            })
            # ensure numeric types
            try:
                payload["year"] = int(payload.get("year", 2022))
                payload["mileage"] = int(payload.get("mileage", 45000))
            except Exception:
                pass

            res = master_orchestrate(payload)
            st.session_state.last_result = res
            st.session_state.total_analyses += 1
            st.session_state.issues_detected += 1
            st.session_state.potential_savings += res["diagnosis"]["potential_saving"]

            reply = f"Analysis completed. Risk: {res['analysis']['risk_band']}. Suggested slot: {res['schedule']['proposed_slot']}."
            st.session_state.ai_history.append(("assistant", reply))

            # speak
            if TTS_AVAILABLE:
                voice_agent.speak_async(reply)
            else:
                speak_js = f"<script>const u=new SpeechSynthesisUtterance({json.dumps(reply)}); u.lang='en-IN'; window.speechSynthesis.speak(u);</script>"
                st_html(speak_js, height=0)

        elif any(k in qlow for k in ["book", "slot", "schedule", "appointment", "confirm"]):
            # book demo slot
            vehicle_id = st.session_state.get("last_payload", {}).get("vehicle_id", "V001")
            booking = sched_agent_simple.book_service(vehicle_id, "Proactive service", city="Mumbai")
            st.session_state.bookings.append(booking)
            reply = f"Booked {booking['slot']} for {booking['vehicle_id']}."
            st.session_state.ai_history.append(("assistant", reply))
            if TTS_AVAILABLE:
                voice_agent.speak_async(reply)
            else:
                st_html(f"<script>const u=new SpeechSynthesisUtterance({json.dumps(reply)}); u.lang='en-IN'; window.speechSynthesis.speak(u);</script>", height=0)
        else:
            reply = "Demo assistant supports: 'analyze vehicle' and 'book slot'. Try one of those."
            st.session_state.ai_history.append(("assistant", reply))
            if TTS_AVAILABLE:
                voice_agent.speak_async(reply)
            else:
                st_html(f"<script>const u=new SpeechSynthesisUtterance({json.dumps(reply)}); u.lang='en-IN'; window.speechSynthesis.speak(u);</script>", height=0)

# -------------------------
# Chat / conversation UI (text)
# -------------------------
st.markdown("---")
st.markdown("### 💬 Assistant Chat")
st.write("You can also chat here. The assistant will respond and speak the reply.")

with st.container():
    # show last 12 messages
    for role, txt in st.session_state.ai_history[-12:]:
        if role == "user":
            st.markdown(f"<div class='user-bubble'><b>You:</b> {txt}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='assistant-bubble'><b>Assistant:</b> {txt}</div>", unsafe_allow_html=True)

    user_msg = st.text_input("Message", key="chat_input")
    if st.button("Send Message"):
        if user_msg and user_msg.strip():
            st.session_state.ai_history.append(("user", user_msg))
            q = user_msg.lower().strip()

            # simple intent responses
            if any(k in q for k in ["analyze", "scan", "diagnos", "health", "check"]):
                payload = st.session_state.get("last_payload", {
                    "make": "Mahindra",
                    "model": "XUV700",
                    "year": 2022,
                    "mileage": 45000,
                    "engine_temp": 195,
                    "brake_health": 80,
                    "battery_health": 75,
                    "tyre_pressure": 32,
                    "owner_name": "Owner",
                    "city": "Mumbai",
                    "vehicle_id": "V001"
                })
                res = master_orchestrate(payload)
                st.session_state.last_result = res
                st.session_state.total_analyses += 1
                st.session_state.issues_detected += 1
                st.session_state.potential_savings += res["diagnosis"]["potential_saving"]
                reply = f"Analysis completed. Risk: {res['analysis']['risk_band']}. Suggested slot: {res['schedule']['proposed_slot']}."
            elif any(k in q for k in ["book", "slot", "schedule", "appointment", "confirm"]):
                vehicle_id = st.session_state.get("last_payload", {}).get("vehicle_id", "V001")
                booking = sched_agent_simple.book_service(vehicle_id, "Proactive service", city="Mumbai")
                st.session_state.bookings.append(booking)
                reply = f"Booked {booking['slot']} for {booking['vehicle_id']}."
            elif any(k in q for k in ["yes", "ok", "confirm"]):
                if st.session_state.last_result:
                    slot = st.session_state.last_result["schedule"]["proposed_slot"]
                    booking = sched_agent_simple.book_service("V001", "Proactive service", city="Mumbai")
                    st.session_state.bookings.append(booking)
                    reply = f"Confirmed booking for {slot}."
                else:
                    reply = "I don't have an active analysis to confirm. Ask me to 'analyze vehicle' first."
            else:
                reply = "I can analyze your vehicle, book slots, or explain findings. Try: 'analyze vehicle' or 'book slot'."

            st.session_state.ai_history.append(("assistant", reply))
            # speak the reply
            if TTS_AVAILABLE:
                voice_agent.speak_async(reply)
            else:
                st_html(f"<script>const u=new SpeechSynthesisUtterance({json.dumps(reply)}); u.lang='en-IN'; window.speechSynthesis.speak(u);</script>", height=0)

            # safe rerun helper (compat across streamlit versions)
            def safe_rerun():
                try:
                    if hasattr(st, "experimental_rerun"):
                        st.experimental_rerun()
                        return
                except Exception:
                    pass
                try:
                    if hasattr(st, "experimental_request_rerun"):
                        st.experimental_request_rerun()
                        return
                except Exception:
                    pass
                # no rerun available: rely on session_state changes to show updates

            safe_rerun()

# ------------------ FOOTER & BOOKINGS ------------------ #
st.markdown("---")
st.caption(
    "© 2025 Autonomous Predictive Maintenance • Hero ✕ Mahindra • Demo built for EY Techathon – Agentic AI + UEBA"
)

# Sidebar bookings
if st.session_state.bookings:
    st.sidebar.markdown("### 📅 Recent Bookings (demo)")
    # bookings returned by sched_agent_simple use 'slot'
    for b in reversed(st.session_state.bookings[-6:]):
        slot_text = b.get("slot") or b.get("proposed_slot") or ""
        st.sidebar.write(f"{b.get('vehicle_id','-')} • {slot_text} • {b.get('issue','-')}")
else:
    st.sidebar.info("No bookings yet (demo)")
