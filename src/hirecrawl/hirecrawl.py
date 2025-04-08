import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Streamlit configuration
st.set_page_config(
    page_title="Career Match - LinkedIn to Job Fit Analysis",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

api_key = os.getenv("FIRECRAWL_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

st.warning(f"🚨 Firecrawl API Key = {api_key if api_key else 'NOT FOUND'}")

st.markdown("""
<style>
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
        max-width: 1200px;
        margin: 0 auto;
    }
    h1, h2, h3 {
        color: #2E5090;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #3e8e41;
    }
    .report-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

def make_firecrawl_request(prompt, urls=None):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if not urls:
        st.error("❌ No URL provided for Firecrawl.")
        return None

    data = {
        "url": urls[0],
        "formats": ["json"],
        "jsonOptions": {
            "prompt": prompt.strip()
        }
    }

    st.info("📡 Sending request to Firecrawl...")
    st.code(json.dumps(data, indent=2))  # Optional: shows request data

    try:
        response = requests.post("https://api.firecrawl.dev/v1/scrape", headers=headers, json=data)
        st.code(f"Response status: {response.status_code}")
        if response.status_code == 200:
            return response.json().get("data", {}).get("json", {})
        else:
            st.error(f"API Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"🔥 Exception calling Firecrawl: {e}")
        return None



def analyze_linkedin_profile(linkedin_url):
    prompt = """
    Analyze this LinkedIn profile and extract the following information:
    - Summary
    - Skills
    - Experience
    - Education
    Format as JSON.
    """
    st.info("🔹 Calling Firecrawl API for LinkedIn...")
    result = make_firecrawl_request(prompt, urls=[linkedin_url], crawl_depth=2)
    if result:
        content = result.get("content", "")
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            return json.loads(content[start:end])
        except:
            st.error("Could not parse LinkedIn profile response.")
    return None

def analyze_job_listing(job_url):
    prompt = """
    Analyze this job listing and extract the following:
    - Job Title
    - Company
    - Required Skills
    - Preferred Skills
    Format as JSON.
    """
    st.info("🔹 Calling Firecrawl API for Job Listing...")
    result = make_firecrawl_request(prompt, urls=[job_url], crawl_depth=2)
    if result:
        content = result.get("content", "")
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            return json.loads(content[start:end])
        except:
            st.error("Could not parse job listing response.")
    return None

def generate_pitch(profile_data, job_data):
    prompt = f"""
    You are a career coach. Based on this LinkedIn profile:
    {json.dumps(profile_data)}

    And this job description:
    {json.dumps(job_data)}

    Write a one-paragraph personalized pitch the candidate could use in a cover letter.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful career coach."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"OpenAI error: {e}")
        return None

def display_header():
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/find-matching-job.png", width=80)
    with col2:
        st.title("Career Match")
        st.subheader("LinkedIn to Job Fit Analysis")
    st.markdown("---")

def display_input_form():
    st.subheader("Input Your Information")
    col1, col2 = st.columns(2)
    with col1:
        linkedin_url = st.text_input("LinkedIn Profile URL", placeholder="https://www.linkedin.com/in/your-profile")
    with col2:
        job_url = st.text_input("Job Listing URL", placeholder="https://www.example.com/job-listing")
    analyze_button = st.button("Analyze Match", use_container_width=True)
    return linkedin_url, job_url, analyze_button

def display_report(profile_data, job_data, pitch):
    st.success("✅ Analysis complete! Here's your live match report.")
    st.subheader("🔍 LinkedIn Summary")
    st.json(profile_data)
    st.subheader("📄 Job Listing Summary")
    st.json(job_data)
    if pitch:
        st.subheader("🎤 Suggested Pitch")
        st.markdown(pitch)

def main():
    display_header()
    linkedin_url, job_url, analyze_button = display_input_form()

    if analyze_button and linkedin_url and job_url:
        with st.spinner("Analyzing your profile and the job listing..."):
            try:
                profile_data = analyze_linkedin_profile(linkedin_url)
                if profile_data:
                    st.success("✅ LinkedIn profile loaded.")
                job_data = analyze_job_listing(job_url)
                if job_data:
                    st.success("✅ Job listing loaded.")

                if profile_data and job_data:
                    pitch = generate_pitch(profile_data, job_data)
                    if pitch:
                        st.success("✅ Pitch generated.")
                    display_report(profile_data, job_data, pitch)
                else:
                    st.error("Analysis failed. Please check the URLs and try again.")
            except Exception as e:
                st.error(f"⚠️ Unexpected error: {e}")
    elif analyze_button:
        st.warning("Please provide both a LinkedIn profile URL and a job listing URL.")

    if not analyze_button:
        with st.expander("How to Use This Tool", expanded=True):
            st.markdown("""
            ### 🚀 Career Match: How it Works
            1. **Paste your LinkedIn profile URL**
            2. **Paste a job listing URL**
            3. **Click \"Analyze Match\"**
            4. **Review your AI-generated insights and personalized pitch**
            """)

main()