"""
AI Service: The 'Socratic' Tutor Brain.
Handles interactions with LLMs (OpenAI/Gemini) with strict pedagogical guardrails.
"""
import os
import httpx
from typing import List, Dict, Optional
from pydantic import BaseModel

# Configuration (In production, load from env)
# AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
# AI_API_KEY = os.getenv("AI_API_KEY", "")

# Strict Socratic System Prompt
SOCRATIC_SYSTEM_PROMPT = """
You are a Socratic Tutor for a K-11 School in Uzbekistan.
Your Goal: Help the student understand the concept/method, but NEVER give the final answer.

STRICT RULES:
1. REFUSE to solve math problems directly. Instead, ask: "What do you think is the first step?"
2. If looking at code, point out the line of error but do not write the fix. say: "Check line X, look at the indent."
3. If asked for an essay, provide an outline or bullet points, NOT the full text.
4. Keep responses short (under 3 sentences) to encourage dialogue.
5. Be encouraging but firm about the "No Cheating" policy.
6. Use emojis occasionally (📚, ✨, 🤔).

Current Student Context:
- Grade: {grade}
- Subject: {subject}
"""

class ChatMessage(BaseModel):
    role: str # "user" or "system" or "assistant"
    content: str

class AIService:
    def __init__(self, api_key: str = "mock-key"):
        self.api_key = api_key
        # self.client = ... (Initialize OpenAI client here)

    async def get_tutor_response(
        self, 
        history: List[ChatMessage], 
        student_grade: int, 
        subject_name: str
    ) -> str:
        """
        Get a response from the AI Tutor with Socratic guardrails.
        """
        # 1. Construct System Prompt with Context
        sys_prompt = SOCRATIC_SYSTEM_PROMPT.format(
            grade=student_grade,
            subject=subject_name
        )
        
        # 2. Mock Response (for now, until API key is set)
        last_msg = history[-1].content.lower()
        
        if "answer" in last_msg or "solve" in last_msg:
            return "🤔 I see you're looking for the answer! I can't give you that directly. What formula do you think applies here?"
        
        if "explain" in last_msg:
            return f"📚 Let's break this down. In {subject_name}, this concept usually starts with definitions. What do you know about it so far?"
            
        return "✨ That's an interesting question! Can you tell me what Step 1 would be?"

        # --- REAL IMPLEMENTATION (commented out) ---
        # messages = [{"role": "system", "content": sys_prompt}] + [m.dict() for m in history]
        # response = await self.client.chat.completions.create(
        #     model="gpt-4o",
        #     messages=messages
        # )
        # return response.choices[0].message.content

    async def generate_homework(
        self, 
        topic: str, 
        grade: int, 
        difficulty: str = "medium"
    ) -> Dict:
        """
        Generate a structured homework assignment.
        """
        # Mock Generation
        return {
            "title": f"{topic} Practice ({difficulty.title()})",
            "description": f"AI Generated exercises for Grade {grade}",
            "problems": [
                {"q": "Problem 1...", "type": "multiple_choice"},
                {"q": "Problem 2...", "type": "open_answer"}
            ]
        }
