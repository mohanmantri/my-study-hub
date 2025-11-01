import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai  # <-- The correct, original library

# -----------------------------
# 1) ADD YOUR API KEY HERE
# -----------------------------
GEMINI_API_KEY = os.environ.get("AIzaSyBtFykIc38p2XBESPdPijxaZ5D036heZEU") # <-- PASTE YOUR KEY HERE
if not GEMINI_API_KEY or GEMINI_API_KEY == "Your Api Key":
    raise RuntimeError("Put your real Gemini API key in GEMINI_API_KEY.")

# Configure the library with your key
genai.configure(api_key=GEMINI_API_KEY)

# Model
# We use "gemini-pro" which is a stable model that works
# even with the old v1beta API error you are seeing.
MODEL_NAME = "gemini-2.5-flash-lite"

# -----------------------------
# 2) PROMPTS FOR THE STUDY HUB
# -----------------------------
STUDY_PROMPTS = {
    "summarize_notes": {
        "instruction": (
            "You are an expert academic summarizer. "
            "Analyze the following text and provide a concise, bullet-pointed summary "
            "of the key concepts, definitions, and main ideas. "
            "Omit any trivial or conversational parts."
        ),
        "mime_type": "text/plain",
        "temperature": 0.3
    },
    
    "explain_concept": {
        "instruction": (
            "You are a friendly and patient tutor. The user will provide text, "
            "but they really just want you to explain the *main concept* from that text. "
            "Identify the core topic and explain it in a simple, step-by-step way, "
            "using an analogy if possible. "
            "Start with 'Here's a simple breakdown of [Concept]...'"
        ),
        "mime_type": "text/plain",
        "temperature": 0.7
    },
    
    "generate_quiz": {
        "instruction": (
            "You are a helpful quiz generator. Based on the following text, "
            "create a set of 5 multiple-choice questions. "
            "Respond ONLY with a valid JSON array. "
            "Each object in the array must have three keys: "
            "'question' (a string), "
            "'options' (a list of 4 strings), "
            "and 'answer' (the correct string from the options list)."
        ),
        "mime_type": "application/json",
        "temperature": 0.5
    }
}

app = Flask(__name__, template_folder="templates")

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/study")
def study_endpoint():
    data = request.get_json(force=True) or {}
    input_text = (data.get("text") or "").strip()
    mode = (data.get("mode") or "summarize_notes").lower()

    if not input_text:
        return jsonify({"error": "No text provided"}), 400
    if mode not in STUDY_PROMPTS:
        return jsonify({"error": "Invalid mode"}), 400

    profile = STUDY_PROMPTS[mode]
    
    # This is the prompt we send to the model
    full_prompt = f"{profile['instruction']}\n\n--- TEXT TO ANALYZE ---\n\n{input_text}"

    try:
        # This is the correct, simple way to do it.
        
        # 1. Set up generation config as a dictionary
        generation_config = {
            "temperature": profile["temperature"],
            "max_output_tokens": 2048,
            "response_mime_type": profile["mime_type"]
        }
        
        # 2. Create the model instance
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config=generation_config
        )

        # 3. Generate the content
        resp = model.generate_content(full_prompt)
        
        # 4. Get the text
        text = resp.text or "(No response)"
        return jsonify({"reply": text, "mode": mode})

    except Exception as e:
        error_message = str(e)
        if "API_KEY_INVALID" in error_message:
            error_message = "Your API Key is invalid. Please check it in app.py."
        return jsonify({"error": f"Error from API: {error_message}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)