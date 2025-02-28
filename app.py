from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import logging
import time
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
import agentops
from pydantic import BaseModel, Field
from typing import List
from tavily import TavilyClient
from scrapegraph_py import Client

# Initialize Flask application
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AGENTOPS_API_KEY = os.getenv("AGENTOPS_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
SCRAPEGRAPH_API_KEY = os.getenv("SCRAPEGRAPH_API_KEY")

# Initialize AgentOps with API key
agentops.init(api_key=AGENTOPS_API_KEY, skip_auto_end_session=True)

# Set output directories
output_dir = "./ai-agent-output"
reports_dir = os.path.join(output_dir, "reports")
os.makedirs(reports_dir, exist_ok=True)

# Initialize LLM with model and temperature
basic_llm = LLM(model="gpt-4o", temperature=0)

# Initialize free clients (Tavily and Scrapegraph)
search_client = TavilyClient(api_key=TAVILY_API_KEY)
scrape_client = Client(api_key=SCRAPEGRAPH_API_KEY)

# Define number of keywords and company context
no_keywords = 10
about_company = "SIA is a company that provides AI solutions to help websites refine their search and recommendation systems."
company_context = StringKnowledgeSource(content=about_company)

def retry_api_call(func, max_retries=3, delay=1, backoff=2):
    """
    Retry function for API calls.
    Tries the provided function up to max_retries times with exponential backoff.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed with error: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= backoff
            else:
                raise

# Pydantic data models
class SuggestedSearchQueries(BaseModel):
    queries: List[str] = Field(..., title="Suggested search queries", min_items=1, max_items=no_keywords)

class SignleSearchResult(BaseModel):
    title: str
    url: str = Field(..., title="Page URL")
    content: str
    score: float
    search_query: str

class AllSearchResults(BaseModel):
    results: List[SignleSearchResult]

class ProductSpec(BaseModel):
    specification_name: str
    specification_value: str

class SingleExtractedProduct(BaseModel):
    page_url: str = Field(..., title="The original url of the product page")
    product_title: str = Field(..., title="The title of the product")
    product_image_url: str = Field(..., title="The url of the product image")
    product_url: str = Field(..., title="The url of the product")
    product_current_price: float = Field(..., title="The current price of the product")
    product_original_price: float = Field(title="The original price of the product before discount. Set to None if no discount", default=None)
    product_discount_percentage: float = Field(title="The discount percentage of the product. Set to None if no discount", default=None)

    product_specs: List[ProductSpec] = Field(..., title="The specifications of the product. Focus on the most important specs to compare.", min_items=1, max_items=5)

    agent_recommendation_rank: int = Field(..., title="The rank of the product to be considered in the final procurement report. (out of 5, Higher is Better) in the recommendation list ordering from the best to the worst")
    agent_recommendation_notes: List[str]  = Field(..., title="A set of notes why would you recommend or not recommend this product to the company, compared to other products.")


class AllExtractedProducts(BaseModel):
    products: List[SingleExtractedProduct]

# Agent: Search Queries Recommendation
search_queries_recommendation_agent = Agent(
    role="Search Queries Recommendation Agent",
    goal="\n".join([
                "To provide a list of suggested search queries to be passed to the search engine.",
                "The queries must be varied and looking for specific items."
            ]),
    backstory="The agent is designed to help in looking for products by providing a list of suggested search queries to be passed to the search engine based on the context provided.",
    llm=basic_llm,
    verbose=True,
)

search_queries_recommendation_task = Task(
    description="\n".join([
        "SIA is looking to buy {product_name} at the best prices (value for a price strategy)",
        "The campany target any of these websites to buy from: {websites_list}",
        "The company wants to reach all available proucts on the internet to be compared later in another stage.",
        "The stores must sell the product in {country_name}",
        "Generate at maximum {no_keywords} queries.",
        "The search keywords must be in {language} language.",
        "Search keywords must contains specific brands, types or technologies. Avoid general keywords.",
        "The search query must reach an ecommerce webpage for product, and not a blog or listing page."
    ]),
    expected_output="A JSON object containing a list of suggested search queries.",
    output_file=os.path.join(output_dir, "step_1_suggested_search_queries.json"),
    agent=search_queries_recommendation_agent,
    output_json=SuggestedSearchQueries,
)

# Agent: Search Engine
@tool
def search_engine_tool(query: str):
    """Useful for search-based queries. Use this to find current information about any query related pages using a search engine"""
    return retry_api_call(lambda: search_client.search(query))

search_engine_agent = Agent(
    role="Search Engine Agent",
    goal="Search for products based on the suggested search queries.",
    backstory="The agent is designed to help in looking for products by searching for products based on the suggested search queries.",
    llm=basic_llm,
    verbose=True,
    tools=[search_engine_tool]
)

search_engine_task = Task(
    description="\n".join([
        "The task is to search for products based on the suggested search queries.",
        "You have to collect results from multiple search queries.",
        "Ignore any susbicious links or not an ecommerce single product website link.",
        "Ignore any search results with confidence score less than ({score_th}) .",
        "The search results will be used to compare prices of products from different websites.",
    ]),
    expected_output="A JSON object containing search results.",
    output_file=os.path.join(output_dir, "step_2_search_results.json"),
    agent=search_engine_agent,
    output_json=AllSearchResults,
)

# Agent: Web Scraping
@tool
def web_scraping_tool(page_url: str):
    """
    An AI Tool to help an agent to scrape a web page
    Example:
    web_scraping_tool(
        page_url="https://www.noon.com/uae-en/front-load-washing-machine-with-quick-wash-drum-clean-and-delay-end-ww70t3020bs-silver/N53074306A/p/?o=db63bc42482cde4e"
    )
    """
    def call_scrape():
        return scrape_client.smartscraper(
            website_url=page_url,
            user_prompt="Extract ```json\n" + SingleExtractedProduct.schema_json() + "```\nFrom the web page"
        )
    try:
        result = retry_api_call(call_scrape)
        return {"page_url": page_url, "details": result}
    except Exception as e:
        logger.error(f"Web scraping failed for {page_url} with error: {e}")
        # Return a fallback result if scraping fails
        return {"page_url": page_url, "details": None}

scraping_agent = Agent(
    role="Web Scraping Agent",
    goal="To extract details from any website.",
    backstory="The agent is designed to help in looking for required values from any website url. These details will be used to decide which best product to buy.",
    llm=basic_llm,
    tools=[web_scraping_tool],
    verbose=True,
)

scraping_task = Task(
    description="\n".join([
        "The task is to extract product details from any ecommerce store page url.",
        "The task has to collect results from multiple pages urls.",
        "Collect the best {top_recommendations_no} products from the search results."
    ]),
    expected_output="A JSON object containing extracted product details.",
    output_file=os.path.join(output_dir, "step_3_extracted_products.json"),
    agent=scraping_agent,
    output_json=AllExtractedProducts,
)

# Agent: Procurement Report Author
procurement_report_author_agent = Agent(
    role="Procurement Report Author Agent",
    goal="To generate a professional HTML page for the procurement report.",
    backstory="The agent is designed to assist in generating a professional HTML page for the procurement report after looking into a list of products.",
    llm=basic_llm,
    verbose=True,
)

procurement_report_author_task = Task(
    description="\n".join([
        "The task is to generate a professional HTML page for the procurement report.",
        "You have to use Bootstrap CSS framework for a better UI.",
        "Use the provided context about the company to make a specialized report.",
        "The report will include the search results and prices of products from different websites.",
        "The report should be structured with the following sections:",
        "1. Executive Summary: A brief overview of the procurement process and key findings.",
        "2. Introduction: An introduction to the purpose and scope of the report.",
        "3. Methodology: A description of the methods used to gather and compare prices.",
        "4. Findings: Detailed comparison of prices from different websites, including tables and charts.",
        "5. Analysis: An analysis of the findings, highlighting any significant trends or observations.",
        "6. Recommendations: Suggestions for procurement based on the analysis.",
        "7. Conclusion: A summary of the report and final thoughts.",
        "8. Appendices: Any additional information, such as raw data or supplementary materials.",
    ]),
    expected_output="A JSON object containing the report URL.",
    output_file=os.path.join(reports_dir, "procurement_report.html"),
    agent=procurement_report_author_agent,
)

# Crew Workflow
SIA_crew = Crew(
    agents=[
        search_queries_recommendation_agent,
        search_engine_agent,
        scraping_agent,
        procurement_report_author_agent,
    ],
    tasks=[
        search_queries_recommendation_task,
        search_engine_task,
        scraping_task,
        procurement_report_author_task,
    ],
    process=Process.sequential,
    knowledge_sources=[company_context]
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    try:
        data = request.json
        product_name = data.get('productName')
        country = data.get('country')
        result_count = data.get('resultCount')
        websites = data.get('websites', [
            "www.amazon.com", "www.ebay.com", "www.aliexpress.com",
            "www.walmart.com", "www.bestbuy.com", "www.newegg.com",
            "www.target.com", "www.jumia.com", "www.noon.com", "www.etsy.com"
        ])

        if not product_name or not country or not result_count:
            return jsonify({"status": "error", "message": "All fields are required"}), 400

        # Execute the Crew Workflow
        SIA_crew.kickoff(
            inputs={
                "product_name": product_name,
                "websites_list": websites,
                "country_name": country,
                "no_keywords": no_keywords,
                "language": "English",
                "score_th": 0.10,
                "top_recommendations_no": result_count
            }
        )

        # Check for the report
        report_path = os.path.join(reports_dir, "procurement_report.html")
        if not os.path.exists(report_path):
            return jsonify({"status": "error", "message": "Procurement report not found"}), 500

        return jsonify({
            "status": "success",
            "message": "Report generated successfully",
            "report_url": f"/reports/{os.path.basename(report_path)}"
        })

    except Exception as e:
        logger.error(f"Error during search: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reports/<path:filename>')
def serve_report(filename):
    return send_from_directory(reports_dir, filename)

# Note: For production, use a production WSGI server (Gunicorn, uWSGI, etc.)
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
