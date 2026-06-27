"""
AI-SDLC Intelligence Dashboard
Focused ONLY on AI tools, techniques, and news that boost your Software Development Lifecycle.

Categories:
  - AI Coding Tools (Copilot, Claude Code, Cursor, Codex, Aider, Windsurf...)
  - New Models (coding-relevant: GPT, Claude, Gemini, DeepSeek, Qwen, MiMo...)
  - Agents & MCP (agentic coding, MCP servers, multi-agent workflows)
  - Prompt & Context Engineering (system prompts, loops, RAG, context windows)
  - Token Optimization (cost, caching, batching, structured output)
  - Best Practices & Workflows (AI-assisted SDLC, testing, code review, CI/CD)
  - Self-Hosting & Local Models (Ollama, llama.cpp, GGUF, on-device)

Sources: 25+ curated RSS feeds, HN, Reddit, GitHub trending
No AI dependency. Pure scraping. Auto-refreshes every 30 min.
"""

import asyncio
import hashlib
import json
import re
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import aiohttp
import feedparser
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

# ─── Configuration ───────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "dashboard.db"
STATIC_DIR = Path(__file__).parent / "static"
REFRESH_INTERVAL = 1800  # 30 minutes
REQUEST_TIMEOUT = 15

# ─── RSS Feeds — SDLC-focused only ───────────────────────────────────

RSS_FEEDS = {
    # ── Official AI company blogs ──
    "Anthropic Blog": "https://www.anthropic.com/rss.xml",
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "HuggingFace Blog": "https://huggingface.co/blog/feed.xml",
    "DeepMind Blog": "https://deepmind.google/blog/rss.xml",
    "Meta AI Blog": "https://ai.meta.com/blog/rss/",
    "Mistral Blog": "https://mistral.ai/feed.xml",

    # ── AI coding tools ──
    "GitHub Changelog": "https://github.blog/changelog/feed/",
    "Cursor Blog": "https://www.cursor.com/blog/rss.xml",
    "LangChain Blog": "https://blog.langchain.dev/rss/",
    "LlamaIndex Blog": "https://www.llamaindex.ai/blog/rss.xml",
    "Langfuse Blog": "https://blog.langfuse.com/rss.xml",
    "CrewAI Blog": "https://www.crewai.com/blog/rss.xml",

    # ── AI newsletters & digests ──
    "AI News (Latent Space)": "https://buttondown.com/ainews/rss",
    "Last Week in AI": "https://lastweekin.ai/feed",
    "The AI Exchange": "https://newsletter.theaiedge.io/feed",
    "The Batch (Andrew Ng)": "https://www.deeplearning.ai/the-batch/feed/",

    # ── Developer-focused AI practitioners ──
    "Simon Willison": "https://simonwillison.net/atom/everything/",
    "Chip Huyen": "https://huyenchip.com/feed.xml",
    "Interconnects (Nathan Lambert)": "https://www.interconnects.ai/feed",
    "Ahead of AI (Sebastian Raschka)": "https://magazine.sebastianraschka.com/feed",
    "Latent Space Podcast": "https://www.latent.space/feed",

    # ── AI dev news ──
    "Ars Technica AI": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",

    # ── Research (coding-relevant) ──
    "arXiv cs.AI": "https://rss.arxiv.org/rss/cs.AI",
    "arXiv cs.CL (NLP)": "https://rss.arxiv.org/rss/cs.CL",
    "arXiv cs.SE (Software Eng)": "https://rss.arxiv.org/rss/cs.SE",
    "arXiv cs.LG (ML)": "https://rss.arxiv.org/rss/cs.LG",
}

# ─── Category Keywords — SDLC boost only ─────────────────────────────

