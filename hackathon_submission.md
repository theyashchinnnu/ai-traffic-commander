# 🏆 Hackathon 2.0 - AI Agents Submission Guide

This file contains your official project summary and detailed instructions for pushing the code to GitHub and deploying to Render.

---

## 📄 Project Summary (127 words)

**AI City Traffic Commander** is a full-stack traffic management system resolving urban congestion and emergency routing. It integrates six CrewAI agents:
1. **Traffic Monitor**: Extracts incident details (Weather & Geocoding APIs).
2. **Congestion Analyst**: Predicts delays and severity (Density Calculator & Historical DB).
3. **RAG Knowledge Expert**: Retrieves SOPs (ChromaDB search over local rules).
4. **Emergency Router**: Plans Ambulance, Police, and Fire routes.
5. **Signal Optimizer**: Adjusts intersection timing and lane configurations.
6. **Public Notifier**: Generates SMS, Email, and social alerts.

ChromaDB RAG uses local markdown documents (SOPs, diversion policies) as knowledge sources. Multiple agents isolate domain-specific tasks, perform sequential tool calling (APIs, files, databases), and manage dependencies. Secure access uses JWT for dashboards and API keys for external IoT traffic sensors.

---

## 🚀 How to Upload to GitHub (Without Git Installed)

We created a custom Python script `upload_to_github.py` that uploads all code files directly via GitHub's API.

1. Generate a **GitHub Personal Access Token (PAT)**:
   - Go to GitHub -> Settings -> Developer Settings -> Personal Access Tokens -> Tokens (classic).
   - Click **Generate new token (classic)**.
   - Give it a name and check the **`repo`** scope checkbox.
   - Click **Generate token** and copy it safely.

2. Run the upload script from your terminal:
   ```bash
   cd c:\Users\yashc\OneDrive\Desktop\arun\ai-traffic-commander
   python upload_to_github.py
   ```
3. Input your GitHub PAT, username, and the desired repository name.
4. The script will automatically create the repository and upload the files.

---

## ☁️ How to Deploy to Render (Free Tier)

Render will build the application using the included `Dockerfile` and expose it publicly.

1. **Create an account** on [Render.com](https://render.com/).
2. **Link GitHub**: Connect your GitHub account.
3. **Deploy Web Service**:
   - In the Render Dashboard, click **New +** -> **Web Service**.
   - Select your newly created `ai-traffic-commander` repository.
   - Use the following settings (Render should automatically detect them from `render.yaml`):
     - **Name**: `ai-traffic-commander`
     - **Runtime**: `Docker`
     - **Instance Type**: `Free`
4. **Configure Environment Variables**:
   - Scroll down to the **Environment Variables** section.
   - Add a new variable:
     - **Key**: `GOOGLE_API_KEY`
     - **Value**: `[Your Gemini API Key from Google AI Studio]`
5. **Start Deployment**:
   - Click **Deploy Web Service**.
   - Render will build the Docker container and start the server. Once the logs show `Uvicorn running on http://0.0.0.0:10000`, the deployment is complete!
   - You will see your public URL (e.g. `https://ai-traffic-commander-xxxx.onrender.com`) at the top of the dashboard. Copy this link for your submission!
