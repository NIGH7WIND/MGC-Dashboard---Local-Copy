from flask import Flask, render_template, request, jsonify, send_file
from utils.gnews_scraper import news_scraper_RSS_links
from utils.playwright_rssLinksResolver_optimized import GoogleNewsLinkResolverOptimized
from utils.articleContentExtractor import extract_content_sync
from utils.gemini_analyser_async import process_articles_sync
from utils.QnA_extractor import extract_qna_data, convert_df_to_json
from utils.gemini_reportGen import generate_financial_report
from utils.markdown2htmlreport import markdown_to_html
import pandas as pd
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
    resolver = GoogleNewsLinkResolverOptimized(max_pages=20)
    resolved_links = resolver.resolve_links_sync(rss_links)
    gnews_rss_df["ResolvedLink"] = gnews_rss_df["Link"].map(resolved_links.get)

    gnews_rss_df = gnews_rss_df.dropna()
    gnews_rss_df.to_excel("resolved_links_debug.xlsx", index=False)

    logger.info("Fetched articles - resolved links: %s", gnews_rss_df.head())
    logger.info("Resolved links: %s out of %s", gnews_rss_df['ResolvedLink'].notnull().sum(), len(gnews_rss_df))
    logger.info("Link resolver completed in : %s seconds", time.time() - start_time)

    # Extract content
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

    logger.info("Analysis completed in : %s seconds", time.time() - start_time)

    # Convert DataFrame to JSON for response
    analysedData = analysed_df.to_json(orient='records')

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

@app.route('/generate-report', methods=['POST'])
def generate_report():
    data = request.get_json()
    company_name = data['companyName']
    analysedData = data['analysedData']  # Get the analysed data directly

    logger.info("Generating report for company: %s", company_name)

    start_time = time.time()

    # Convert the list of JSON objects into a pandas DataFrame
    try:
        # Use json_normalize if the data structure requires flattening
        analysed_df = pd.json_normalize(analysedData)
    except Exception as e:
        logger.error("Error converting analysedData to DataFrame: %s", e)
        return jsonify({"error": "Error processing data", "message": str(e)}), 500

    logger.info("Analyzed data converted to DataFrame")

    # Extract QnA data
    QnA_df = extract_qna_data(analysed_df)
    logger.info("QnA df: %s", QnA_df.head())

    QnA_df.to_excel("QnA_debugging_output.xlsx", index=False)

    # Convert QnA data to JSON
    reportGen_input = convert_df_to_json(QnA_df)
    with open('reportGen_input_debug.txt', 'w') as f:
        f.write(reportGen_input)

    logger.info("ReportGen input: %s", reportGen_input[:100] + "...")

    logger.info("Generating report for: %s", company_name)
    
    # Extract the financial report in markdown format
    financial_report = generate_financial_report(company_name, reportGen_input)

    with open('financial_report_debug.txt', 'w', encoding="utf-8") as f:
        f.write(financial_report)

    # Convert the markdown into html format
    html_report = markdown_to_html(financial_report)

    # Save the HTML output to a file
    output_path = "financial_report.html"
    with open(output_path, "w", encoding="utf-8") as html_file:
        html_file.write(html_report)

    logger.info("Report generated in %.2f seconds", time.time() - start_time)

    # Send the HTML file to the frontend for download
    return send_file(output_path, as_attachment=True, download_name=f"{company_name}_financial_report.html", mimetype='text/html')


if __name__ == "__main__":
    app.run(debug=True)