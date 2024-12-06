import os
import json
import ast
import pandas as pd
import asyncio
import time
from dotenv import load_dotenv
from utils.gemini_model import model_config, initiate_model, start_history, model_output
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
genai_api_key = os.getenv("GEMINI_API_KEY")
assert genai_api_key, "GEMINI_API_KEY is not set in the environment variables."

# Pricing constants (price per million tokens * USD to INR conversion)
INPUT_PRICING = 0.075 * 10**-6 * 84
OUTPUT_PRICING = 0.30 * 10**-6 * 84

def format_q_value(value):
    """
    Format the 'Q' columns containing JSON-like data for readability.

    :param value: JSON-like string or dict.
    :return: Formatted string or "Invalid data format".
    """
    try:
        if isinstance(value, str):
            data_dict = ast.literal_eval(value)
        else:
            data_dict = value
    except (json.JSONDecodeError, ValueError):
        return "Invalid data format"

    categorical = data_dict.get('categorical', 'N/A')
    text = data_dict.get('text', 'N/A')

    if categorical == 'N/A' and text == 'N/A':
        return "N/A"
    elif text == "N/A":
        return categorical
    else:
        return f"{categorical}\n{text}"

async def process_article(article, chat_session):
    """
    Process a single article using the Gemini API.

    :param article: A dictionary containing article data.
    :param chat_session: Chat session object.
    :return: Processed result and token counts.
    """
    try:
        article_headline = article["Title"]
        article_content = article["Content"]
        logger.debug(f"Processing article: {article_headline}.")

        # Call the synchronous model output in a thread
        response = await asyncio.to_thread(model_output, article_headline, article_content, chat_session)

        # Extract result and token usage
        result = json.loads(response.text)
        result["date"] = article["Published_Date"]
        result["link"] = article["ResolvedLink"]
        inp_tokens = response.usage_metadata.prompt_token_count
        out_tokens = response.usage_metadata.candidates_token_count

        return result, inp_tokens, out_tokens
    except Exception as e:
        logger.error(f"Error processing article: {article['Title']}. Error: {e}")
        return None, 0, 0

async def process_chunk(chunk, model):
    """
    Process all articles in a single date chunk.

    :param chunk: DataFrame containing articles for a single date.
    :param model: Gemini model instance.
    :return: List of processed results and token counts.
    """
    curr_date = chunk["Published_Date"].values[0]
    logger.info(f"Processing articles for date: {curr_date}.")
    chat_session = start_history(model)

    chunk_results = []
    chunk_inp_tokens = 0
    chunk_out_tokens = 0

    for _, article in chunk.iterrows():
        result, inp_tokens, out_tokens = await process_article(article, chat_session)
        if result:
            chunk_results.append(result)
        chunk_inp_tokens += inp_tokens
        chunk_out_tokens += out_tokens

    logger.info(f"Finished processing for date: {curr_date}. Tokens used: {chunk_inp_tokens + chunk_out_tokens}.")
    return chunk_results, chunk_inp_tokens, chunk_out_tokens

async def process_all_chunks(date_chunks, model):
    """
    Process all date chunks concurrently.

    :param date_chunks: List of DataFrames grouped by date.
    :param model: Gemini model instance.
    :return: DataFrame of all processed results.
    """
    all_results = []
    total_inp_tokens = 0
    total_out_tokens = 0

    tasks = [process_chunk(chunk, model) for chunk in date_chunks]
    for chunk_results, chunk_inp_tokens, chunk_out_tokens in await asyncio.gather(*tasks):
        all_results.extend(chunk_results)
        total_inp_tokens += chunk_inp_tokens
        total_out_tokens += chunk_out_tokens

        logger.debug(f"Chunk cost: Rs-{chunk_inp_tokens * INPUT_PRICING + chunk_out_tokens * OUTPUT_PRICING:.2f}.")

    logger.info(f"Total tokens used: {total_inp_tokens + total_out_tokens}. "
                f"Total cost: Rs-{total_inp_tokens * INPUT_PRICING + total_out_tokens * OUTPUT_PRICING:.2f}.")
    return pd.DataFrame(all_results)

async def process_articles(df, company_name):
    """
    Entry point for processing articles.

    :param df: DataFrame containing article data.
    :param company_name: Name of the company for model configuration.
    :return: DataFrame containing processed article results with the cols:
    Q1,	Q2,	Q3,	Q4,	Q5,	Q6,	Q7,	Q8,	Q9,	headline, negative_sentiment, neutral_sentiment, positive_sentiment, red_flag_score, tags, unique_id, date, link.
    """
    # Group data by date
    date_chunks = [group for _, group in df.groupby("Published_Date")]

    # Initialize the model
    config = model_config()
    model = initiate_model(company_name, config)

    # Process all chunks
    results_df = await process_all_chunks(date_chunks, model)

    # Format 'Q' columns if they exist
    q_cols = [col for col in results_df.columns if col.startswith('Q')]
    for col in q_cols:
        results_df[col] = results_df[col].apply(format_q_value)

    return results_df

def process_articles_sync(df, company_name):
    """
    Synchronous wrapper for processing articles.
    
    :param df: DataFrame containing article data.
    :param company_name: Name of the company for model configuration.
    :return: DataFrame containing processed article results.
    """
    # Run the asynchronous code in a synchronous context
    return asyncio.run(process_articles(df, company_name))

# Usage example
if __name__ == "__main__":
    start_time = time.time()
    # Load your DataFrame from wherever it is (e.g., from an Excel file, database, etc.)
    df = pd.read_excel(r"E:\Intern\Minerva\LLM API\Input_files\AG_test.xlsx")
    company_name = "Adani Green Energy Ltd"

    # Process the DataFrame instead of a file path
    processed_df = process_articles_sync(df, company_name)
    processed_df.to_excel("gemini_debugging_output.xlsx", index=False)
    print("Processing complete.")
    print(processed_df.head())  # Replace with further integration into Flask
    print("Time elapsed: ", time.time() - start_time)
