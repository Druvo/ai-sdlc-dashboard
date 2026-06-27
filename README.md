# AI-SDLC Intelligence Dashboard

A standalone dashboard that tracks AI tools, models, and practices specifically for software developers. No AI dependency — pure RSS/API scraping.

## What It Tracks

| Category | Examples |
|----------|----------|
| 🤖 AI Coding Tools | Copilot, Claude Code, Cursor, Codex, Aider, Windsurf, Cline |
| 🧠 New Models (Coding) | GPT, Claude, Gemini, DeepSeek, Qwen, MiMo benchmarks |
| 🔗 Agents & MCP | Agentic coding, MCP servers, multi-agent workflows |
| 📝 Prompt & Context Engineering | System prompts, loops, RAG, context windows |
| 💰 Token Optimization | Cost, caching, batching, rate limits |
| ⚙️ Best Practices & SDLC | AI testing, code review, CI/CD, workflows |
| 🏠 Self-Hosting & Local Models | Ollama, llama.cpp, GGUF, quantization |

## Sources (25+)

- **Official blogs**: Anthropic, OpenAI, Google AI, HuggingFace
- **Dev practitioners**: Simon Willison, Chip Huyen, Andrew Ng
- **News**: TechCrunch, The Verge, Ars Technica, VentureBeat
- **Community**: Hacker News, Reddit (r/LocalLLaMA, r/MachineLearning)
- **Research**: arXiv (cs.AI, cs.CL, cs.SE)
- **Code**: GitHub trending AI repos

## Quick Start

```bash
cd ~/ai-dashboard
python server.py
```

Open **http://localhost:8501** in your browser.

Or double-click `start-dashboard.bat`.

## Features

- Auto-fetches every 30 minutes
- SDLC-filtered (no healthcare/art/autonomous driving noise)
- Category sidebar with counts
- Time range filter (6h / 24h / 3d / 7d)
- Full-text search
- Manual refresh button
- Dark theme, responsive

## Dependencies

```bash
pip install feedparser aiohttp fastapi uvicorn
```

## Files

```
ai-dashboard/
├── server.py           # Backend (FastAPI + RSS fetcher)
├── static/index.html   # Frontend (vanilla JS)
├── start-dashboard.bat # One-click startup
├── dashboard.db        # SQLite cache (auto-created)
└── README.md           # This file
```
