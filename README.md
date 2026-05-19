# Voice2Value – AI Product Feedback Intelligence Platform 🚀

## Overview

Voice2Value is an AI-powered **Product Feedback Intelligence Platform** designed to automatically collect, process, analyze, and visualize user feedback from multiple sources such as CSV uploads, APIs, and Google Play reviews.

The platform helps product teams identify critical issues, understand user sentiment, prioritize fixes, and improve overall product quality using NLP, clustering, sentiment analysis, and AI-generated insights.

---

# ✨ Features

## 🧠 AI / NLP Pipeline

- Text preprocessing using spaCy
- Embedding generation using Sentence Transformers
- HDBSCAN-based issue clustering
- Sentiment analysis using VADER
- Trend detection and priority scoring
- LLM-powered summaries and labels

---

## 📥 Data Ingestion

- CSV upload support
- JSON API ingestion
- Google Play review connector
- Scheduler-based automated ingestion
- Duplicate review filtering

---

## 📊 Dashboard & Analytics

- Real-time dashboard
- Critical issue tracking
- Positive feedback analysis
- Cluster visualization
- Sync history and ingestion tracking
- System health monitoring

---

## 🔌 REST API

### Ingestion

```http
POST /upload-csv
POST /ingest-api
GET  /ingestion-status
```

### Processing

```http
POST /process-reviews
GET  /cluster-results/{id}
GET  /top-clusters
```

### Scheduler

```http
POST /scheduler/start
POST /scheduler/stop
GET  /scheduler/status
```

---

# 🏗️ System Architecture

```text
Google Play Reviews / CSV / APIs
                ↓
        Data Ingestion Layer
                ↓
           Raw Review DB
                ↓
         NLP Processing Pipeline
                ↓
      Clustering & Sentiment
                ↓
       Priority & Trend Engine
                ↓
         AI Insight Generator
                ↓
            Dashboard UI
```

---

# 🛠️ Tech Stack

## Backend

- Python
- Flask
- FastAPI
- scikit-learn
- spaCy
- HDBSCAN
- Sentence Transformers
- VADER Sentiment

---

## Frontend

- HTML
- CSS
- JavaScript
- Node.js
- Express.js

---

## Database

- MongoDB
- SQLite
- PostgreSQL (Production Ready)

---

## DevOps / CI-CD

- Git
- GitHub
- GitLab CI/CD

---

# 🔄 NLP Pipeline Workflow

```text
Review Input
     ↓
Filtering & Validation
     ↓
Text Preprocessing
     ↓
Embedding Generation
     ↓
Issue Clustering
     ↓
Sentiment Analysis
     ↓
Trend Detection
     ↓
Priority Scoring
     ↓
LLM Insight Generation
     ↓
Dashboard Visualization
```

---

# 📁 Project Structure

```bash
backend/
│
├── app/
│   ├── services/
│   ├── models/
│   ├── workers/
│   ├── api/
│   └── main.py
│
├── tests/
├── uploads/
├── logs/
├── data/
└── run.py

frontend/
│
├── Landing page/
├── dashboard/
└── server.js
```

---

# 🚀 Run Commands

## 1️⃣ Start Backend API

```bash
cd D:\AI\backend
python run.py
```

---

## 2️⃣ Build Landing UI

```bash
cd D:\AI\frontend\Landing page\Voice2Value-master

npm install
npm run build
```

---

## 3️⃣ Start Frontend Server

```bash
cd D:\AI\frontend

npm install
node server.js
```

---

## 4️⃣ Open Application

```text
http://localhost:3000
```

---

# 📱 Google Play Review Integration

The platform supports automated review collection using:

- google-play-scraper

### Example Monitored Apps

- Spotify
- Instagram
- WhatsApp
- Amazon
- Swiggy

---

# ⚙️ CI/CD Pipeline

The project includes GitLab CI/CD support with:

- Build stage
- Test stage
- Deployment stage
- Automated validation
- Pipeline execution monitoring

---

# 🔮 Future Enhancements

- Multi-source review connectors
- Predictive issue detection
- Root cause analysis
- Automated bug report generation
- Real-time notifications
- Docker & Kubernetes deployment
- Advanced analytics dashboard

---

# 💡 Novelty of the Project

Unlike traditional review analysis systems, Voice2Value focuses on:

✅ AI-driven issue clustering  
✅ Automated priority scoring  
✅ Trend-aware product intelligence  
✅ LLM-generated actionable insights  
✅ Real-time product feedback monitoring

The system is designed not only to analyze reviews, but also to assist product teams in identifying, prioritizing, and responding to critical product issues efficiently.

---

# 👨‍💻 Contributors

- Sathiya
- Voice2Value Development Team

---

# 📜 License

This project is developed for academic and research purposes.
