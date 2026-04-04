# Converted from Semmy's LLM API Test Script
#
# This script defines a sample prompt and API call that would be 
# implemented into the tablets system for lightweight and fast access to an LLM "teacher"
# This is a version using the OpenAI key rather than gemini
# Good progamming practices says I can't push my ky key to gh, so just ask me if you need it for testing.

import os
import json
import datetime
from typing import TypedDict
import os
from openai import OpenAI # install openai to venv

# globals

# to get the api key type this into terminal: export OPENAI_API_KEY="actual key here"
# print("API KEY:", os.getenv("OPENAI_API_KEY")) # check if it worked
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = "gpt-5-mini"
# GEMINI_API_KEY = "put your api key here"
# MODEL_NAME = "gemini-1.5-flash" # best LLM model for fast responses, accuracy may struggle


# genai.configure(api_key=GEMINI_API_KEY) # basically sign in

class JapaneseFeedback(TypedDict): 
    """
    This is a class that I made for the API definition, im not sure if its complete or if it needs more fields,
    but it should be enough to get us started with testing the API and seeing how it works. 
    """
    timestamp: str
    model: str
    # probably some field for the practice target word
    is_correct: bool
    english_explanation: str
    japanese_feedback: str
    suggested_correction: str
    
# def evaluate_japanese_usage(study_word: str, user_sentence: str):
#     """
#     Evaluates a user's sentence based on a specific study word.
#     """
#     model = genai.GenerativeModel(MODEL_NAME)
    
#     # the prompt is very important and I still havent figured out an optimal one
#     prompt = f"""
#     You are a Japanese language sensei. 
#     The student is a beginner learning the word: "{study_word}".
#     They wrote the following sentence: "{user_sentence}"
    
#     Evaluate if they used the word correctly in context. 
#     Provide feedback in both English and Japanese (hiragana/kanji).
#     Keep the Japanese feedback simple for a beginner.
#     """

#     # Guarantee JSON output
#     response = model.generate_content(
#         prompt,
#         generation_config={
#             "response_mime_type": "application/json",
#             "response_schema": JapaneseFeedback
#         }
#     )
    
    
#     feedback_data = json.loads(response.text) # the reposese will be stored in a dict
    
#     # Manually adding metadata as requested
#     feedback_data['timestamp'] = datetime.datetime.now().isoformat()
#     feedback_data['model'] = MODEL_NAME
    
#     return feedback_data
    
def evaluate_japanese_usage(study_word: str, user_sentence: str):
    """
    Evaluates a user's sentence based on a specific study word.
    """

    prompt = f"""
    You are a Japanese language sensei. 
    The student is a beginner learning the word: "{study_word}".
    They wrote the following sentence: "{user_sentence}"

    Evaluate if they used the word correctly in context.
    Provide feedback in both English and Japanese (hiragana/kanji).
    Keep the Japanese feedback simple for a beginner.

    Respond ONLY in valid JSON with the following fields:
    - is_correct (boolean)
    - english_explanation (string)
    - japanese_feedback (string)
    - suggested_correction (string)
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "JapaneseFeedback",
                "schema": {
                    "type": "object",
                    "properties": {
                        "is_correct": {"type": "boolean"},
                        "english_explanation": {"type": "string"},
                        "japanese_feedback": {"type": "string"},
                        "suggested_correction": {"type": "string"},
                    },
                    "required": [
                        "is_correct",
                        "english_explanation",
                        "japanese_feedback",
                        "suggested_correction",
                    ],
                },
            },
        },
    )

    # feedback_data = response.output_parsed
    feedback_data = json.loads(response.choices[0].message.content)

    # Add metadata
    feedback_data["timestamp"] = datetime.datetime.now().isoformat()
    feedback_data["model"] = MODEL_NAME

    return feedback_data

# --- Example Usage ---
if __name__ == "__main__":
    target_word = "食べる (taberu)"
    user_input = "I 食べる sushi tomorrow."
    
    result = evaluate_japanese_usage(target_word, user_input)
    
    print(json.dumps(result, indent=4, ensure_ascii=False))