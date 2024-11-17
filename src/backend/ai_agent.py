# backend/ai_agent.py

import openai
import os
import time
import re
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class AI_Agent:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.valid_actions = ["WAIT", "GRASP", "ROTATE", "RELEASE", "ROTATE_BACK"]

    def process_external_prompt(self, prompt):
        # Example: Direct mapping or use AI to interpret
        action = prompt.upper().strip()
        if action in self.valid_actions:
            return action
        else:
            # Default action or use AI to determine
            return "WAIT"
