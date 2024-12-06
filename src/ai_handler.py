import os
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

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
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
        self._toc_cache = {}


    def process_toc(self, toc_content: str) -> TOCStructure:
        cache_key = hash(toc_content)
        if cache_key in self._toc_cache:
            return self._toc_cache[cache_key]
           
        prompt = self._create_toc_prompt(toc_content)
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Use the appropriate model
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes and structures table of contents information from textbooks."},
                {"role": "user", "content": prompt}
            ],
            response_format=TOCStructure,
        )
        self._toc_cache[cache_key] = completion.choices[0].message.parsed
        return self._toc_cache[cache_key]
   
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
   
    def generate_questions(self, section_content: str, num_questions: int = 5) -> Questions:
        """
        Generate a specific number of questions from section content.
       
        Args:
            section_content: The text content to generate questions from
            num_questions: Number of questions to generate (default: 5)
           
        Returns:
            Questions object containing generated questions and answers
        """
        prompt = self._create_question_prompt(section_content, num_questions)
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Use the appropriate model
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are an AI assistant that generates exactly {num_questions} "
                        "fill-in-the-blank questions from textbook sections provided to you "
                        "(delimited by XML tags). Each question must:\n"
                        "- Have exactly ONE blank space indicated by '_____' \n"
                        "- The blank can accept multiple words as an answer, but there should only be one blank per question\n"
                        "Example good format:\n"
                        "Q: The first civilization in Mesopotamia was established by the _____ people.\n"
                        "A: Sumerian\n\n"
                        "Example bad format (do not use):\n"
                        "Q1: The _____ civilization was established in _____ BCE.\n"
                        "A1: Sumerian, 4000\n\n"
                        "Focus on the main educational content, ignoring figure descriptions, "
                        "in-text questions, and other miscellaneous information. If you cannot "
                        "create suitable questions from the given content, state 'I could not "
                        "generate appropriate questions from this content.'"
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format=Questions,
        )
        return completion.choices[0].message.parsed
   
    def _create_question_prompt(self, section_content: str, num_questions: int) -> str:
        """
        Create a prompt for question generation with specific question count.
       
        Args:
            section_content: The content to generate questions from
            num_questions: Number of questions to generate
           
        Returns:
            Formatted prompt string
        """
        return f"""
        <section>
        {section_content}
        </section>
        Please generate exactly {num_questions} questions in the following format:
        {{
            "questions": [
                {{
                    "question": "Question",
                    "answer": "Answer"
                }},
            ]
        }}
        """