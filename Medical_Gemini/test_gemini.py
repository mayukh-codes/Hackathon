import os
from dotenv import load_dotenv
from google import genai

# Load .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY missing in .env")
    exit()

# Create Gemini client
client = genai.Client(api_key=API_KEY)

print("✅ Gemini AI Ready (Type 'exit' to stop)\n")

while True:
    query = input("🧑‍⚕️ Ask Medical AI: ")

    if query.lower() in ["exit", "quit"]:
        print("👋 Exiting AI test")
        break

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query
        )

        print("\n🤖 Gemini Response:")
        print(response.text)
        print("-" * 50)

    except Exception as e:
        print("\n❌ API Error:", e)
