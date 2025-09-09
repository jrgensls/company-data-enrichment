<p align="center">
  <a href="https://brightdata.com/">
    <img src="https://mintlify.s3.us-west-1.amazonaws.com/brightdata/logo/light.svg" width="300" alt="Bright Data Logo">
  </a>
</p>

# Company Data Enrichment Tool 🏢

**Instantly enrich company lists with actionable business data using [Bright Data Web Scraper API](https://brightdata.com/products/web-scraper), Google Gemini AI, and Streamlit. Perfect for lead generation, market research, or competitor analysis. Just upload your CSV—get CEO, funding, products, and more in minutes.**

<div align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue"/>
  <img src="https://img.shields.io/badge/License-MIT-blue"/>
</div>

---

https://github.com/user-attachments/assets/4d25c7e3-18c1-4c92-9521-848d03ec9443

## Features 🚀
- **Automated enrichment**. Collect 13+ data points per company, including CEO, funding, and products.
- **CSV upload**. Process multiple company records in a single upload.
- **Progress tracking**. Monitor enrichment progress as the tool processes data.
- **User-friendly interface**. Clean, professional dashboard for easy data access.

## End-to-end workflow 🔄
1. **User input**. Upload a CSV with company names via the [Streamlit](https://streamlit.io/) interface.
2. **Data preparation**. [Pandas](https://pandas.pydata.org/) checks for valid company names and removes duplicates.
3. **Web scraping**. [Requests](https://requests.readthedocs.io/en/latest/) send data to the [Bright Data Web Scraper API](https://brightdata.com/products/web-scraper). Bright Data scrapes web sources for company information.
4. **AI processing**. [Google Gemini AI](https://ai.google.dev/) standardizes formats and removes inconsistencies.
5. **Results display**. Enriched data appears in an interactive Streamlit table. Download results or continue enriching more fields.

## Data fields ℹ️
Each company record may include, based on public data availability:
- **Leadership**. CEO, Founders, Executives.
- **Company Info**. LinkedIn URL, Services, Contact Email, Headquarters, and Founded.
- **Financials**. Funding, Investors, Trustpilot Rating (if available).
- **Updates**. News, Products, Open Roles (if listed).

## Prerequisites 🛠️
- [Python 3.9+](https://python.org/) 🐍
- [Bright Data API key](https://docs.brightdata.com/api-reference/authentication#how-do-i-generate-a-new-api-key%3F) 🔑
- [Google Gemini API key](https://aistudio.google.com/apikey) 🔑

## Quick start ⚙️

### Step 1 – clone the repository
```bash
git clone https://github.com/triposat/ai-company-enrichment.git
```

### Step 2 – navigate to the folder
```bash
cd ai-company-enrichment
```

### Step 3 – create and activate a virtual environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### Step 4 – install dependencies
```bash
pip install -r requirements.txt
```

### Step 5 – create a `.env` file with
```bash
BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
DATASET_ID=your_dataset_id_here
```

### Step 6 – run the app
```bash
streamlit run app.py
```

### Step 7
Upload a CSV with a “Company Name” column and select fields to enrich.

## Next steps
To master AI data enrichment, leverage Bright Data’s powerful tools and support:
- Power your AI models with advanced [Web Access APIs](https://brightdata.com/ai/web-access) for seamless data access.
- Explore the [ultimate MCP tool](https://brightdata.com/ai/mcp-server) to connect your AI to the web and enjoy 5,000 MCP requests every month for free.
- Use [pre-collected datasets](https://brightdata.com/products/datasets) with billions of records for high-quality data.
- Integrate with AI platforms like n8n and CrewAI to [connect and build AI agents](https://docs.brightdata.com/integrations/ai-integrations).
- Learn more about AI data solutions in Bright Data’s [blogs page](https://brightdata.com/blog).

For expert guidance, [contact Bright Data’s support team](https://brightdata.com/contact).
