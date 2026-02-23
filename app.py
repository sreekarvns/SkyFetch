import streamlit as st
import requests
import json
from fpdf import FPDF
from phi.agent import Agent
from phi.model.ollama import Ollama
import os
from dotenv import load_dotenv

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="SkyFetch - AI Weather System",
    page_icon="🌤️",
    layout="centered"
)

# Enhanced Custom CSS for modern, aesthetic design
custom_css = """
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Global styling */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Hero title styling */
    .hero-title {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #7c3aed, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { filter: drop-shadow(0 0 5px rgba(0, 212, 255, 0.3)); }
        to { filter: drop-shadow(0 0 20px rgba(124, 58, 237, 0.5)); }
    }
    
    .hero-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #94a3b8;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    /* Agent step indicators */
    .agent-step {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .step-active {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        color: white;
        animation: pulse 1.5s infinite;
    }
    
    .step-complete {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
    }
    
    .step-pending {
        background: rgba(255, 255, 255, 0.1);
        color: #94a3b8;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.02); opacity: 0.9; }
    }
    
    /* Weather summary card */
    .weather-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1), rgba(124, 58, 237, 0.1));
        border-radius: 20px;
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 2rem;
        margin: 1.5rem 0;
    }
    
    .weather-card h3 {
        color: #00d4ff;
        font-family: 'Inter', sans-serif;
        margin-bottom: 1rem;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
        font-size: 1.1rem;
        padding: 0.75rem 1rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #7c3aed;
        box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.3);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(124, 58, 237, 0.4);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669, #10b981);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1e2e 0%, #2d2d44 100%);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Status box styling */
    .stStatus {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
    }
    
    /* Feature cards */
    .feature-card {
        text-align: center;
        padding: 1rem;
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-title {
        color: #e2e8f0;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    
    .feature-desc {
        color: #94a3b8;
        font-size: 0.85rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# API Configuration
load_dotenv()
weather_key = os.getenv("WEATHER_KEY")
model_id = "llama3.2"

# ==========================================
# 2. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.markdown("**Model:** `llama3.2`")
    st.markdown("**API:** OpenWeatherMap")
    
    st.divider()
    
    st.markdown("## 🤖 How It Works")
    st.markdown("""
    <div style="font-size: 0.9rem; color: #94a3b8;">
    
    **1. 🔍 Weather Agent**  
    Fetches real-time data from weather API
    
    **2. ✍️ Content Agent**  
    Converts data into readable report
    
    **3. 📄 PDF Agent**  
    Generates downloadable PDF
    
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.info("💡 Ensure Ollama is running locally!")
    
    st.markdown("---")
    st.markdown("##### Powered by")
    st.markdown("🧠 **PhiData** + 🦙 **Ollama** + 🌐 **OpenWeatherMap**")

# ==========================================
# 3. DEFINE CUSTOM TOOLS
# ==========================================

def get_weather(city: str) -> str:
    """
    Fetches real-time weather data for a given city using OpenWeatherMap.
    """
    if not weather_key:
        return "Error: Weather API Key missing."
    
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": weather_key,
        "units": "metric"
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            temp_celsius = data['main']['temp']
            temp_fahrenheit = round((temp_celsius * 9/5) + 32, 1)
            weather_info = {
                "City": data["name"],
                "Temperature": f"{temp_celsius}°C / {temp_fahrenheit}°F",
                "Description": data["weather"][0]["description"],
                "Humidity": f"{data['main']['humidity']}%",
                "Wind Speed": f"{data['wind']['speed']} m/s"
            }
            return json.dumps(weather_info)
        else:
            return f"Error: {data.get('message', 'Failed to fetch data')}"
            
    except Exception as e:
        return f"Error fetching weather: {str(e)}"

def create_weather_pdf(text_content: str) -> str:
    """
    Generates a PDF file with the given weather report content.
    Returns the filename of the generated PDF.
    """
    filename = "weather_report.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt="SkyFetch Weather Report", ln=True, align='C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=12)
    safe_text = text_content.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    
    pdf.output(filename)
    return filename

# ==========================================
# 4. DEFINE THE AGENTS
# ==========================================

# Agent 1: The Researcher
weather_agent = Agent(
    name="WeatherFetcher",
    model=Ollama(id=model_id),
    tools=[get_weather],
    instructions=["You are a weather tool. Use 'get_weather' for the city. Output ONLY the JSON data found."],
    show_tool_calls=True,
    markdown=True
)