CATEGORIES = {
    "🤖 AI Coding Tools": [
        "copilot", "github copilot", "claude code", "cursor", "windsurf", "cline",
        "aider", "devin", "codex", "openai codex", "hermes agent", "openclaw",
        "codeium", "tabnine", "amazon q", "codewhisperer", "continue.dev",
        "supermaven", "sourcegraph", "cody", "bolt", "v0", "lovable", "replit",
        "ai coding", "ai code", "ai assistant", "coding agent", "pair programming",
        "ai IDE", "ai editor", "code completion", "code generation",
    ],
    "🧠 New Models (Coding)": [
        "gpt-4", "gpt-5", "o1", "o3", "o4", "claude", "sonnet", "opus", "haiku",
        "gemini", "llama", "mistral", "qwen", "deepseek", "mimo", "mixtral",
        "phi-4", "command r", "grok", "model release", "model launch", "benchmark",
        "swe-bench", "humaneval", "arena", "coding benchmark", "reasoning model",
        "foundation model", "open-source model", "frontier model",
    ],
    "🔗 Agents & MCP": [
        "agent", "agentic", "mcp", "model context protocol", "multi-agent",
        "function calling", "tool use", "tool calling", "agentic coding",
        "autogen", "crewai", "langchain agent", "openai agents sdk",
        "anthropic tool", "mcp server", "mcp client", "a2a", "agent-to-agent",
        "workflow", "orchestration", "agent framework",
    ],
    "📝 Prompt & Context Engineering": [
        "prompt engineering", "system prompt", "chain of thought", "few-shot",
        "context window", "context engineering", "prompt template", "structured output",
        "json mode", "response format", "loop", "agentic loop", "reasoning",
        "thinking", "extended thinking", "scratchpad", "self-reflection",
        "rag", "retrieval", "embedding", "vector", "knowledge base",
        "semantic search", "reranker", "chunk", "context stuffing",
    ],
    "💰 Token Optimization & Cost": [
        "token", "token optimization", "cost", "pricing", "budget",
        "prompt caching", "context caching", "cache", "batch", "batching",
        "rate limit", "throughput", "latency", "ttft", "tokens per second",
        "cost saving", "cheaper", "free tier", "api pricing",
        "speculative decoding", "kv cache", "flash attention",
    ],
    "⚙️ Best Practices & SDLC": [
        "best practice", "tips", "guide", "tutorial", "workflow",
        "ai testing", "ai code review", "ai documentation", "ai refactoring",
        "test generation", "ai ci/cd", "ai devops", "tdd", "ai tdd",
        "clean code", "code quality", "technical debt", "ai migration",
        "ai modernization", "legacy code", "codebase", "ai pair",
        "headroom", "context management", "ai skill",
    ],
    "🏠 Self-Hosting & Local Models": [
        "local", "self-host", "ollama", "llamafile", "llama.cpp", "kobold",
        "open webui", "docker", "homelab", "on-device", "edge ai",
        "npu", "gguf", "gptq", "quantization", "fine-tuning", "lora", "qlora",
        "distillation", "local llm", "private ai", "air-gapped",
    ],
}

# ─── Strict SDLC filter ──────────────────────────────────────────────

# Articles must match at least one SDLC-relevant keyword to be included.
# This filters out general AI news (healthcare, art, autonomous driving, etc.)
SDLC_KEYWORDS = [
    # Tools & coding
    "code", "coding", "developer", "programming", "software", "ide", "editor",
    "github", "gitlab", "vscode", "vs code", "jetbrains", "terminal", "cli",
    "api", "sdk", "library", "framework", "package", "npm", "pip", "npm",
    "debug", "test", "lint", "format", "refactor", "deploy", "ci/cd", "pipeline",
    "commit", "pr", "pull request", "merge", "branch", "repo", "repository",
    # AI-specific dev terms
    "llm", "ai", "model", "agent", "mcp", "rag", "prompt", "token",
    "embedding", "vector", "inference", "fine-tun", "quantiz", "benchmark",
    "copilot", "cursor", "claude", "gpt", "gemini", "openai", "anthropic",
    "deepseek", "mistral", "llama", "qwen", "mimo",
    "chatbot", "assistant", "autonomous", "agentic", "workflow",
    # DevOps & infra
    "docker", "kubernetes", "k8s", "cloud", "aws", "azure", "gcp",
    "server", "hosting", "deploy", "monitor", "log", "observ",
    # Software engineering
    "architecture", "microservice", "monolith", "clean code", "solid",
    "design pattern", "algorithm", "data structure", "performance",
    "scalab", "security", "authentication", "authorization",
]


def is_sdlc_relevant(title: str, summary: str) -> bool:
    """Check if article is relevant to software development."""
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in SDLC_KEYWORDS)


