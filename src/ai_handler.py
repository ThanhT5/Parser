import os  # Importing the os module to interact with the operating system
from openai import OpenAI  # Importing the OpenAI client for API interactions
from pydantic import BaseModel  # Importing BaseModel for data validation and settings management
from typing import List  # Importing List for type hinting

# Class representing a single entry in the table of contents (TOC)
class TOCEntry(BaseModel):
    level: int  # The hierarchy level of the entry (0 for chapters, 1 for sections, etc.)
    number: str  # The number of the chapter or section
    title: str  # The title of the chapter or section
    page: int  # The page number where the chapter or section starts

# Class representing the structure of the table of contents
class TOCStructure(BaseModel):
    entries: List[TOCEntry]  # A list of TOCEntry objects

# Class representing a question and its answer
class Question(BaseModel):
    # chapter: int  # Optional: chapter number (commented out for now)
    question: str  # The question text
    answer: str  # The answer to the question

# Class representing a collection of questions
class Questions(BaseModel):
    questions: List[Question]  # A list of Question objects

# Class to handle interactions with the ChatGPT API
class ChatGPTHandler:
    def __init__(self):
        # Retrieve the OpenAI API key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Raise an error if the API key is not found
            raise ValueError("No OpenAI API key found. Please set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)  # Initialize the OpenAI client with the API key

    # Method to process the table of contents and return a structured TOC
    def process_toc(self, toc_content: str) -> TOCStructure:
        prompt = self._create_toc_prompt(toc_content)  # Create a prompt for the API
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Specify the model to use
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes and structures table of contents information from textbooks."},
                {"role": "user", "content": prompt}  # User's prompt for processing
            ],
            response_format=TOCStructure,  # Specify the expected response format
        )
        return completion.choices[0].message.parsed  # Return the parsed response

    # Private method to create a prompt for analyzing the TOC
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
    
    # Method to generate questions based on section content
    def generate_questions(self, section_content: str) -> List[str]:
        prompt = self._create_question_prompt(section_content)  # Create a prompt for question generation
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",  # Specify the model to use
            messages=[
                {"role": "system", "content": "You are an AI assistant that generates 5 fill-in-the-blank questions from textbook sections provided to you (delimited by XML tags). Focus on the main educational content, ignoring figure descriptions, in-text questions, and other miscellaneous information. Generate 5 questions for each request. If you cannot create suitable questions from the given content, state 'I could not generate appropriate questions from this content.'"},
                {"role": "user", "content": prompt}  # User's prompt for generating questions
            ],
            response_format=Questions,  # Specify the expected response format
        )
        return completion.choices[0].message.parsed  # Return the parsed response
    
    # Private method to create a prompt for generating questions
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