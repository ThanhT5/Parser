import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List

class TOCEntry(BaseModel):
    level: int
    number: str
    title: str
    page: int

class TOCStructure(BaseModel):
    entries: List[TOCEntry]

class Question(BaseModel):
    #chapter: int
    question: str
    answer: str

class Questions(BaseModel):
    questions: List[Question]

class ChatGPTHandler:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)

    def process_toc(self, toc_content: str) -> TOCStructure:
        prompt = self._create_toc_prompt(toc_content)
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes and structures table of contents information from textbooks."},
                {"role": "user", "content": prompt}
            ],
            response_format=TOCStructure,
        )
        return completion.choices[0].message.parsed
    
    def _create_toc_prompt(self, toc_content: str) -> str:
        return f"""
        Please analyze the following table of contents from a textbook and extract the following information:
        - Chapter numbers and titles
        - Section numbers and titles within each chapter
        - Page numbers for each chapter and section

        Here's the table of contents content:

        {toc_content}

        Please structure the information according to the following format:
        {{
            "entries": [
                {{
                    "level": 0,
                    "number": "1",
                    "title": "Chapter Title",
                    "page": 10
                }},
                {{
                    "level": 1,
                    "number": "1.1",
                    "title": "Section Title",
                    "page": 11
                }},
                ...
            ]
        }}

        Use "level" to indicate the hierarchy:
        - 0 for chapters
        - 1 for sections
        - 2 for subsections (if any)
        - and so on for deeper levels
        """
    
    def generate_questions(self, section_content: str) -> List[str]:
        prompt = self._create_question_prompt(section_content)
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are an AI assistant that generates 5 fill-in-the-blank questions from textbook sections provided to you (delimited by XML tags). Focus on the main educational content, ignoring figure descriptions, in-text questions, and other miscellaneous information. Generate 5 questions for each request. If you cannot create suitable questions from the given content, state 'I could not generate appropriate questions from this content.'"},
                {"role": "user", "content": prompt}
            ],
            response_format=Questions,
        )
        return completion.choices[0].message.parsed
    
    def _create_question_prompt(self, section_content: str) -> str:
        return f"""
        <section>
        {section_content}
        </section>
        Please structure the questions in the following format:
        {{
            "questions": [
                {{
                    "question": "Question",
                    "answer": "Answer"
                }},
            ]
        }}


        """