# 🏆 AI-Powered Sports Quiz Generation Agent

An intelligent **Retrieval-Augmented Generation (RAG)** application that generates high-quality sports quizzes using historical knowledge stored in **ChromaDB**, live sports information from the web, and **Groq LLMs**. The application provides an interactive **Streamlit** interface with quiz generation, answer evaluation, scoring, and export functionality.

---

## 📌 Features

- 🎯 Generate sports quizzes for multiple sports
- 🤖 AI-powered quiz generation using **Groq LLM**
- 📚 Retrieval-Augmented Generation (RAG)
- 🗂️ Vector database using **ChromaDB**
- 🔍 Live sports information using **DuckDuckGo Search**
- 📝 Multiple Choice Questions (MCQs)
- ✅ Instant answer evaluation
- 📊 Quiz score calculation
- 📄 Export quizzes as:
  - PDF
  - Markdown
  - JSON
- 📱 Generate social media captions
- 🎨 Clean and interactive Streamlit UI

---

# 🏗️ Project Architecture

```
                +----------------------+
                |     Streamlit UI     |
                +----------+-----------+
                           |
                           |
               User selects Sport &
                 Difficulty Level
                           |
                           |
         +-----------------+-----------------+
         |                                   |
         |                                   |
         ▼                                   ▼
  ChromaDB Retrieval               DuckDuckGo Search
 (Historical Sports Data)         (Latest Sports News)
         |                                   |
         +---------------+-------------------+
                         |
                         ▼
                RAG Context Builder
                         |
                         ▼
                 Groq LLM (Llama 3.3)
                         |
                         ▼
                 Quiz JSON Generation
                         |
                         ▼
              Evaluation & Score Engine
                         |
                         ▼
          PDF | JSON | Markdown Export
```

---

# 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Frontend | Streamlit |
| Language | Python 3.11+ |
| LLM | Groq (Llama 3.3 70B Versatile) |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| Web Search | DuckDuckGo Search |
| RAG Framework | LangChain |
| PDF Export | FPDF2 |
| Environment | Python Dotenv |

---

# 📂 Project Structure

```
sports_quiz_agent/
│
├── app.py
├── requirements.txt
├── README.md
├── .env.example
│
├── config/
│
├── data/
│
├── src/
│   ├── database/
│   ├── llm/
│   ├── models/
│   ├── rag/
│   ├── search/
│   ├── ui/
│   └── utils/
│
├── chroma_store/
│
└── static/
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/yourusername/sports_quiz_agent.git

cd sports_quiz_agent
```

---

## Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file in the project root.

```env
LLM_PROVIDER=groq

GROQ_API_KEY=your_groq_api_key

GROQ_MODEL=llama-3.3-70b-versatile

EMBEDDING_MODEL=all-MiniLM-L6-v2
```

---

# ▶️ Run the Application

```bash
streamlit run app.py
```

Application runs at

```
http://localhost:8501
```

---

# 🚀 How It Works

1. User selects a sport.
2. User selects difficulty level.
3. Historical sports facts are retrieved from ChromaDB.
4. Latest sports information is fetched from DuckDuckGo Search.
5. Retrieved information is combined into a RAG context.
6. Groq LLM generates a structured quiz.
7. User submits answers.
8. Application evaluates responses.
9. Results can be exported to PDF, JSON, or Markdown.

---

# 📄 Export Options

The application supports exporting quizzes as:

- PDF
- JSON
- Markdown

Additionally, it can generate social media captions for sharing quizzes online.

---

# 📸 Screenshots

## Home Page

_Add screenshot here_

---

## Generated Quiz

_Add screenshot here_

---

## Quiz Results

_Add screenshot here_

---

## Export Options

_Add screenshot here_

---

# ✨ Key Highlights

- Retrieval-Augmented Generation (RAG)
- Vector Search using ChromaDB
- AI Quiz Generation
- Live Sports Information
- Groq Integration
- Interactive UI
- Export Functionality
- Clean Modular Architecture
- Environment-based Configuration

---

# 📈 Future Enhancements

- User Authentication
- Quiz History
- Leaderboard
- Timed Quiz Mode
- Difficulty Prediction
- Speech-based Quiz
- Multiplayer Quiz
- More Sports Categories
- Admin Dashboard
- Cloud Deployment

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository.
2. Create a feature branch.

```bash
git checkout -b feature-name
```

3. Commit changes.

```bash
git commit -m "Added new feature"
```

4. Push the branch.

```bash
git push origin feature-name
```

5. Create a Pull Request.

---

# 📄 License

This project is developed for educational and internship assessment purposes.

---

# 👨‍💻 Author

**Omprakash Karri**

- GitHub: https://github.com/OMPRAKASHKARRI
- LinkedIn: https://www.linkedin.com/in/omprakash-karri/

---

⭐ If you found this project useful, consider giving it a star!