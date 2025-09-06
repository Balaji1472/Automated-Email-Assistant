# AI Communication Assistant

A smart, AI-powered tool designed to streamline customer support by automatically fetching, analyzing, and drafting responses to support emails.

---

🎬 **Demo Video**
Watch a complete walkthrough of the application, from fetching an unread email to analyzing it and sending a professional, AI-generated reply.

➡️ [Watch the Demo Video Here](https://drive.google.com/file/d/1hEo7AIR-2LB4SkFYbJGae6ALK1rKoqiY/view?usp=sharing)


---

✨ **Key Features**

* **Automated Email Fetching**: Automatically connects to a Gmail inbox to find and process unread support-related emails.
* **Multi-Layered AI Analysis**: Each email is analyzed to determine its:

  * **Sentiment**: Positive, Negative, or Neutral
  * **Priority**: Urgent or Not Urgent
  * **Summary**: A concise, one-sentence overview of the customer's request.
* **Context-Aware Response Generation**: Uses a Retrieval-Augmented Generation (RAG) system with a local knowledge base to provide accurate, context-specific answers.
* **Human-in-the-Loop Design**: The AI generates a high-quality draft, but the user always has the final say. You can review and edit the response directly in the UI before sending.
* **Interactive Dashboard**: A clean and modern user interface built with Streamlit that provides a high-level overview of email statistics, processing results, and detailed analytics.

---

⚙️ **How It Works: The Workflow**

1. **Fetch Emails**: The user clicks *"Process New Unread Emails"* on the web interface.
2. **Backend Processing**: The Streamlit frontend calls the FastAPI backend API. The backend connects to Gmail via IMAP to fetch unread support emails.
3. **AI Core Analysis**: For each email, the system uses the Google Gemini API to perform sentiment analysis, prioritize the request, and generate a summary.
4. **Knowledge Retrieval (RAG)**: The AI uses the email summary to search a ChromaDB vector database for relevant information to answer the customer's question.
5. **Generate Draft Response**: The retrieved knowledge and the initial analysis are passed back to the Gemini API to generate a professional and helpful draft response.
6. **Display Results**: The processed emails, analysis, and draft responses are displayed clearly on the Streamlit dashboard.
7. **Review and Send**: The user can review the original email, edit the AI-generated draft, and send the final response directly from the dashboard using SMTP.

---

🛠️ **Technology Stack**

* **Backend**: FastAPI, Uvicorn
* **Frontend**: Streamlit, Plotly
* **AI & Machine Learning**: Google Gemini, ChromaDB
* **Email Handling**: Python `imaplib` & `smtplib`
* **Core Language**: Python

---

🚀 **Setup and Usage**

### Step 1: Clone the Repository

```bash
git clone https://github.com/Balaji1472/Automated-Email-Assistant.git
cd Automated-Email-Assistant
```

### Step 2: Set Up a Virtual Environment

It's highly recommended to use a virtual environment.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies

Install all the required Python packages.

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Rename the example file `.env.example` to `.env`.

Open the new `.env` file and add your credentials:

```bash
# Gmail Credentials (use an App Password, not your main password)
GMAIL_ADDRESS="your-email@gmail.com"
GMAIL_PASSWORD="your-gmail-app-password"

# Google Gemini API Key
GEMINI_API_KEY="your-gemini-api-key"
```

⚠️ **Important Security Note:**

* For `GMAIL_PASSWORD`, you must use a **Google App Password**. Your regular password will not work. You can generate one here: [Google App Passwords](https://myaccount.google.com/apppasswords).
* Ensure IMAP is enabled in your Gmail settings.

### Step 5: Run the Application

You need to run the backend and frontend servers in two separate terminals.

**Terminal 1: Start the Backend (FastAPI)**

```bash
uvicorn backend:app --reload
```

The backend will be running at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

**Terminal 2: Start the Frontend (Streamlit)**

```bash
streamlit run frontend.py
```

Your web browser should automatically open with the application.

---

✅ You are now ready to use the **AI Communication Assistant**!
