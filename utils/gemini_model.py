import logging
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def model_config():
    logger.info("Setting up the model configuration.")
    # Create the model
    generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_schema": content.Schema(
        type = content.Type.OBJECT,
        description = "Schema for analyzing financial sentiment, red flag scoring, and answering financial analysis questions of news headlines.",
        required = [
            "headline", "positive_sentiment", "negative_sentiment", "neutral_sentiment", 
            "red_flag_score", "tags", "unique_id", "Q1", "Q2", "Q3", "Q4", "Q5", 
            "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q12"
        ],
        properties = {
            "headline": content.Schema(
                type = content.Type.STRING,
            ),
            "positive_sentiment": content.Schema(
                type = content.Type.NUMBER,
            ),
            "negative_sentiment": content.Schema(
                type = content.Type.NUMBER,
            ),
            "neutral_sentiment": content.Schema(
                type = content.Type.NUMBER,
            ),
            "red_flag_score": content.Schema(
                type = content.Type.NUMBER,
            ),
            "tags": content.Schema(
                type = content.Type.ARRAY,
                items = content.Schema(
                    type = content.Type.STRING,
                ),
            ),
            "unique_id": content.Schema(
                type = content.Type.NUMBER,
            ),
            "Q1": content.Schema(
                type = content.Type.OBJECT,
                description = "Are there any regulatory or legal issues faced by the Company or its subsidiaries?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Yes", "No", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q2": content.Schema(
                type = content.Type.OBJECT,
                description = "Are there any legal issues faced by the promoters of the Company?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Yes", "No", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q3": content.Schema(
                type = content.Type.OBJECT,
                description = "Has the Company faced employee attrition in the past and has the key management team changed in the past 2 years?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Yes", "No", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q4": content.Schema(
                type = content.Type.OBJECT,
                description = "Is the industry in which Company operates facing a slowdown?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Yes", "No", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q5": content.Schema(
                type = content.Type.OBJECT,
                description = "Is the Company overvalued as compared to its peers?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Yes", "No", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q6": content.Schema(
                type = content.Type.OBJECT,
                description = "Are there any significant upcoming events or product launches that could impact the company’s performance?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Yes", "No", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q7": content.Schema(
                type = content.Type.OBJECT,
                description = "Has the Company's revenues, operating profit margins, and net profit margins grown year-on-year for the past 3 years, and are these better than industry growth rates?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Yes", "No", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q8": content.Schema(
                type = content.Type.OBJECT,
                description = "Has the Company's debt increased or decreased over the past 3 years?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Increased", "Decreased", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q9": content.Schema(
                type = content.Type.OBJECT,
                description = "Has the Company's capacity utilization increased or decreased over the past 3 years, and how much capacity has the Company added in the past 3 years?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Increased", "Decreased", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q10": content.Schema(
                type = content.Type.OBJECT,
                description = "Has the promoter stake in the Company increased or decreased in the past?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Increased", "Decreased", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q11": content.Schema(
                type = content.Type.OBJECT,
                description = "Has the institution stake in the Company increased or decreased in the past?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Increased", "Decreased", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
            "Q12": content.Schema(
                type = content.Type.OBJECT,
                description = "How many analysts are tracking the Company's stock, and what is the percentage upside on the target price given by the analysts?",
                required = ["categorical"],
                properties = {
                    "categorical": content.Schema(
                        type = content.Type.STRING,
                        enum = ["Upside", "No Upside", "N/A"]
                    ),
                    "text": content.Schema(
                        type = content.Type.STRING,
                    ),
                },
            ),
        },
    ),
    "response_mime_type": "application/json",
    }
    
    return generation_config

def initiate_model(company_name, config):
    logger.info(f"Initializing the model for company: {company_name}.")
    model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-8b",
    generation_config=config,
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
    },
    system_instruction=f"You are a financial expert with the skillset of a professional quantitative trader and investment analyst responsible for analysing \nCompany_name: {company_name}\nYour task is to analyze the news articles with content relevant to {company_name} and assign financial sentiment scores (positive, negative, and neutral) and a red flag score (all on a scale of 0-100). Red flag scores should be based on events or information that are significantly detrimental for the company (drop in stock price is not a red flag but mostly an after effect of the redflag event. Give higher red flag scores for the redflag event). If an article content is not relevant to {company_name}, assign full neutral score and other scores 0. Scoring must be strictly based on the information from news articles relevant to {company_name}, reflecting the potential financial impact of the information on stock price and investment decisions. Emphasize the scoring based on how these news would affect the {company_name} company’s financial outlook. Assign relevant tags(no more than 3) to the articles. Assign same unique_id to articles that deal with the same incident by comparing the article headlines. Ensure each unique story receives only one unique ID. \n\nAdditionally, evaluate the following questions based on the information from the news articles using a combination of categorical (given in json schema) and contextual answers (4 lines for each answer N/A if no relevant info):\n\nAre there any regulatory or legal issues faced by {company_name} or its subsidiaries?\nAre there any legal issues faced by the promoters of {company_name}?\nHas {company_name} faced employee attrition in the past, and has the key management team of {company_name} changed in the past 2 years?\nIs the industry in which {company_name} operates facing a slowdown?\nIs {company_name} overvalued compared to its peers?\nAre there any significant upcoming events or product launches that could impact {company_name}'s performance?\nHas {company_name} revenue, operating profit margins, and net profit margins grown year-on-year for the past 3 years, and are these better than industry growth rates?\nHas {company_name} debt increased or decreased over the past 3 years?\nHas {company_name} capacity utilization increased or decreased over the past 3 years, and how much capacity has {company_name} added in the past 3 years?\nHas the promoter stake in {company_name} increased or decreased in the past?\nHas the institutional stake in {company_name} increased or decreased in the past?\nHow many analysts are tracking {company_name} stock, and what is the percentage upside on the target price given by these analysts?\n\nThe answers must be specifically relevant to {company_name} and must be based on the news article content. Include a one line justification of the answer as well. If no relevant information is available for any question, use \"N/A\" as the answer.",
    )
    return model

def start_history(model):
    logger.info("Starting chat session.")
    chat_session = model.start_chat(
        history=[
        ]
    )
    return chat_session

def model_output(article_headline, article_content, chat_session):
    logger.info(f"Processing article: {article_headline}.")
    response = chat_session.send_message(f"headline:{article_headline} \n content: {article_content}")
    return response