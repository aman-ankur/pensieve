# 🧠 Pensieve - Meeting Memory Bank

> *"I use the Pensieve. One simply siphons the excess thoughts from one's mind, pours them into the basin, and examines them at one's leisure."*  
> — **Albus Dumbledore**

## What is Pensieve?

Just as Dumbledore's Pensieve allows one to extract, examine, and organize memories, this tool automatically transforms your Zoom meeting transcripts into structured, searchable summaries. Never lose track of important decisions, action items, or key insights from your meetings again.

## ✨ Features

- **🔍 Auto-Discovery**: Monitors your Zoom folder for new meeting transcripts
- **🤖 AI Summarization**: Uses local LLM to create structured summaries with:
  - Key discussion points
  - Action items with ownership and deadlines
  - Decisions made
  - Next steps and follow-ups
- **📂 Smart Organization**: Automatically organizes summaries by date and meeting type
- **🔒 Privacy-First**: All processing happens locally using Ollama
- **⚡ Real-time Processing**: Summaries generated immediately after meetings end

## 🚀 Quick Start

```bash
# Install Ollama
brew install ollama
ollama pull llama3.1:8b

# Install dependencies
pip install -r requirements.txt

# Start monitoring
python src/main.py
```

## 📊 Stats
- **Target**: 20+ meetings/week → 80+ meetings/month
- **Time Saved**: ~30 minutes/week of manual note-taking
- **Storage**: Local-only, no cloud dependencies

## 🎯 Roadmap

- **MVP**: Basic monitoring and summarization
- **V2**: Notion integration, advanced search
- **V3**: Calendar sync, Slack notifications

---
