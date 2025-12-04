from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import os

app = FastAPI(title="SEOSiri Intelligence API")

origins = [
    "https://seosiri-app-992.web.app",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisRequest(BaseModel):
    domain: str
    competitor_url: str = None
    persona: str

@app.get("/")
def health_check():
    return {"status": "SEOSiri Intelligence Online", "version": "1.6.0 FINAL"}

@app.post("/api/analyze")
def analyze_strategy(
    request: AnalysisRequest, 
    x_gemini_api_key: str = Header(None)
):
    if not x_gemini_api_key:
        raise HTTPException(status_code=401, detail="Missing Gemini API Key in request headers.")

    try:
        genai.configure(api_key=x_gemini_api_key)
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"API Key configuration error: {str(e)}")

    comp_data = "No competitor data provided"
    if request.competitor_url:
        try:
            url_to_scrape = request.competitor_url
            if not url_to_scrape.startswith(('http://', 'https://')):
                url_to_scrape = 'https://' + url_to_scrape
            
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url_to_scrape, headers=headers, timeout=7)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                title = soup.title.string.strip() if soup.title else "No Title Found"
                comp_data = f"Competitor's Page Title: {title}"
        except Exception as e:
            comp_data = f"Could not analyze competitor: {str(e)}"

    prompt = f"""
    Analyze the domain '{request.domain}' for the target persona '{request.persona}'.
    Competitor Context: {comp_data}.
    Provide a JSON response with these keys: "gap_analysis", "hook_strategy", "keyword_opportunity".
    Return ONLY the raw, valid JSON object.
    """
    
    try:
        response = model.generate_content(prompt)
        clean_response = response.text.strip().replace("```json", "").replace("```", "")
        return {"result": clean_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)