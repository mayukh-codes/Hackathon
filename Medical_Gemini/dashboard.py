import streamlit as st
import pandas as pd
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import requests
import os
from dotenv import load_dotenv

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Smart Patient Monitoring",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= ENV =================
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ================= SESSION STATE =================
if "patients" not in st.session_state:
    st.session_state.patients = {}

if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

if "pause_refresh" not in st.session_state:
    st.session_state.pause_refresh = False

if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""

# ================= AUTO REFRESH =================
if not st.session_state.pause_refresh:
    st_autorefresh(interval=2500, key="refresh")

# ================= SIDEBAR =================
st.sidebar.title("🧑‍⚕️ Patient Control")

mode = st.sidebar.radio("Mode", ["➕ New Patient", "📂 Existing Patient"])

if mode == "➕ New Patient":
    pid = st.sidebar.text_input("Patient ID")
    name = st.sidebar.text_input("Name")
    age = st.sidebar.number_input("Age", 0, 120, 30)
    gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Other"])

    if st.sidebar.button("Add Patient"):
        if pid and pid not in st.session_state.patients:
            st.session_state.patients[pid] = {
                "name": name,
                "age": age,
                "gender": gender,
                "vitals": [],
                "last_10": []
            }
            st.session_state.current_patient = pid
            st.sidebar.success("✅ Patient Added")
        else:
            st.sidebar.error("❌ Invalid / Duplicate ID")

else:
    if st.session_state.patients:
        pid = st.sidebar.selectbox("Select Patient", st.session_state.patients.keys())
        if st.sidebar.button("Load Patient"):
            st.session_state.current_patient = pid
    else:
        st.sidebar.info("No patients available")

# ================= DASHBOARD =================
if st.session_state.current_patient:

    patient = st.session_state.patients[st.session_state.current_patient]

    st.title(f"🏥 Patient Dashboard — {patient['name']}")
    st.caption(f"Age: {patient['age']} | Gender: {patient['gender']}")

    # -------- Generate Vitals --------
    def generate_vitals():
        return {
            "time": datetime.now(),
            "HR": random.randint(60, 120),
            "SpO2": random.randint(85, 99),
            "BP": random.randint(90, 150),
            "Temp": round(random.uniform(36, 39), 1)
        }

    vital = generate_vitals()
    patient["vitals"].append(vital)
    patient["last_10"].append(vital)

    if len(patient["last_10"]) > 10:
        patient["last_10"].pop(0)
    if len(patient["vitals"]) > 300:
        patient["vitals"].pop(0)

    # -------- Alert Logic --------
    def get_alert(data):
        if len(data) < 7:
            return "GREEN"
        if all(v["HR"] > 110 or v["SpO2"] < 90 or v["BP"] > 140 or v["Temp"] > 38 for v in data[-7:]):
            return "RED"
        if all(v["HR"] > 100 or v["SpO2"] < 94 or v["BP"] > 130 or v["Temp"] > 37.5 for v in data[-7:]):
            return "YELLOW"
        return "GREEN"

    alert = get_alert(patient["last_10"])

    # ================= DATA =================
    df = pd.DataFrame(patient["vitals"])
    df["time"] = pd.to_datetime(df["time"])

    # ===== PER-MINUTE AVERAGE TABLE =====
    df["minute"] = df["time"].dt.floor("T")
    minute_avg_df = (
        df.groupby("minute")[["HR", "SpO2", "BP", "Temp"]]
        .mean()
        .round(2)
        .reset_index()
    )

    left, right = st.columns([3.5, 1.5])

    # ================= LEFT =================
    with left:

        # -------- STATUS --------
        if alert == "GREEN":
            st.success("🟢 Patient Stable")
        elif alert == "YELLOW":
            st.warning("🟡 Needs Observation")
        else:
            st.error("🔴 Critical Condition")

        # -------- METRICS --------
        latest = df.iloc[-1]
        m1, m2, m3, m4 = st.columns(4)

        m1.metric("❤️ Heart Rate", f"{latest['HR']} bpm")
        m2.metric("🫁 SpO₂", f"{latest['SpO2']} %")
        m3.metric("🩸 BP", f"{latest['BP']} mmHg")
        m4.metric("🌡 Temp", f"{latest['Temp']} °C")

        st.markdown("### 📊 Live Vitals (Raw Data)")

        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.line_chart(df, y="HR")
        with r1c2:
            st.line_chart(df, y="SpO2")

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.line_chart(df, y="BP")
        with r2c2:
            st.line_chart(df, y="Temp")

        # ===== TABLE ONLY (NO GRAPH) =====
        st.markdown("### ⏱️ Per-Minute Average Vitals (Table)")
        st.dataframe(
            minute_avg_df.tail(10),
            use_container_width=True
        )

        st.markdown("### 🚑 Caregiver Guidance")
        if alert == "RED":
            st.error("Immediate doctor call. Oxygen & airway ensure karo.")
        elif alert == "YELLOW":
            st.warning("Close monitoring & recheck vitals.")
        else:
            st.success("No action needed.")

    # ================= RIGHT : AI =================
    with right:
        st.markdown("## 🤖 AI Assistant")

        query = st.text_area(
            "Ask medical query",
            placeholder="Eg: SpO2 88 ho toh kya kare?",
            height=120
        )

        if st.button("Ask AI"):
            if not OPENROUTER_API_KEY:
                st.error("API key missing")
            elif not query.strip():
                st.warning("Question likho")
            else:
                st.session_state.pause_refresh = True
                st.session_state.ai_response = ""

                with st.spinner("AI soch raha hai..."):
                    try:
                        res = requests.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": "mistralai/mistral-7b-instruct:free",
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": "You are a medical assistant. Answer shortly in Hinglish."
                                    },
                                    {"role": "user", "content": query}
                                ],
                                "temperature": 0.5
                            },
                            timeout=30
                        )

                        if res.status_code == 200:
                            st.session_state.ai_response = res.json()["choices"][0]["message"]["content"]
                        else:
                            st.session_state.ai_response = "AI busy / quota issue."

                    except:
                        st.session_state.ai_response = "AI service unavailable."

                st.session_state.pause_refresh = False

        if st.session_state.ai_response:
            st.markdown("### 🧠 AI Response")
            st.write(st.session_state.ai_response)

else:
    st.info("👈 Sidebar se patient add / select karo")
