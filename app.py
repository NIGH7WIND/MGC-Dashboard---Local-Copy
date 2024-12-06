from flask import Flask, render_template, request, jsonify
from utils.gnews_scraper import news_scraper_RSS_links
from utils.playwright_rssLinksResolver import GoogleNewsLinkResolver
from utils.trafilatura_articleContentExtractor import extract_content_sync
from utils.gemini_analyser_async import process_articles_sync
from utils.QnA_extractor import extract_qna_data
import logging
import time
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scraper-score', methods=['POST'])
def scraper_score():
    data = request.get_json()
    company_name = data['companyName']
    time_period = data['timePeriod']
    logger.info("Received data: %s", data)

    start_time = time.time()

    # Fetch news data (RSS links as placeholder)
    gnews_rss_df = news_scraper_RSS_links(company_name, time_period)
    logger.info("Fetched articles - rss links: %s", gnews_rss_df.head())

    gnews_rss_df.to_excel("gnews_scrapped_debug.xlsx", index=False)

    # Resolve the RSS links to actual links
    rss_links = gnews_rss_df["Link"].tolist()
    resolver = GoogleNewsLinkResolver(max_concurrent_tasks=20)
    resolved_links = resolver.resolve_links_sync(rss_links)
    gnews_rss_df["ResolvedLink"] = gnews_rss_df["Link"].map(resolved_links.get)
    
    gnews_rss_df = gnews_rss_df.dropna()
    gnews_rss_df.to_excel("resolved_links_debug.xlsx", index=False)

    logger.info("Fetched articles - resolved links: %s", gnews_rss_df.head())
    logger.info("Resolved links: %s out of %s", gnews_rss_df['ResolvedLink'].notnull().sum(), len(gnews_rss_df))
    logger.info("Link resolver completed in : %s seconds", time.time() - start_time)
    
    article_links = gnews_rss_df["ResolvedLink"].tolist()
    extracted_contents = extract_content_sync(article_links)
    gnews_rss_df["Content"] = gnews_rss_df["ResolvedLink"].map(extracted_contents.get)
    gnews_rss_df = gnews_rss_df.dropna()

    gnews_rss_df.to_excel("trafilatura_debug.xlsx", index=False)

    logger.info("Content extraction completed in : %s seconds", time.time() - start_time)
    
    logger.info("Fetched articles with content: %s", gnews_rss_df.head())

    # Analyse the articles using Gemini API
    analysed_df = process_articles_sync(gnews_rss_df, company_name)

    analysed_df.to_excel("gemini_analysed_debug.xlsx", index=False)    

    logger.info("Analysed articles: %s", analysed_df.head())

    # Extract the QnA data from the analysed df
    QnA_df = extract_qna_data(analysed_df)

    QnA_df.to_excel("QnA_debugging_output.xlsx", index=False)

    # Convert DataFrame to JSON (placeholder for sentiment results)
    analysedData = analysed_df.to_json(orient='records')

    analysed_df.to_excel("gemini_debugging_output.xlsx", index=False)

    # Prepare response
    response = {
        'status': 'success',
        'message': "Sentiment analysis request received successfully",
        'companyName': company_name,
        'data': analysedData
    }

    with open('debugging_response.json', 'w') as f:
        json.dump(response, f)

    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)