# Agent 2: The Writer
content_agent = Agent(
    name="ContentWriter",
    model=Ollama(id=model_id),
    instructions=[
        "You are a weather reporter.",
        "Convert the provided data into a short, friendly paragraph.",
        "Do not include raw JSON.",
        "Mention temperature, conditions, and a clothing recommendation."
    ],
    markdown=True
)

# Agent 3: The Publisher
pdf_agent = Agent(
    name="PDFCreator",
    model=Ollama(id=model_id),
    tools=[create_weather_pdf],
    instructions=[
        "You are a publisher.",
        "Use 'create_weather_pdf' to save the text provided.",
        "Return the filename ONLY."
    ],
    show_tool_calls=True
)

# ==========================================
# 5. STREAMLIT UI
# ==========================================

# Hero Section
st.markdown('<h1 class="hero-title">🌤️ SkyFetch</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Multi-Agent AI Weather Intelligence System</p>', unsafe_allow_html=True)

# Agent Pipeline Visualization
st.markdown("""
<div style="display: flex; justify-content: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 2rem;">
    <span class="agent-step step-pending">🔍 Weather Agent</span>
    <span style="color: #64748b; align-self: center;">→</span>
    <span class="agent-step step-pending">✍️ Content Agent</span>
    <span style="color: #64748b; align-self: center;">→</span>
    <span class="agent-step step-pending">📄 PDF Agent</span>
</div>
""", unsafe_allow_html=True)

# Input Section
query_input = st.text_input("💬 Weather Query (optional)", placeholder="e.g., Is it good for a picnic? Should I carry an umbrella?", label_visibility="visible")
city_input = st.text_input("🏙️ Enter City Name", "Hyderabad", label_visibility="visible")
generate_btn = st.button("🚀 Generate Weather Report", use_container_width=True)

# Process
if generate_btn:
    if not weather_key:
        st.error("⚠️ Weather API Key is missing!")
    else:
        status_box = st.status("🤖 Agents collaborating...", expanded=True)
        
        try:
            # --- STEP 1 ---
            status_box.write("🔍 **Agent 1 (Weather Researcher):** Fetching real-time data...")
            raw_weather = weather_agent.run(f"Get weather for {city_input}")
            status_box.write("✅ Weather data retrieved!")
            
            # --- STEP 2 ---
            status_box.write("✍️ **Agent 2 (Content Writer):** Crafting your report...")
            # Include user's query context if provided
            if query_input.strip():
                prompt = f"Write a weather report based on this data: {raw_weather.content}. Also address this question: {query_input}"
            else:
                prompt = f"Write a report based on this data: {raw_weather.content}"
            summary_response = content_agent.run(prompt)
            final_report_text = summary_response.content
            status_box.write("✅ Report drafted!")
            
            # --- STEP 3 ---
            status_box.write("📄 **Agent 3 (PDF Publisher):** Generating PDF...")
            # Directly call the PDF creation function to ensure the file is created
            pdf_filename = create_weather_pdf(final_report_text)
            status_box.write("✅ PDF created!")
            
            status_box.update(label="✨ All agents completed successfully!", state="complete", expanded=False)
            
            # Weather Summary Display
            st.markdown(f"""
            <div class="weather-card">
                <h3>📋 Weather Report for {city_input}</h3>
                <p style="color: #e2e8f0; line-height: 1.8;">{final_report_text}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Download Button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with open("weather_report.pdf", "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_file,
                        file_name=f"SkyFetch_{city_input}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
        except Exception as e:
            st.error(f"❌ An error occurred: {e}")
            st.info("💡 **Tip:** Make sure Ollama is running with `llama3.2` model!")

# Footer Section - Features
st.markdown("---")
st.markdown("### ✨ Powered by Multi-Agent AI")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔍</div>
        <div class="feature-title">Real-time Data</div>
        <div class="feature-desc">Live weather from OpenWeatherMap API</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🧠</div>
        <div class="feature-title">AI Processing</div>
        <div class="feature-desc">Local LLM via Ollama (llama3.2)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📄</div>
        <div class="feature-title">PDF Export</div>
        <div class="feature-desc">Download professional reports</div>
    </div>
    """, unsafe_allow_html=True)