# ─── Database ─────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT,
            source TEXT,
            summary TEXT,
            category TEXT,
            published TEXT,
            fetched_at TEXT NOT NULL,
            score REAL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            fetched_at TEXT,
            article_count INTEGER,
            error TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON articles(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_published ON articles(published DESC)")
    conn.commit()
    conn.close()


def make_id(title: str, url: str) -> str:
    return hashlib.md5(f"{title}|{url}".encode()).hexdigest()


def classify(title: str, summary: str) -> str:
    """Classify article into SDLC category based on keyword matching."""
    text = f"{title} {summary}".lower()
    scores = {}
    for cat, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[cat] = score
    if not scores:
        return "📰 General Dev AI"
    return max(scores, key=scores.get)


def save_articles(articles: list[dict]):
    conn = sqlite3.connect(str(DB_PATH))
    now = datetime.now(timezone.utc).isoformat()
    saved = 0
    for a in articles:
        aid = make_id(a["title"], a.get("url", ""))
        try:
            conn.execute("""
                INSERT OR IGNORE INTO articles
                (id, title, url, source, summary, category, published, fetched_at, score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (aid, a["title"], a.get("url", ""), a.get("source", ""),
                  a.get("summary", ""), a.get("category", "📰 General Dev AI"),
                  a.get("published", ""), now, a.get("score", 0)))
            saved += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return saved


def get_articles(category: Optional[str] = None, limit: int = 300,
                 hours: int = 72) -> list[dict]:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    if category and category != "all":
        rows = conn.execute(
            "SELECT * FROM articles WHERE category=? AND fetched_at>? "
            "ORDER BY published DESC LIMIT ?",
            (category, cutoff, limit)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM articles WHERE fetched_at>? "
            "ORDER BY published DESC LIMIT ?",
            (cutoff, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    cutoff_24h = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    recent = conn.execute(
        "SELECT COUNT(*) FROM articles WHERE fetched_at>?", (cutoff_24h,)
    ).fetchone()[0]
    cats = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM articles "
        "GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    last_fetch = conn.execute(
        "SELECT MAX(fetched_at) FROM fetch_log"
    ).fetchone()[0]
    conn.close()
    return {
        "total_articles": total,
        "articles_24h": recent,
        "categories": {r[0]: r[1] for r in cats},
        "last_fetch": last_fetch or "Never",
    }


# ─── Helpers ──────────────────────────────────────────────────────────

def clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:500] if len(text) > 500 else text


def parse_date(entry) -> str:
    for field in ('published_parsed', 'updated_parsed'):
        parsed = getattr(entry, field, None) or entry.get(field)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    for field in ('published', 'updated'):
        val = getattr(entry, field, None) or entry.get(field, '')
        if val:
            return val
    return datetime.now(timezone.utc).isoformat()


# ─── Fetchers ────────────────────────────────────────────────────────

async def fetch_rss(session: aiohttp.ClientSession, name: str,
                    url: str) -> list[dict]:
    articles = []
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(
                total=REQUEST_TIMEOUT)) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
            feed = feedparser.parse(text)
            for entry in feed.entries[:20]:
                title = entry.get('title', '').strip()
                if not title:
                    continue
                link = entry.get('link', '')
                summary = clean_html(
                    entry.get('summary', entry.get('description', '')))
                # SDLC filter: skip irrelevant articles
                if not is_sdlc_relevant(title, summary):
                    continue
                articles.append({
                    "title": title,
                    "url": link,
                    "source": name,
                    "summary": summary,
                    "category": classify(title, summary),
                    "published": parse_date(entry),
                })
    except Exception:
        pass
    return articles


async def fetch_hn(session: aiohttp.ClientSession) -> list[dict]:
    """Fetch top AI/dev stories from Hacker News."""
    articles = []
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        async with session.get(url,
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            ids = (await resp.json())[:100]

        sem = asyncio.Semaphore(10)

        async def fetch_story(sid):
            async with sem:
                try:
                    async with session.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                        timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        return await resp.json()
                except Exception:
                    return None

        stories = await asyncio.gather(
            *[fetch_story(sid) for sid in ids])

        for story in stories:
            if not story or story.get("type") != "story":
                continue
            title = story.get("title", "")
            if not is_sdlc_relevant(title, ""):
                continue
            story_url = story.get(
                "url",
                f"https://news.ycombinator.com/item?id={story['id']}")
            score = story.get("score", 0)
            comments = story.get("descendants", 0)
            ts = story.get("time", 0)
            pub = (datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                   if ts else "")
            articles.append({
                "title": f"{title} ({score}\u2b06 {comments}\U0001f4ac)",
                "url": story_url,
                "source": "Hacker News",
                "summary": f"HN: {score} points, {comments} comments",
                "category": classify(title, ""),
                "published": pub,
                "score": score,
            })
    except Exception:
        pass
    return articles


async def fetch_reddit(session: aiohttp.ClientSession,
                       subreddit: str) -> list[dict]:
    articles = []
    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
        headers = {"User-Agent": "AI-SDLC-Dashboard/1.0"}
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
            for post in data.get("data", {}).get("children", []):
                d = post.get("data", {})
                title = d.get("title", "")
                link = d.get("url", "")
                if d.get("is_self"):
                    link = f"https://reddit.com{d.get('permalink', '')}"
                score = d.get("score", 0)
                comments = d.get("num_comments", 0)
                ts = d.get("created_utc", 0)
                pub = (datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                       if ts else "")
                selftext = clean_html(d.get("selftext", ""))[:300]
                if not is_sdlc_relevant(title, selftext):
                    continue
                articles.append({
                    "title": f"{title} ({score}\u2b06 {comments}\U0001f4ac)",
                    "url": link,
                    "source": f"r/{subreddit}",
                    "summary": selftext or f"Reddit: {score} upvotes",
                    "category": classify(title, selftext),
                    "published": pub,
                    "score": score,
                })
    except Exception:
        pass
    return articles


async def fetch_github_trending(session: aiohttp.ClientSession) -> list[dict]:
    articles = []
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y-%m-%d")
        url = (f"https://api.github.com/search/repositories?"
               f"q=ai+OR+llm+OR+agent+OR+copilot+OR+mcp+created:>{since}"
               f"&sort=stars&order=desc&per_page=20")
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-SDLC-Dashboard/1.0"}
        async with session.get(url, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
            for repo in data.get("items", []):
                name = repo.get("full_name", "")
                desc = repo.get("description", "") or ""
                stars = repo.get("stargazers_count", 0)
                lang = repo.get("language", "") or ""
                articles.append({
                    "title": f"\u2b50 {name} ({stars:,}\u2605)",
                    "url": repo.get("html_url", ""),
                    "source": "GitHub Trending",
                    "summary": f"{desc} [{lang}]",
                    "category": classify(name + " " + desc, ""),
                    "published": repo.get("created_at", ""),
                    "score": stars,
                })
    except Exception:
        pass
    return articles


# ─── Background Fetcher ──────────────────────────────────────────────

async def fetch_all():
    all_articles = []
    conn_log = sqlite3.connect(str(DB_PATH))
    now = datetime.now(timezone.utc).isoformat()

    async with aiohttp.ClientSession() as session:
        # RSS feeds
        tasks = [fetch_rss(session, name, url)
                 for name, url in RSS_FEEDS.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            name = list(RSS_FEEDS.keys())[i]
            if isinstance(result, list):
                all_articles.extend(result)
                conn_log.execute(
                    "INSERT INTO fetch_log (source,fetched_at,article_count) "
                    "VALUES (?,?,?)", (name, now, len(result)))
            else:
                conn_log.execute(
                    "INSERT INTO fetch_log (source,fetched_at,article_count,"
                    "error) VALUES (?,?,0,?)", (name, now, str(result)[:200]))

        # HN
        hn = await fetch_hn(session)
        all_articles.extend(hn)
        conn_log.execute(
            "INSERT INTO fetch_log (source,fetched_at,article_count) "
            "VALUES (?,?,?)", ("Hacker News", now, len(hn)))

        # Reddit
        for sub in ["LocalLLaMA", "MachineLearning", "artificial",
                     "ChatGPTPro", "ClaudeAI", "singularity", "OpenAI"]:
            reddit = await fetch_reddit(session, sub)
            all_articles.extend(reddit)
            conn_log.execute(
                "INSERT INTO fetch_log (source,fetched_at,article_count) "
                "VALUES (?,?,?)", (f"r/{sub}", now, len(reddit)))

        # GitHub trending
        gh = await fetch_github_trending(session)
        all_articles.extend(gh)
        conn_log.execute(
            "INSERT INTO fetch_log (source,fetched_at,article_count) "
            "VALUES (?,?,?)", ("GitHub Trending", now, len(gh)))

    conn_log.commit()
    conn_log.close()

    saved = save_articles(all_articles)
    return {
        "fetched": len(all_articles),
        "saved": saved,
        "sources": len(RSS_FEEDS) + 4,
    }


async def periodic_fetch():
    while True:
        try:
            result = await fetch_all()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Fetched {result['fetched']} articles from "
                  f"{result['sources']} sources, saved {result['saved']} new")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetch error: {e}")
        await asyncio.sleep(REFRESH_INTERVAL)


# ─── App ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(periodic_fetch())
    yield
    task.cancel()


app = FastAPI(title="AI-SDLC Intelligence Dashboard", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/articles")
async def api_articles(category: str = "all", limit: int = 300,
                       hours: int = 72):
    return JSONResponse(get_articles(category=category, limit=limit,
                                     hours=hours))


@app.get("/api/stats")
async def api_stats():
    return JSONResponse(get_stats())


@app.post("/api/refresh")
async def api_refresh():
    return JSONResponse(await fetch_all())


@app.get("/api/categories")
async def api_categories():
    return JSONResponse(list(CATEGORIES.keys()) + ["📰 General Dev AI"])


if __name__ == "__main__":
    import uvicorn
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║  AI-SDLC Intelligence Dashboard          ║")
    print("  ║  http://localhost:8501                    ║")
    print("  ╚══════════════════════════════════════════╝")
    print()
    uvicorn.run(app, host="127.0.0.1", port=8501, log_level="info")
