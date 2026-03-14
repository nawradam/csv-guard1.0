# agents/analyst_agent.py

import vertexai
from vertexai.generative_models import GenerativeModel

class AnalystAgent:
    def __init__(self, project_id):
        vertexai.init(project=project_id, location="us-central1")
        # Use the current stable model
        self.model = GenerativeModel("gemini-2.5-flash")

    def analyze(self, csv_content):
        prompt = f"""
        You are a Data Auditor. Analyze this CSV data for anomalies:
        {csv_content}

        List 3 key insights or suspicious rows. Keep it brief.
        """
        response = self.model.generate_content(prompt)
        return response.text