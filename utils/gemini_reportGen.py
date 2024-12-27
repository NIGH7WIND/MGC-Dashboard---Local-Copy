import os
import google.generativeai as genai
from utils.sysInstruct_reportGen import generate_system_instruction
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def generate_financial_report(company_name: str, user_input: str) -> str:
    # Configure the API with your GEMINI API key
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    # Set up generation configuration
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    # Set up safety settings
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
    }

    # Generate system instruction for the given company
    system_instruction = generate_system_instruction(company_name)

    # Create the model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
        system_instruction=system_instruction
    )

    # Start chat session
    chat_session = model.start_chat(
        history=[]
    )

    # Send the user input message to get the output
    response = chat_session.send_message(user_input)

    # Return the response text
    return response.text
