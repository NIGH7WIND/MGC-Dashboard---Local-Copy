import asyncio
from datetime import datetime, timedelta, date
import pandas as pd
import time
from gnews import GNews
import logging
from aiohttp import ClientSession, ClientTimeout

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create an asynchronous function to fetch news for a specific interval
async def fetch_news_for_interval(company_name: str, interval_start: str, interval_end: str, max_results: int = 100, session: ClientSession = None):
    """
    Fetch news articles for a specific time interval asynchronously.
    """
    logger.info(f"Fetching articles for '{company_name}' from {interval_start} to {interval_end}.")
    start_time = time.time()

    try:
        google_news = GNews(language='en', country='IN', max_results=max_results, start_date=date.fromisoformat(interval_start), end_date=date.fromisoformat(interval_end))
        search_results = await asyncio.to_thread(google_news.get_news, company_name)

        articles = []
        for result in search_results:
            try:
                link = result["url"]
                date_published = datetime.strptime(result["published date"], '%a, %d %b %Y %H:%M:%S GMT').strftime('%Y-%m-%d')
                title = result["title"]
                if not title:
                    raise ValueError("Title empty.")

                article = {
                    "Title": title,
                    "Link": link,
                    "Published_Date": date_published
                }
                articles.append(article)
            except Exception as e:
                logger.warning(f"Error processing article result: {e}", exc_info=True)

        logger.info(f"Fetched {len(articles)} articles for '{company_name}' from {interval_start} to {interval_end}.")
        return articles
    except Exception as e:
        logger.error(f"Error in fetch_news_for_interval: {e}", exc_info=True)
        return []
    finally:
        logger.debug(f"Interval fetch completed in {time.time() - start_time:.2f} seconds.")


# Function to run the asynchronous tasks concurrently
async def fetch_all_news(company_name: str, intervals: list, max_results: int = 100):
    """
    Fetch news articles asynchronously for all intervals.
    """
    tasks = []
    async with ClientSession(timeout=ClientTimeout(total=10)) as session:
        for interval_start, interval_end in intervals:
            tasks.append(fetch_news_for_interval(company_name, interval_start, interval_end, max_results, session))

        results = await asyncio.gather(*tasks)
        
    return results


def get_days_from_period(period: str) -> int:
    """
    Converts a period string (e.g., '7d', '30d', '365d') to the number of days.

    Args:
    - period (str): The period string.

    Returns:
    - int: The number of days corresponding to the given period.
    """
    period_unit = period[-1]  # 'd' for days
    period_value = int(period[:-1])  # Extract the numeric part

    if period_unit == 'd':
        return period_value
    else:
        raise ValueError("Invalid period format. Use 'd' for days.")


def news_scraper_RSS_links(company_name: str, period: str, max_results: int = 100):
    """
    Scrapes news articles from Google News for a given company asynchronously over a split time period.
    """
    logger.info(f"Starting news scraper for '{company_name}' with period '{period}'.")
    start_time = time.time()

    try:
        # Convert the period to the total number of days
        total_days = get_days_from_period(period)

        # Get the current date as the end date (only date, no time)
        end_dt = datetime.now().date()

        # Calculate the start date based on the total days
        start_dt = end_dt - timedelta(days=total_days)

        # Split the date range into 5 equal intervals to get more results
        num_intervals = 5
        interval_days = total_days // num_intervals

        intervals = []
        for i in range(num_intervals):
            interval_start = (start_dt + timedelta(days=i * interval_days)).strftime('%Y-%m-%d')
            interval_end = (start_dt + timedelta(days=(i + 1) * interval_days)).strftime('%Y-%m-%d')
            if i == num_intervals - 1:  # Ensure the last interval goes up to the end date
                interval_end = end_dt.strftime('%Y-%m-%d')

            intervals.append((interval_start, interval_end))

        # Run the async function to fetch news
        results = asyncio.run(fetch_all_news(company_name, intervals, max_results))

        # Combine results into a DataFrame
        all_articles = []
        for result in results:
            all_articles.extend(result)

        article_df_with_rssLinks = pd.DataFrame(all_articles).reset_index(drop=True)

        # Sort the final DataFrame by the published date and drop duplicates
        article_df_with_rssLinks = article_df_with_rssLinks.sort_values(by="Published_Date").drop_duplicates(subset=["Title", "Link", "Published_Date"]).reset_index(drop=True)
        logger.info(f"Scraper completed successfully. Total articles fetched: {len(article_df_with_rssLinks)}.")
        return article_df_with_rssLinks
    
    except Exception as e:
        logger.error(f"Error in news_scraper_RSS_links: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        logger.info(f"News scraper completed in {time.time() - start_time:.2f} seconds.")
