# 🧑‍🏫 AI Tutor Backend

This is the backend service for an AI-powered coding tutor built with **Django REST Framework** and **LangChain (Google Gemini integration)**.  
It provides authentication, script management, chat history, and AI-driven coding advice.

---

## 🚀 Features
- User registration & authentication (JWT-ready)
- Script CRUD (create, open, update, list)
- AI tutor agent powered by Google Gemini
- Saves & retrieves chat history
- Tracks user skill level (1–100)

---

## ⚙️ Tech Stack
- Django + Django REST Framework
- LangChain + Google Gemini
- Pydantic (structured outputs)
- SQLite/Postgres (DB)

---

## 🔑 Environment Variables
Create a `.env` file in your project root:




---

## 🛠️ Setup & Run
```bash
# Clone repo
git clone https://github.com/jackenbe/StrikeNet-new_backend.git
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

