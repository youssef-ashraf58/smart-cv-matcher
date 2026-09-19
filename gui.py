import streamlit as st
import requests

# Define your FastAPI endpoints
BASE_URL = "http://localhost:8000"
UPLOAD_URL = f"{BASE_URL}/cv/upload"
QUERY_URL = f"{BASE_URL}/query/ask"

st.set_page_config(page_title="Smart CV Matcher", layout="wide")
st.title("📄 Smart CV Matcher")
st.markdown("A RAG-powered system to analyze and match CVs to job requirements (English + Arabic)")

# --- SIDEBAR: CV UPLOAD ---
st.sidebar.header("1. Upload CV")
uploaded_file = st.sidebar.file_uploader("Upload a PDF CV", type=["pdf"])

if st.sidebar.button("Upload & Process"):
    if uploaded_file is not None:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        with st.spinner("Uploading and embedding into ChromaDB..."):
            try:
                response = requests.post(UPLOAD_URL, files=files)
                if response.status_code == 200:
                    st.sidebar.success(f"Successfully processed: {uploaded_file.name}")
                else:
                    st.sidebar.error(f"Upload failed: {response.text}")
            except Exception as e:
                st.sidebar.error(f"Connection error: {e}")
    else:
        st.sidebar.warning("Please select a PDF file first.")

# --- MAIN PAGE: QUERY / MATCHING ---
st.header("2. Match against Job Description")
job_description = st.text_area("Paste the Job Description or ask a specific question about the CV:", height=200)

# Settings matching your backend schema
col1, col2 = st.columns(2)
with col1:
    llm_provider = st.selectbox("LLM Provider", ["gemini", "openai", "local"])
with col2:
    top_k = st.number_input("Top K Chunks", min_value=1, value=5)

if st.button("Analyze & Match"):
    if not job_description:
        st.warning("Please enter a job description or query.")
    elif not uploaded_file:
        st.warning("Please upload a CV in the sidebar first so the system knows which file to query.")
    else:
        with st.spinner("Analyzing match using LLM..."):
            try:
                # Payload exactly matching your Swagger schema
                payload = {
                    "question": job_description,
                    "cv_filename": uploaded_file.name,
                    "top_k": top_k,
                    "llm_provider": llm_provider
                } 
                response = requests.post(QUERY_URL, json=payload)
                
                if response.status_code == 200:
                    st.success("Analysis Complete!")
                    result = response.json()
                    
                    # Display the final answer
                    st.write("### Answer")
                    st.write(result.get("answer", "No answer found."))
                    
                    # Optional: Show retrieved chunks for transparency
                    with st.expander("View Retrieved Chunks"):
                        st.json(result.get("retrieved_chunks", []))
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")