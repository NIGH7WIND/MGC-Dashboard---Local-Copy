import pandas as pd
import asyncio
import aiohttp
from trafilatura import extract
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_url_async(session, url):
    """
    Asynchronously fetch the HTML content of a URL.

    Args:
        session (aiohttp.ClientSession): The session to make the request.
        url (str): The URL to fetch.

    Returns:
        str: The HTML content or None if the fetch fails.
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        logger.error(f"Failed to fetch URL: {url}, Error: {str(e)}")
        return None

async def extract_content(url, session):
    """
    Asynchronously extract content from a URL using trafilatura.

    Args:
        url (str): The URL to extract content from.
        session (aiohttp.ClientSession): The session to make the request.

    Returns:
        str: The extracted content or None if extraction fails.
    """
    try:
        page_content = await fetch_url_async(session, url)
        if not page_content:
            raise ValueError(f"Failed to retrieve content from {url}")

        tflr_content = extract(page_content)
        
        if not tflr_content:
            raise ValueError("Trafilatura failed to extract content.")

        logger.debug(f"Extracted content from {url} (Length: {len(tflr_content)})")
        return tflr_content

    except Exception as e:
        logger.error(f"Error processing URL {url}: {str(e)}")
        return None

async def extract_content_for_multiple_urls(urls):
    """
    Process multiple URLs to extract content concurrently.

    Args:
        urls (list of str): List of URLs to extract content from.

    Returns:
        dict: A dictionary where keys are URLs and values are the extracted content (or None for failed extractions).
    """
    async with aiohttp.ClientSession() as session:
        tasks = {url: extract_content(url, session) for url in urls if not url.startswith("https://news.google.com")}
        results = await asyncio.gather(*tasks.values())
        
        # Map results to their corresponding URLs
        return dict(zip(tasks.keys(), results))

def extract_content_sync(urls):
    """
    Synchronous wrapper for extracting content from multiple URLs.

    Args:
        urls (list of str): List of URLs to extract content from.

    Returns:
        dict: A dictionary where keys are URLs and values are the extracted content (or None for failed extractions).
    """
    return asyncio.run(extract_content_for_multiple_urls(urls))


# # Example usage

# if __name__ == "__main__":
#     # Sample list of URLs (replace with actual URLs you want to process)
#     df = pd.read_excel(r"E:\Intern\Minerva\Web Scrapping\TATA Motors_LinksResolved.xlsx")
#     df = df.dropna()
#     urls = df["ResolvedLink"].tolist()

#     # Synchronously extract content from multiple URLs
#     extracted_content = extract_content_sync(urls)

#     # Update the DataFrame with the extracted content
#     df["ExtractedContent"] = df["ResolvedLink"].map(extracted_content)

#     # Print the updated DataFrame
#     print(df.head())
