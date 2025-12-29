import express from "express";
import cors from "cors";
import fetch from "node-fetch";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 5000;

// 🔹 ROOT ROUTE (TEST)
app.get("/", (req, res) => {
  res.send("✅ Gemini backend is running");
});

// 🔹 AI ROUTE
app.post("/ask-ai", async (req, res) => {
  try {
    const { query } = req.body;

    if (!query) {
      return res.status(400).json({ error: "Query missing" });
    }

    // Gemini API call
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${process.env.GEMINI_API_KEY}`
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                {
                  text: `You are a medical assistant. Answer shortly in Hinglish.\nUser: ${query}\nAnswer:`
                }
              ]
            }
          ],
          temperature: 0.5,
          maxOutputTokens: 300
        })
      }
    );

    const data = await response.json();

    const reply =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      "No response from Gemini";

    res.json({ reply });

  } catch (err) {
    console.error("Gemini API Error:", err);
    res.status(500).json({ error: "Gemini API failed" });
  }
});

app.listen(PORT, () => {
  console.log(`✅ Gemini backend running on port ${PORT}`);
});
