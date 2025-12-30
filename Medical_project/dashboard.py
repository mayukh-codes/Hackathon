import streamlit as st
import pandas as pd
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Smart Patient Monitoring", layout="wide")

# ---------------- AUTO REFRESH ----------------
st_autorefresh(interval=1000, key="refresh")

# ---------------- SESSION STATE ----------------
if "patients" not in st.session_state:
    st.session_state.patients = {}
if "current_patient" not in st.session_state:
    st.session_state.current_patient = None

# ---------------- SIDEBAR : PATIENT SELECTION ----------------
st.sidebar.title("🧑‍⚕️ Patient Section")
action = st.sidebar.radio("Choose:", ["New Patient", "Existing Patient"])

if action == "New Patient":
    pid = st.sidebar.text_input("Patient ID")
    name = st.sidebar.text_input("Name")
    age = st.sidebar.number_input("Age", 0, 120, 25)
    gender = st.sidebar.selectbox("Gender", ["Male", "Female", "Other"])

    if st.sidebar.button("Add Patient"):
        if pid not in st.session_state.patients:
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
            st.sidebar.warning("Patient ID exists")

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

# ---------------- MAIN DASHBOARD ----------------
if st.session_state.current_patient:

    patient = st.session_state.patients[st.session_state.current_patient]

    st.title(f"🏥 Dashboard - {patient['name']}")
    st.caption(f"Age: {patient['age']} | Gender: {patient['gender']}")

    # ---------------- GENERATE VITALS ----------------
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

    # ---------------- ALERT LOGIC (Vitals AI) ----------------
    def get_alert(data):
        if len(data) < 7:
            return "GREEN"
        if all(v["HR"] > 110 or v["SpO2"] < 90 or v["BP"] > 140 or v["Temp"] > 38 for v in data[-7:]):
            return "RED"
        if all(v["HR"] > 100 or v["SpO2"] < 94 or v["BP"] > 130 or v["Temp"] > 37.5 for v in data[-7:]):
            return "YELLOW"
        return "GREEN"

    alert = get_alert(patient["last_10"])

    # ---------------- LAYOUT ----------------
    left, right = st.columns([3, 1])

    # ================= LEFT SIDE =================
    with left:
        if alert == "GREEN":
            st.success("🟢 Patient Stable")
        elif alert == "YELLOW":
            st.warning("🟡 Minor Fluctuation")
        else:
            st.error("🔴 CRITICAL CONDITION")

        df = pd.DataFrame(patient["vitals"])

        st.subheader("📊 Live Vitals (2 Graphs per Row)")

        # -------- ROW 1 --------
        g1, g2 = st.columns(2)
        with g1:
            st.markdown("**Heart Rate (BPM)**")
            st.line_chart(df["HR"])
        with g2:
            st.markdown("**SpO₂ (%)**")
            st.line_chart(df["SpO2"])

        # -------- ROW 2 --------
        g3, g4 = st.columns(2)
        with g3:
            st.markdown("**Blood Pressure**")
            st.line_chart(df["BP"])
        with g4:
            st.markdown("**Temperature (°C)**")
            st.line_chart(df["Temp"])

        st.subheader("⏱ Per-Minute Average")
        avg = df[["HR", "SpO2", "BP", "Temp"]].tail(60).mean()
        st.write(avg.round(2))

        # -------- AI–1 : CAREGIVER GUIDANCE --------
        st.markdown("## 🚑 AI Caregiver Guidance")
        if alert == "RED":
            st.error("""
            • Keep patient upright  
            • Clear airway  
            • Loosen tight clothing  
            • Call doctor immediately  
            """)
        elif alert == "YELLOW":
            st.warning("""
            • Observe patient closely  
            • Recheck vitals  
            """)
        else:
            st.success("Patient stable, no action required")

    # ================= RIGHT SIDE : CHAT AI =================
    with right:
        st.markdown("## 🤖 AI Chat Assistant")
        st.caption("Internet-based medical & system queries")

        query = st.text_area(
            "Ask AI",
            placeholder="Eg: BP high hone par kya kare?",
            height=140
        )

        if st.button("Ask AI"):
            if query.strip() != "":
                st.info("Fetching response from AI...")
                
                # ---------------- OpenRouter AI Integration ----------------
                import requests
                import os
                from dotenv import load_dotenv

                load_dotenv()
                OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

                def query_openrouter(prompt):
                    url = "https://openrouter.ai/api/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    }
                    data = {
                        "model": "meta-llama/llama-3.2-3b-instruct:free",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                    try:
                        response = requests.post(url, headers=headers, json=data)
                        resp_json = response.json()
                        return resp_json["choices"][0]["message"]["content"]
                    except:
                        return "AI API failed or quota exceeded. Follow standard protocol."

                answer = query_openrouter(query)
                st.write(answer)
            else:
                st.warning("Please enter a query first.")

        st.markdown("---")
        st.caption("This AI is independent from vitals monitoring AI")


else:
    st.info("👈 Please add or select a patient")
