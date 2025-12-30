import streamlit as st
import pandas as pd
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import requests
import os
from dotenv import load_dotenv

# ================= PAGE CONFIG =================
st.set_page_config(page_title="Smart Patient Monitoring", layout="wide")

# ================= ENV =================
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# ================= SESSION STATE INIT =================
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
    st_autorefresh(interval=2000, key="refresh")

# ================= SIDEBAR =================
st.sidebar.title("🧑‍⚕️ Patient Section")
action = st.sidebar.radio("Choose:", ["New Patient", "Existing Patient"])

if action == "New Patient":
    pid = st.sidebar.text_input("Patient ID")
    name = st.sidebar.text_input("Name")
    age = st.sidebar.number_input("Age", 0, 120, 25)
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
            st.sidebar.success("Patient Added")
        else:
            st.sidebar.warning("Invalid / Duplicate Patient ID")

else:
    if st.session_state.patients:
        pid = st.sidebar.selectbox(
            "Select Patient",
            list(st.session_state.patients.keys())
        )
        if st.sidebar.button("Load Patient"):
            st.session_state.current_patient = pid
    else:
        st.sidebar.info("No patients found")

# ================= DASHBOARD =================
if st.session_state.current_patient:

    patient = st.session_state.patients[st.session_state.current_patient]

    st.title(f"🏥 Dashboard - {patient['name']}")
    st.caption(f"Age: {patient['age']} | Gender: {patient['gender']}")

    # ---------- Generate vitals ----------
    def generate_vitals():
        return {
            "timestamp": datetime.now(),
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

    # ---------- Alert Logic ----------
    def get_alert(data):
        if len(data) < 7:
            return "GREEN"
        if all(v["HR"] > 110 or v["SpO2"] < 90 or v["BP"] > 140 or v["Temp"] > 38 for v in data[-7:]):
            return "RED"
        if all(v["HR"] > 100 or v["SpO2"] < 94 or v["BP"] > 130 or v["Temp"] > 37.5 for v in data[-7:]):
            return "YELLOW"
        return "GREEN"

    alert = get_alert(patient["last_10"])

    left, right = st.columns([3, 1])

    # ================= LEFT =================
    with left:
        if alert == "GREEN":
            st.success("🟢 Patient Stable")
        elif alert == "YELLOW":
            st.warning("🟡 Minor Fluctuation")
        else:
            st.error("🔴 CRITICAL CONDITION")

        df = pd.DataFrame(patient["vitals"])

        st.subheader("📊 Live Vitals (2 Graphs / Row)")

        g1, g2 = st.columns(2)
        with g1:
            st.line_chart(df["HR"])
        with g2:
            st.line_chart(df["SpO2"])

        g3, g4 = st.columns(2)
        with g3:
            st.line_chart(df["BP"])
        with g4:
            st.line_chart(df["Temp"])

        st.subheader("🚑 AI Caregiver Guidance")
        if alert == "RED":
            st.error("Doctor ko turant call karo. Oxygen & airway clear rakho.")
        elif alert == "YELLOW":
            st.warning("Patient observe karo, vitals recheck karo.")
        else:
            st.success("Patient stable hai.")

    # ================= RIGHT : AI CHAT =================
    with right:
        st.markdown("## 🤖 AI Chat Assistant")

        query = st.text_area(
            "Ask AI",
            placeholder="Eg: BP high ho toh kya kare?",
            height=130
        )

        if st.button("Ask AI"):
            if not OPENROUTER_API_KEY:
                st.error("OPENROUTER_API_KEY missing")
            elif query.strip() == "":
                st.warning("Question likho pehle")
            else:
                st.session_state.pause_refresh = True
                st.session_state.ai_response = ""

                with st.spinner("AI soch raha hai..."):
                    try:
                        response = requests.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "http://localhost:8501",
                                "X-Title": "Smart Patient Monitoring"
                            },
                            json={
                                "model": "mistralai/mistral-7b-instruct:free",
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": "You are a medical assistant. Answer briefly in simple Hinglish."
                                    },
                                    {"role": "user", "content": query}
                                ],
                                "temperature": 0.6
                            },
                            timeout=30
                        )

                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.ai_response = data["choices"][0]["message"]["content"]
                        else:
                            st.session_state.ai_response = "AI busy / free quota exhausted."

                    except Exception:
                        st.session_state.ai_response = "AI service unavailable."

                st.session_state.pause_refresh = False

        if st.session_state.ai_response:
            st.markdown("### 🧠 AI Response")
            st.write(st.session_state.ai_response)

else:
    st.info("👈 Pehle patient add ya select karo")
