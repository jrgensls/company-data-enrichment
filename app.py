import streamlit as st
import pandas as pd
import requests
import time
import json
import google.genai as genai
from typing import List, Dict, Any, Optional
import re
import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path, override=True)

st.set_page_config(
    page_title="EnrichIQ - Enterprise Intelligence Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

class CompanyDataExtractor:
    def __init__(self):
        self.bright_data_api_key = os.getenv("BRIGHT_DATA_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.dataset_id = os.getenv("DATASET_ID")
        
        # Stop execution if any required API credentials are missing to prevent runtime errors
        if not all([self.bright_data_api_key, self.gemini_api_key, self.dataset_id]):
            st.error("❌ Configuration error: Please check your API keys in the .env file")
            st.stop()
        
        self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        
        self.available_fields = {
            'CEO': 'Who is the current CEO of {company}? Return ONLY the full name in format: FirstName LastName (no titles, no extra text). If no CEO, return "Not found".',
            'Founders': 'Who founded {company}? Return founder name(s) in EXACT format: FirstName LastName, FirstName LastName (comma-separated if multiple, no extra text). Can be 1 or more founders. If no founder info, return "Not found".',
            'Executives': 'List the key executives at {company} in EXACT format: FirstName LastName - JobTitle, FirstName LastName - JobTitle (comma-separated pairs). Include 1-5 executives as available. If no executive info, return "Not found".',
            'LinkedIn URL': 'What is the official LinkedIn company page URL for {company}? Return ONLY the complete URL starting with https://www.linkedin.com/company/ (no extra text). If no LinkedIn page, return "Not found".',
            'Services': 'What are the main services offered by {company}? Return services in format: Service1, Service2, Service3 (comma-separated, no numbers, no extra text). Include 1-5 services as available. If no service info, return "Not found".',
            'Contact Email': 'What is the customer support or contact email for {company}? Return ONLY the email address in format: email@domain.com (no extra text). If no support email, return "Not found".',
            'Headquarters': 'Where is {company} headquartered? Return in EXACT format: City, State/Country (comma-separated, no extra text). If no headquarters info, return "Not found".',
            'News': 'What are the most recent significant business news about {company}? Return in EXACT format: News1, News2, News3 (recent news items, comma-separated, no dates, no extra text). Include 1-5 news items as available. If no recent news, return "Not found".',
            'Funding': 'What recent funding has {company} received? Return in EXACT format: $Amount Series, $Amount Series (e.g., $50M Series B, $25M Series A - comma-separated if multiple). Include 1-3 funding rounds as available. If no funding info, return "Not found".',
            'Investors': 'Who are the main investors in {company}? Return investors in format: Investor1, Investor2, Investor3 (comma-separated, no extra text). Include 1-5 investors as available. If no investor info, return "Not found".',
            'Founded': 'When and where was {company} founded? Return in EXACT format: Year, City (e.g., 2015, San Francisco - no extra text). If no founding info, return "Not found".',
            'Trustpilot Rating': 'What is {company}\'s Trustpilot rating? Return in EXACT format: X.X/Y (e.g., 4.5/1200 - rating out of 5 slash total reviews, no extra text). If no Trustpilot rating, return "Not found".',
            'Open Roles': 'What job categories is {company} hiring for? Return categories in format: Category1, Category2, Category3 (comma-separated, no extra text). Include 1-5 categories as available. If no job postings, return "Not found".',
            'Products': 'What are {company}\'s main products? Return products in format: Product1, Product2, Product3 (comma-separated, no extra text). Include 1-5 products as available. If no product info, return "Not found".'
        }
        
        self.field_formatting_rules = {
            'CEO': {
                'format': 'FirstName LastName',
                'example': 'Sam Altman',
                'rules': 'Single CEO name only, no titles, no extra text',
                'min_items': 1,
                'max_items': 1
            },
            'Founders': {
                'format': 'FirstName LastName, FirstName LastName',
                'example': 'Elon Musk, Martin Eberhard',
                'rules': 'Comma-separated founder names, 1-4 founders acceptable',
                'min_items': 1,
                'max_items': 4
            },
            'Executives': {
                'format': 'FirstName LastName - JobTitle, FirstName LastName - JobTitle',
                'example': 'John Smith - CTO, Jane Doe - VP Engineering',
                'rules': 'Name space dash space title, 1-5 executives acceptable',
                'min_items': 1,
                'max_items': 5
            },
            'LinkedIn URL': {
                'format': 'https://www.linkedin.com/company/companyname',
                'example': 'https://www.linkedin.com/company/openai',
                'rules': 'Single complete LinkedIn company URL only',
                'min_items': 1,
                'max_items': 1
            },
            'Services': {
                'format': 'Service1, Service2, Service3',
                'example': 'AI Research, Language Models, API Services',
                'rules': 'Comma-separated services, 1-5 services acceptable',
                'min_items': 1,
                'max_items': 5
            },
            'Contact Email': {
                'format': 'email@domain.com',
                'example': 'support@openai.com',
                'rules': 'Single email address only',
                'min_items': 1,
                'max_items': 1
            },
            'Headquarters': {
                'format': 'City, State/Country',
                'example': 'San Francisco, CA',
                'rules': 'Single headquarters location only',
                'min_items': 1,
                'max_items': 1
            },
            'News': {
                'format': 'News1, News2, News3',
                'example': 'New AI model launch, Partnership with Microsoft, Series C funding',
                'rules': 'Comma-separated news items, 1-5 items acceptable',
                'min_items': 1,
                'max_items': 5
            },
            'Funding': {
                'format': '$Amount Series, $Amount Series',
                'example': '$50M Series B, $25M Series A',
                'rules': 'Dollar amount and round type, 1-3 rounds acceptable',
                'min_items': 1,
                'max_items': 3
            },
            'Investors': {
                'format': 'Investor1, Investor2, Investor3',
                'example': 'Andreessen Horowitz, Sequoia Capital, Khosla Ventures',
                'rules': 'Comma-separated investor names, 1-5 investors acceptable',
                'min_items': 1,
                'max_items': 5
            },
            'Founded': {
                'format': 'Year, City',
                'example': '2015, San Francisco',
                'rules': 'Single founding year and location',
                'min_items': 1,
                'max_items': 1
            },
            'Trustpilot Rating': {
                'format': 'X.X/Y',
                'example': '4.5/1200',
                'rules': 'Single rating and review count',
                'min_items': 1,
                'max_items': 1
            },
            'Open Roles': {
                'format': 'Category1, Category2, Category3',
                'example': 'Engineering, Sales, Marketing',
                'rules': 'Comma-separated job categories, 1-5 categories acceptable',
                'min_items': 1,
                'max_items': 5
            },
            'Products': {
                'format': 'Product1, Product2, Product3',
                'example': 'ChatGPT, GPT-4, DALL-E',
                'rules': 'Comma-separated product names, 1-5 products acceptable',
                'min_items': 1,
                'max_items': 5
            }
        }

    def extract_single_field(self, companies: List[str], field_name: str) -> Dict[str, str]:
        if field_name not in self.available_fields:
            return {company: "Field not found" for company in companies}
        
        input_array = []
        prompt_template = self.available_fields[field_name]
        
        for company in companies:
            prompt = prompt_template.format(company=company)
            input_array.append({
                "url": "https://google.com/aimode",
                "prompt": prompt,
                "country": ""
            })
        
        request_data = {
            "input": input_array,
            "custom_output_fields": ["answer_text"]
        }
        
        headers = {
            "Authorization": f"Bearer {self.bright_data_api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={self.dataset_id}&include_errors=true"
        
        try:
            # Execute batch API call to Bright Data for web scraping
            response = requests.post(url, headers=headers, json=request_data)
            response.raise_for_status()
            result = response.json()
            snapshot_id = result.get('snapshot_id')
            
            # Handle API response errors with graceful fallback
            if not snapshot_id:
                return {company: "API Error" for company in companies}
            
            # Poll for job completion with timeout protection
            if not self.wait_for_ready(snapshot_id):
                return {company: "Timeout" for company in companies}
            
            # Download and process results with AI formatting
            results = self.download_batch_results(snapshot_id)
            if not results:
                return {company: "No Results" for company in companies}
            
            return self.smart_process_single_field_results(results, companies, field_name)
            
        except Exception as e:
            st.error(f"❌ Data extraction failed: {str(e)}")
            return {company: f"Error: {str(e)}" for company in companies}

    def wait_for_ready(self, snapshot_id: str, max_wait: int = 300) -> bool:
        headers = {"Authorization": f"Bearer {self.bright_data_api_key}"}
        url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                
                progress_data = response.json()
                status = progress_data.get('status', 'unknown')
                
                if status == 'ready':
                    return True
                elif status == 'failed':
                    return False
                
                time.sleep(10)
                
            except Exception:
                time.sleep(10)
        
        return False

    def download_batch_results(self, snapshot_id: str) -> List[Dict]:
        headers = {"Authorization": f"Bearer {self.bright_data_api_key}"}
        url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception:
            return []

    def smart_process_single_field_results(self, results: List[Dict], companies: List[str], field_name: str) -> Dict[str, str]:
        all_raw_data = []
        for i, result in enumerate(results):
            if isinstance(result, dict) and 'answer_text' in result:
                clean_text = result['answer_text'].replace('\n', ' ').strip()
                all_raw_data.append(f"RESULT {i+1}: {clean_text}")
        
        combined_data = "\n\n".join(all_raw_data)
        companies_list = ", ".join(companies)
        
        field_rules = self.field_formatting_rules.get(field_name, {})
        format_example = field_rules.get('format', 'extracted value')
        example_value = field_rules.get('example', 'example value')
        specific_rules = field_rules.get('rules', 'follow standard format')
        min_items = field_rules.get('min_items', 1)
        max_items = field_rules.get('max_items', 5)
        
        json_template = {}
        for company in companies:
            json_template[company] = format_example
        
        # Construct AI prompt with adaptive formatting rules for consistent data extraction
        extraction_prompt = f"""
You are a data extraction expert with ADAPTIVE formatting requirements. Extract {field_name} information for companies.

COMPANIES: {companies_list}
FIELD TO EXTRACT: {field_name}

SEARCH RESULTS:
{combined_data}

ADAPTIVE FORMATTING REQUIREMENTS FOR {field_name}:
- REQUIRED FORMAT: {format_example}
- EXAMPLE OUTPUT: {example_value}
- SPECIFIC RULES: {specific_rules}
- ACCEPTABLE RANGE: {min_items}-{max_items} items (include ALL available items within this range)

Return ONLY a valid JSON object with this EXACT structure:
{json.dumps(json_template, indent=2)}

CRITICAL ADAPTIVE RULES:
- If information not found, use "Not found"
- NEVER force exact counts - adapt to available data
- Include ALL available items within the acceptable range
- Maintain consistent formatting across all companies
- Return ONLY valid JSON, nothing else
"""
        
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=[{'parts': [{'text': extraction_prompt}]}]
            )
            
            if (response and 
                response.candidates and 
                len(response.candidates) > 0 and
                response.candidates[0].content and
                response.candidates[0].content.parts and
                len(response.candidates[0].content.parts) > 0):
                
                gemini_response = response.candidates[0].content.parts[0].text
                
                if gemini_response:
                    gemini_response = gemini_response.strip()
                else:
                    gemini_response = ""
                
                if gemini_response.startswith('```json'):
                    gemini_response = gemini_response.replace('```json', '').replace('```', '').strip()
                elif gemini_response.startswith('```'):
                    gemini_response = gemini_response.replace('```', '').strip()
                
                try:
                    parsed_data = json.loads(gemini_response)
                    
                    company_data = {}
                    for company in companies:
                        if (company in parsed_data and 
                            isinstance(parsed_data[company], str)):
                            value = parsed_data[company].strip()
                            
                            value = self.enforce_field_formatting(value, field_name)
                            
                            company_data[company] = value if value else "Not found"
                        else:
                            company_data[company] = "Not found"
                    
                    return company_data
                    
                except json.JSONDecodeError:
                    return self.fallback_single_field_processing(results, companies, field_name)
            
            return self.fallback_single_field_processing(results, companies, field_name)
            
        except Exception:
            return self.fallback_single_field_processing(results, companies, field_name)

    def enforce_field_formatting(self, value: str, field_name: str) -> str:
        if not value or value.lower() in ['not found', 'n/a', 'na', 'none', '', 'null']:
            return "Not found"
        
        value = value.strip()
        
        if field_name == 'CEO':
            # Remove titles and parenthetical info, extract clean name
            value = re.sub(r'\b(CEO|Chief Executive Officer|Mr\.|Ms\.|Dr\.|President)\s*', '', value, flags=re.IGNORECASE)
            value = re.sub(r'\s*\(.*?\)', '', value)
            value = value.strip()
            parts = value.split()
            if len(parts) >= 2:
                return ' '.join(parts[:3])
            return value if value else "Not found"
        
        elif field_name in ['Founders', 'Services', 'Investors', 'News', 'Open Roles', 'Products']:
            value = re.sub(r'\s*and\s*', ', ', value)
            value = re.sub(r'\s*&\s*', ', ', value)
            parts = [part.strip() for part in value.split(',')]
            clean_parts = [part for part in parts if part and len(part) > 2]
            if clean_parts:
                return ', '.join(clean_parts[:5])
            return "Not found"
        
        elif field_name == 'LinkedIn URL':
            # Extract and normalize LinkedIn company URLs
            linkedin_pattern = r'(https?://)?(?:www\.)?linkedin\.com/company/[^\s,)]*'
            match = re.search(linkedin_pattern, value, re.IGNORECASE)
            if match:
                url = match.group(0)
                if not url.startswith('https://'):
                    url = 'https://' + url.lstrip('http://')
                return url.rstrip('/')
            return "Not found"
        
        elif field_name == 'Contact Email':
            # Extract valid email addresses using RFC-compliant regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            match = re.search(email_pattern, value)
            if match:
                return match.group(0).lower()
            return "Not found"
        
        return ' '.join(value.split()) if value else "Not found"

    def fallback_single_field_processing(self, results: List[Dict], companies: List[str], field_name: Optional[str] = None) -> Dict[str, str]:
        company_data = {}
        
        for i, company in enumerate(companies):
            if i < len(results):
                result = results[i]
                if isinstance(result, dict) and 'answer_text' in result:
                    answer_text = result['answer_text']
                    processed = answer_text.strip() if answer_text else "Not found"
                    processed = ' '.join(processed.split())
                    
                    if field_name:
                        processed = self.enforce_field_formatting(processed, field_name)
                    
                    company_data[company] = processed if processed else "Not found"
                else:
                    company_data[company] = "Not found"
            else:
                company_data[company] = "Not found"
        
        return company_data


def get_extractor():
    return CompanyDataExtractor()

def main():
    st.markdown("""
    <style>
    /* Main layout and data table */
    .main .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0.8rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1200px;
    }
    .stDataFrame { border: none; }
    .stDataFrame > div {
        border: 1px solid #e1e5e9;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* File uploader customization */
    .stFileUploader {
        max-width: 220px;
    }
    
    .stFileUploader small,
    .stFileUploader div small,
    .stFileUploader * small,
    .stFileUploader section small,
    .stFileUploader [data-testid="stFileUploaderDropzone"] small {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Hide the drag drop text limit info */
    .stFileUploader section::after {
        content: "" !important;
    }
    
    .stFileUploader [data-testid="stFileUploaderDropzoneInstructions"] {
        display: none !important;
    }
    
    /* Upload container */
    .stFileUploader > div {
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%) !important;
        padding: 0.7rem 0.5rem !important;
        text-align: center !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 12px !important;
        min-height: 60px !important;
    }
    
    .stFileUploader > div:hover {
        border-color: #4A90E2 !important;
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f2ff 100%) !important;
        box-shadow: 0 4px 8px rgba(74, 144, 226, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Upload button text */
    .stFileUploader label {
        font-size: 0.85rem !important;
        color: #4A90E2 !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        margin: 0 !important;
        letter-spacing: 0.3px !important;
    }
    
    /* Drag area */
    .stFileUploader section {
        min-height: 18px !important;
        padding: 0.15rem !important;
        font-size: 0.65rem !important;
        color: #6b7280 !important;
        border: none !important;
        background: transparent !important;
    }
    
    .main h3 {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        margin-top: 1.5rem;
    }
    
    .stInfo {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .element-container {
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 15px;">
        <h1 style="font-size: 2.5rem; font-weight: 700; margin-bottom: 3px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🧠 EnrichIQ
        </h1>
        <p style="font-size: 1rem; color: #666; margin-bottom: 3px;">Company data enrichment platform</p>
        <p style="font-size: 0.85rem; color: #888; margin-bottom: 5px;">
            Powered by <a href="http://brightdata.com/" target="_blank" style="color: #4A90E2; text-decoration: none;">Bright Data</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'csv_processed_count' not in st.session_state:
        st.session_state.csv_processed_count = 0
    
    
    st.markdown("""
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    
    .info-icon {
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 1px solid #4A90E2;
        background-color: transparent;
        color: #4A90E2;
        font-size: 11px;
        font-weight: bold;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: Arial, sans-serif;
    }
    
    .info-icon:hover {
        border-color: #357ABD;
        color: #357ABD;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 280px;
        background-color: #333;
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -140px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 12px;
    }
    
    .tooltip .tooltiptext::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #333 transparent transparent transparent;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    upload_col, icon_col = st.columns([4, 1])
    
    with upload_col:
        uploaded_file = st.file_uploader(
            "Ingest Entity Database", 
            type=['csv'],
            key=f"csv_uploader_{st.session_state.csv_processed_count}",
            label_visibility="collapsed"
        )
    
    with icon_col:
        st.markdown(
            '<div style="margin-top: 12px; text-align: center;">'
            '<div class="tooltip">'
            '<div class="info-icon">i</div>'
            '<span class="tooltiptext">Upload CSV with "Company Name" column</span>'
            '</div>'
            '</div>', 
            unsafe_allow_html=True
        )
    
    
    extractor = get_extractor()
    
    if 'companies_data' not in st.session_state:
        st.session_state.companies_data = pd.DataFrame({
            'Company': [''] * 10,
            **{field: [''] * 10 for field in extractor.available_fields.keys()}
        })
        st.session_state.companies_data['Company'] = st.session_state.companies_data['Company'].astype(str)
    
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_csv(uploaded_file)
            
            company_col = None
            for col in uploaded_df.columns:
                if col.strip().lower() == 'company name':
                    company_col = col
                    break
            
            if company_col is None:
                available_cols = ", ".join(uploaded_df.columns.tolist())
                st.error(f"❌ CSV must have 'Company Name' column header. Available columns: {available_cols}")
            else:
                company_names = uploaded_df[company_col].dropna().astype(str).str.strip()
                company_names = company_names[company_names != ''].tolist()
                
                if company_names:
                    st.session_state.companies_data = pd.DataFrame({
                        'Company': company_names,
                        **{field: [''] * len(company_names) for field in extractor.available_fields.keys()}
                    })
                    
                    st.success(f"✅ Successfully loaded {len(company_names)} companies ready for enrichment")
                    
                    st.session_state.csv_processed_count += 1
                    st.rerun()
                else:
                    st.error("❌ No company names found in your CSV file")
                
        except Exception as e:
            st.error(f"❌ Could not read CSV file: {str(e)}")
    
    column_config = {
        "Company": st.column_config.TextColumn(
            "Company Name",
            help="Input organizational identifiers for strategic intelligence acquisition (one per row)",
            width="medium",
            required=False,
            disabled=False
        )
    }
    
    professional_tooltips = {
        'CEO': 'Find the current CEO name',
        'Founders': 'Get company founder information',
        'Executives': 'Key leadership team members', 
        'LinkedIn URL': 'Company LinkedIn profile link',
        'Services': 'What services the company offers',
        'Contact Email': 'Main customer support email',
        'Headquarters': 'Company main office location',
        'News': 'Recent company news and updates',
        'Funding': 'Investment and funding history',
        'Investors': 'Key investors and venture capital firms',
        'Founded': 'When and where the company was founded',
        'Trustpilot Rating': 'Customer review score and rating',
        'Open Roles': 'Current job openings and hiring',
        'Products': 'Main products and offerings'
    }
    
    for field_name in extractor.available_fields.keys():
        column_config[field_name] = st.column_config.TextColumn(
            field_name,
            help=professional_tooltips.get(field_name, f"Company {field_name.lower()}"),
            disabled=True
        )

    # Fix for Streamlit data_editor double-typing bug using direct comparison
    edited_df = st.data_editor(
        st.session_state.companies_data,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=350,
        num_rows="dynamic",
        key="data_editor_key"
    )
    
    if not edited_df.equals(st.session_state.companies_data):
        # Critical fix: Preserve all field columns when manual typing updates DataFrame
        # This prevents button processing failures due to missing columns
        updated_data = edited_df.copy()
        
        for field in extractor.available_fields.keys():
            if field not in updated_data.columns:
                updated_data[field] = [''] * len(updated_data)
        
        st.session_state.companies_data = updated_data
        st.rerun()

    st.markdown('<p style="font-size: 1.1rem; font-weight: 600; margin: 15px 0 8px 0; color: #2c3e50;">Data Fields</p>', unsafe_allow_html=True)
    
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False
        
    if 'current_processing_field' not in st.session_state:
        st.session_state.current_processing_field = None
        
    if 'processing_step' not in st.session_state:
        st.session_state.processing_step = 'idle'  # State machine: idle -> starting -> api_call -> updating -> completed
        
    if 'processing_data' not in st.session_state:
        st.session_state.processing_data = None
        
    status_area = st.container()
    
    # Performance optimization: Only calculate valid companies during active processing
    if st.session_state.is_processing and st.session_state.current_processing_field:
        valid_companies = st.session_state.companies_data[
            (st.session_state.companies_data['Company'].str.strip() != '') & 
            (st.session_state.companies_data['Company'].notna())
        ]['Company'].str.strip().tolist()
        
        if valid_companies:
            field_name = st.session_state.current_processing_field
            
            status_placeholder = status_area.empty()
            progress_placeholder = status_area.empty() 
            details_placeholder = status_area.empty()
            
            # State machine implementation for step-by-step processing UI
            if st.session_state.processing_step == 'starting':
                status_placeholder.markdown(f"⚙️ **Starting {field_name} enrichment...**")
                progress_placeholder.progress(25)
                details_placeholder.markdown("*Initializing extraction process...*")
                
                st.session_state.processing_step = 'api_call'
                time.sleep(0.5)  # Minimal delay for UI update
                st.rerun()
                
            elif st.session_state.processing_step == 'api_call':
                status_placeholder.markdown(f"🌐 **Extracting {field_name} data...**")
                progress_placeholder.progress(50)
                details_placeholder.markdown(f"*Analyzing {len(valid_companies)} companies...*")
                
                # Core data extraction: Bright Data API + AI processing
                extractor = get_extractor()
                field_data = extractor.extract_single_field(valid_companies, field_name)
                
                st.session_state.processing_data = field_data
                st.session_state.processing_step = 'updating'
                st.rerun()
                
            elif st.session_state.processing_step == 'updating':
                status_placeholder.markdown(f"📊 **Updating {field_name} results...**")
                progress_placeholder.progress(75)
                
                field_data = st.session_state.processing_data
                processed_count = 0
                
                # Update DataFrame with extracted data using company name matching
                if field_data:
                    for company, value in field_data.items():
                        mask = st.session_state.companies_data['Company'].str.strip() == company.strip()
                        if mask.any():
                            st.session_state.companies_data.loc[mask, field_name] = value
                            processed_count += 1
                
                details_placeholder.markdown(f"*Updated {processed_count} companies*")
                
                st.session_state.processing_step = 'completed'
                st.rerun()
                
            elif st.session_state.processing_step == 'completed':
                status_placeholder.markdown(f"✅ **{field_name} enrichment completed!**")
                progress_placeholder.progress(100)
                
                processed_count = len([v for v in st.session_state.processing_data.values() if v != "Not found"]) if st.session_state.processing_data else 0
                details_placeholder.markdown(f"*Successfully enriched {processed_count} companies*")
                
                time.sleep(2)
                
                # Reset all processing state variables
                status_placeholder.empty()
                progress_placeholder.empty() 
                details_placeholder.empty()
                
                st.session_state.is_processing = False
                st.session_state.current_processing_field = None
                st.session_state.processing_step = 'idle'
                st.session_state.processing_data = None
                
                st.rerun()
            
    if not st.session_state.is_processing:
        status_placeholder = status_area.empty()
        progress_placeholder = status_area.empty() 
        details_placeholder = status_area.empty()
        
        # Performance optimization: Cache company validation to prevent excessive DataFrame ops
        if 'cached_valid_companies' not in st.session_state:
            st.session_state.cached_valid_companies = st.session_state.companies_data[
                (st.session_state.companies_data['Company'].str.strip() != '') & 
                (st.session_state.companies_data['Company'].notna())
            ]['Company'].str.strip().tolist()
            # Cache will be updated when companies_data changes
        
        if not st.session_state.cached_valid_companies:
            status_placeholder.info("🏢 **Add company names to begin enrichment**")
    
    st.markdown("""
    <style>
    /* Compact button styling */
    .stButton > button {
        background: linear-gradient(90deg, #4A90E2, #5BA0F2);
        color: white; border: none; border-radius: 5px; font-weight: 500;
        transition: all 0.2s ease; height: 1.4rem !important; font-size: 11px !important;
        padding: 0.08rem 0.2rem !important; margin: 0.02rem !important;
        min-width: 85px !important; max-width: 120px !important; width: auto !important;
        white-space: nowrap !important; text-overflow: ellipsis !important; overflow: hidden !important;
        line-height: 1.1 !important; display: inline-flex !important; align-items: center !important;
        justify-content: center !important; box-sizing: border-box !important;
    }
    
    /* Font size overrides */
    div.stButton > button, .stApp .stButton > button, button[kind="primary"],
    [data-testid="stButton"] button, .stButton button, button, .stApp button,
    div button, button[kind="secondary"], * button, button * {
        font-size: 11px !important; height: 1.4rem !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #357ABD, #4A90E2);
        transform: translateY(-1px); box-shadow: 0 3px 6px rgba(74, 144, 226, 0.25);
    }
    
    /* Compact layout spacing */
    .stButton { margin-bottom: 0.05rem !important; margin-top: 0.02rem !important; }
    div[data-testid="column"] { padding: 0.02rem !important; margin: 0 !important; }
    .element-container { margin-bottom: 0.1rem !important; }
    
    /* Button grid layout */
    .row-widget.stHorizontal { gap: 0 !important; display: flex !important; justify-content: flex-start !important; flex-wrap: wrap !important; }
    .row-widget.stHorizontal > div { padding: 0.02rem !important; margin: 0 !important; flex: 0 0 auto !important; width: auto !important; min-width: 90px !important; max-width: 120px !important; }
    div[data-testid="column"] { padding: 0.02rem !important; margin: 0 !important; flex: 0 0 auto !important; width: auto !important; }
    div[data-testid="column"] > div { padding: 0 !important; margin: 0 !important; width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)
    
    field_names = list(extractor.available_fields.keys())
    
    cols_per_row = 8
    button_cols = st.columns([1] * cols_per_row)
        
    for i, field_name in enumerate(field_names):
        col_index = i % cols_per_row
        with button_cols[col_index]:
            button_text = field_name
            button_key = f"enrich_{field_name.replace(' ', '_').lower()}"
            
            # Button state logic: current processing, other processing, or available
            is_current_processing = (st.session_state.is_processing and 
                                   st.session_state.current_processing_field == field_name)
            is_other_processing = (st.session_state.is_processing and 
                                 st.session_state.current_processing_field != field_name)
                
            if is_current_processing:
                st.button(f"⚙️ {button_text}", key=button_key, disabled=True, help=f"Currently processing {field_name}")
                button_clicked = False
            elif is_other_processing:
                st.button(button_text, key=button_key, disabled=True, help="Another field is currently processing")
                button_clicked = False
            else:
                button_clicked = st.button(button_text, key=button_key, help=professional_tooltips.get(field_name, f"Find {field_name.lower()} information"))
                
            if button_clicked and not st.session_state.is_processing:
                valid_companies = st.session_state.companies_data[
                    (st.session_state.companies_data['Company'].str.strip() != '') & 
                    (st.session_state.companies_data['Company'].notna())
                ]['Company'].str.strip().tolist()
                
                if valid_companies:
                    # Initialize processing state machine
                    st.session_state.is_processing = True
                    st.session_state.current_processing_field = field_name
                    st.session_state.processing_step = 'starting'
                    
                    st.rerun()


if __name__ == "__main__":
    main()
