import pandas as pd
import asyncio
import aiohttp
from trafilatura import extract
from newspaper import Article
import logging
import time
from concurrent.futures import ThreadPoolExecutor

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Thread pool executor for Newspaper3k to allow non-blocking execution
executor = ThreadPoolExecutor()

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
        logger.debug(f"Failed to fetch URL {url}: Error: {str(e)}")
        return None

async def extract_with_trafilatura(url, session):
    """
    Extract content from a URL using Trafilatura.

    Args:
        url (str): The URL to extract content from.
        session (aiohttp.ClientSession): The session to make the request.

    Returns:
        str: Extracted content or None if extraction fails.
    """
    try:
        page_content = await fetch_url_async(session, url)
        if not page_content:
            raise ValueError("Failed to retrieve page content.")
        tflr_content = extract(page_content)
        if not tflr_content:
            raise ValueError("Trafilatura extraction failed.")
        logger.info(f"Extracted with Trafilatura from {url}")
        return tflr_content
    except Exception as e:
        logger.debug(f"Trafilatura failed for {url}: {str(e)}")
        return None

def extract_with_newspaper(url):
    """
    Extract content from a URL using Newspaper3k.

    Args:
        url (str): The URL to extract content from.

    Returns:
        str: Extracted content or None if extraction fails.
    """
    try:
        article = Article(url)
        article.download()
        article.parse()
        if article.text:
            logger.info(f"Extracted with Newspaper3k from {url}")
            return article.text
        else:
            return None
    except Exception as e:
        logger.debug(f"Newspaper3k failed for {url}: {str(e)}")
        return None

async def extract_with_newspaper_async(url):
    """
    Non-blocking wrapper for Newspaper3k extraction.

    Args:
        url (str): The URL to extract content from.

    Returns:
        str: Extracted content or None if extraction fails.
    """
    return await asyncio.get_event_loop().run_in_executor(executor, extract_with_newspaper, url)

async def extract_content_with_fallback(url, session):
    """
    Attempt to extract content using Trafilatura and fall back to Newspaper3k if it fails.

    Args:
        url (str): The URL to extract content from.
        session (aiohttp.ClientSession): The session to make requests.

    Returns:
        str: Extracted content or None if both methods fail.
    """
    content = await extract_with_trafilatura(url, session)
    if content:
        return content
    else:
        logger.debug(f"Falling back to Newspaper3k for {url}")
        content = await extract_with_newspaper_async(url)
        return content

async def extract_content_for_multiple_urls(urls):
    """
    Extract content for multiple URLs concurrently.

    Args:
        urls (list of str): List of URLs to extract content from.

    Returns:
        dict: A dictionary where keys are URLs and values are the extracted content.
    """
    async with aiohttp.ClientSession() as session:
        # Create tasks and ensure coroutines are properly awaited
        tasks = [extract_content_with_fallback(url, session) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {url: result if not isinstance(result, Exception) else None for url, result in zip(urls, results)}

def extract_content_sync(urls):
    """
    Synchronous wrapper for extracting content from multiple URLs.

    Args:
        urls (list of str): List of URLs to extract content from.

    Returns:
        dict: A dictionary where keys are URLs and values are the extracted content (or None for failed extractions).
    """
    results = asyncio.run(extract_content_for_multiple_urls(urls))

    # Log and print summary
    total_urls = len(urls)
    total_failed = sum(1 for content in results.values() if content is None)
    total_success = total_urls - total_failed

    if total_failed > 0:
        logger.debug("Failed URLs:")
        for url, content in results.items():
            if content is None:
                logger.debug(f"- {url}")

    logger.info(f"Total URLs processed: {total_urls}")
    logger.info(f"Total successful extractions: {total_success}")
    logger.info(f"Total failed extractions: {total_failed}")

    print(f"Extraction Summary: Processed: {total_urls}, Success: {total_success}, Failed: {total_failed}")
    return results

# Example usage
if __name__ == "__main__":
    # Load URLs from Excel
    df = pd.read_excel(r"E:\Intern\Minerva\Web Scrapping\TATA Motors_LinksResolved.xlsx")
    df = df.dropna()
    urls = df["ResolvedLink"].tolist()

    start_time = time.time()

    # Extract content
    results = extract_content_sync(urls)

    print("Total time taken for content extraction: ", time.time() - start_time, "s")

    # Save results
    output_path = r"E:\Intern\Minerva\Web Scrapping\Extracted_Content.xlsx"
    df_results = pd.DataFrame([{"URL": url, "Content": content} for url, content in results.items()])
    df_results.to_excel(output_path, index=False)
    logger.info(f"Extraction results saved to {output_path}")

    # Optionally save failed URLs for later inspection
    failed_output_path = r"E:\Intern\Minerva\Web Scrapping\Failed_URLs.xlsx"
    failed_urls = [url for url, content in results.items() if content is None]
    pd.DataFrame({"FailedURLs": failed_urls}).to_excel(failed_output_path, index=False)
    logger.info(f"Failed URLs saved to {failed_output_path}")
