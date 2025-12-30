import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    print("❌ OPENROUTER_API_KEY not found")
    exit()

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost",
    "X-Title": "Hackathon Medical AI"
}

data = {
    "model": "mistralai/mistral-7b-instruct:free",
    "messages": [
        {
            "role": "system",
            "content": "You are a medical emergency assistant."
        },
        {
            "role": "user",
            "content": "If a patient's oxygen level is 88%, what immediate steps should be taken?"
        }
    ],
    "temperature": 0.6,
    "max_tokens": 200
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)

    print("\n🔎 Raw Status Code:", response.status_code)

    resp = response.json()

    print("\n🔎 Raw JSON Response:\n")
    print(json.dumps(resp, indent=2))

    if response.status_code == 200:
        try:
            content = resp["choices"][0]["message"]["content"]
            if content.strip() == "":
                raise Exception("Empty content")
            print("\n✅ AI Response:\n")
            print(content)
        except:
            print("\n⚠️ AI returned empty message.")
            print("Fallback Response:")
            print(
                "• Place patient upright\n"
                "• Ensure airway is clear\n"
                "• Provide oxygen if available\n"
                "• Call doctor immediately"
            )
    else:
        print("\n❌ API Error")

except Exception as e:
    print("\n❌ Request Failed:", e)
