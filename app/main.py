# app/main.py

import pandas as pd
from flask import Flask, render_template, request, session, redirect, url_for
from guardian_agent import GuardianAgent
from analyst_agent import AnalystAgent
from flask_session import Session

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

PROJECT_ID = "mythic-ego-490214-m3"

guardian = GuardianAgent(PROJECT_ID)
analyst = AnalystAgent(PROJECT_ID)

@app.route("/", methods=["GET", "POST"])
def index():
    if "chat" not in session:
        session["chat"] = []
    if "csv_text" not in session:
        session["csv_text"] = None
    if "csv_safe" not in session:
        session["csv_safe"] = False

    logs = []
    result = None
    question_allowed = False

    # --- CSV Upload ---
    if "upload_csv" in request.form:
        file = request.files.get("csv_file")
        if file:
            try:
                df = pd.read_csv(file)
                csv_text = df.to_string()
                session["csv_text"] = csv_text
                logs.append("[System] CSV uploaded successfully.")

                # Guardian check for safety
                logs.append("[Guardian] Checking CSV for malicious patterns...")
                if guardian.inspect(csv_text) == "MATCH":
                    session["csv_safe"] = False
                    result = "❌ This CSV is unsafe! You cannot ask questions."
                    logs.append("[Guardian] Security violation detected!")
                else:
                    session["csv_safe"] = True
                    result = "✅ CSV is safe. You can now ask questions."
                    logs.append("[Guardian] CSV passed safety check.")
                    question_allowed = True
                    session["chat"] = []  # reset chat for new CSV
            except Exception as e:
                result = f"⚠️ Error reading CSV: {str(e)}"
                logs.append(f"[Error] {str(e)}")
                session["csv_text"] = None
                session["csv_safe"] = False

    # --- User Question / AI Chat ---
    elif "ask_question" in request.form:
        user_question = request.form.get("user_question", "").strip()
        if session["csv_safe"] and session["csv_text"]:
            if user_question:
                session["chat"].append({"role": "user", "message": user_question})
                logs.append("[Analyst] Generating AI response...")

                try:
                    raw_analysis = analyst.analyze(f"{session['csv_text']}\n\nUser question: {user_question}")
                    # Check AI output safety
                    if guardian.inspect(raw_analysis) == "MATCH":
                        ai_message = "⚠️ AI response contained unsafe content and was redacted."
                        logs.append("[Guardian] AI output blocked due to unsafe content.")
                    else:
                        ai_message = raw_analysis
                        logs.append("[Analyst] AI response generated safely.")

                    session["chat"].append({"role": "ai", "message": ai_message})
                    result = ai_message
                    question_allowed = True
                except Exception as e:
                    result = f"⚠️ AI analysis failed: {str(e)}"
                    logs.append(f"[Error] {str(e)}")
            else:
                result = "❌ Please enter a question."
                question_allowed = True
        else:
            result = "❌ CSV not uploaded or unsafe. Upload a safe CSV first."
            question_allowed = False

    # Enable question box only if CSV is safe
    if session.get("csv_safe"):
        question_allowed = True

    return render_template(
        "index.html",
        logs=logs,
        result=result,
        question_allowed=question_allowed,
        chat=session.get("chat", [])
    )

@app.route("/reset")
def reset_session():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)