from datetime import datetime, timedelta, date
import pandas as pd
import time
from gnews import GNews
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def fetch_news_for_interval(company_name: str, interval_start: str, interval_end: str, max_results: int = 100):
    """
    Fetch news articles for a specific time interval.

    Args:
    - company_name (str): The name of the company to search for.
    - interval_start (str): The start date in 'YYYY-MM-DD' format.
    - interval_end (str): The end date in 'YYYY-MM-DD' format.
    - max_results (int): The maximum number of results for this interval.

    Returns:
    - articles (list): List of dictionaries containing news articles for the interval.
    """
    logger.info(f"Fetching articles for '{company_name}' from {interval_start} to {interval_end}.")
    start_time = time.time()
    
    try:
        google_news = GNews(language='en', country='IN', max_results=max_results, start_date=date.fromisoformat(interval_start), end_date=date.fromisoformat(interval_end))
        search_results = google_news.get_news(company_name)

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
    

def news_scraper_RSS_links(company_name: str, period: str, max_results: int = 100):
    """
    Scrapes news articles from Google News for a given company over a split time period.

    Args:
    - company_name (str): The name of the company to search for.
    - period (str): The time period selected from the frontend (e.g., '7d', '30d', '365d', '730d').
    - max_results (int): The maximum number of results per interval (default: 100).

    Returns:
    - df (pd.DataFrame): A DataFrame containing the scraped news articles with columns: Title, Link, Published_Date.
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

        # Prepare a DataFrame to store all the results
        article_df_with_rssLinks = pd.DataFrame()

        # Use ThreadPoolExecutor to fetch results in parallel
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(fetch_news_for_interval, company_name, start, end, max_results) for start, end in intervals]
            
            for future in as_completed(futures):
                articles = future.result()
                interval_df = pd.DataFrame(articles).reset_index(drop=True)
                article_df_with_rssLinks = pd.concat([article_df_with_rssLinks, interval_df], ignore_index=True)

        # Sort the final DataFrame by the published date and drop duplicates
        article_df_with_rssLinks = article_df_with_rssLinks.sort_values(by="Published_Date").drop_duplicates(subset=["Title", "Link"]).reset_index(drop=True)
        logger.info(f"Scraper completed successfully. Total articles fetched: {len(article_df_with_rssLinks)}.")
        return article_df_with_rssLinks
    
    except Exception as e:
        logger.error(f"Error in news_scraper_RSS_links: {e}", exc_info=True)
        return pd.DataFrame()
    finally:
        logger.info(f"News scraper completed in {time.time() - start_time:.2f} seconds.")