## **CREWAI-AGENTS: AI-Powered Procurement Assistant** 🛒🤖
![GitHub Repo stars](https://img.shields.io/github/stars/ahmedali703/CREWAI-AGENTS?style=social)

### **Overview**
**CREWAI-AGENTS** is an AI-powered procurement assistant that helps businesses find, compare, and recommend products from various e-commerce websites. This system leverages **CrewAI**, **Flask**, and several AI models to automate the procurement process and generate detailed comparison reports.

It follows a structured workflow where:
1. **AI suggests search queries** to find relevant products.
2. **A search engine agent retrieves product pages** from e-commerce sites.
3. **A web scraping agent extracts key product details.**
4. **A reporting agent compiles a procurement report** in a professional HTML format.

### **Features**
✅ AI-generated search queries tailored for specific product searches.  
✅ Automated web scraping to extract product details.  
✅ Smart ranking and recommendation based on best value.  
✅ Generates a **detailed procurement report** with structured insights.  
✅ Easy-to-use **REST API** for seamless integration.  

---

## **Tech Stack**
🔹 **Backend**: Python (Flask, CrewAI)  
🔹 **AI Models**: OpenAI GPT-4o  
🔹 **Web Scraping**: Scrapegraph API  
🔹 **Search Engine**: Tavily API  
🔹 **Frontend**: Static HTML, CSS, JavaScript  

---

## **Installation & Setup**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-username/CREWAI-AGENTS.git
cd CREWAI-AGENTS
```

### **2️⃣ Create a Virtual Environment**
```bash
python -m venv ai_env
source ai_env/bin/activate  # On macOS/Linux
ai_env\Scripts\activate      # On Windows
```

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4️⃣ Set Up Environment Variables**
Rename `.env.local.example` to `.env` and add your API keys:
```
OPENAI_API_KEY=your_openai_api_key
AGENTOPS_API_KEY=your_agentops_api_key
TAVILY_API_KEY=your_tavily_api_key
SCRAPEGRAPH_API_KEY=your_scrapegraph_api_key
```

### **5️⃣ Run the Application**
```bash
python app.py
```
The API will be available at **`http://localhost:5000`**.

---

## **Usage**
### **API Endpoints**
#### 🔹 **Run a Product Search**
**Endpoint:**  
```
POST /api/search
```
**Request Body (JSON):**
```json
{
  "productName": "Laptop",
  "country": "USA",
  "resultCount": 5
}
```
**Response Example:**
```json
{
  "status": "success",
  "message": "Report generated successfully",
  "report_url": "/reports/procurement_report.html"
}
```

#### 🔹 **Retrieve the Procurement Report**
After running the search, open the generated report URL in a browser.

---

## **Project Structure**
```
CREWAI-AGENTS/
│── ai_env/                  # Virtual environment (ignored in .gitignore)
│── ai-agent-output/         # Stores AI-generated reports and outputs
│── static/                  # Frontend assets (CSS, JS)
│── templates/               # HTML templates
│── app.py                   # Main Flask application
│── requirements.txt         # Python dependencies
│── .env.local.example       # Example environment variables
│── README.md                # Project documentation
```

---

## **Contributing**
Contributions are welcome! 🎉  
To contribute:
1. Fork the repository.
2. Create a new branch (`feature/new-feature`).
3. Commit your changes.
4. Submit a pull request.

---

## **License**
This project is licensed under the **MIT License**. Feel free to use, modify, and distribute it.

---

🚀 **Happy Coding!** 🚀

