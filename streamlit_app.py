"""
GitRAG — Streamlit Frontend
GitHub Codebase Q&A powered by RAG (Retrieval-Augmented Generation)

Design principles applied (UI/UX Pro Max):
- Dark developer tool aesthetic (#0d1117 bg, #2563eb accent, #10b981 success)
- Contrast ratios ≥ 4.5:1 for all text (WCAG AA)
- 8dp spacing rhythm throughout
- Loading feedback within 150ms (spinners on every async call)
- Empty states with clear guidance
- Error messages with recovery path
- Semantic color: blue=info, green=success, red=error, amber=warning
"""

import streamlit as st
import requests
import json
import time

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitRAG — Codebase Q&A",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design tokens & global CSS ────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Base dark theme ── */
  [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #e6edf3;
  }
  [data-testid="stSidebar"] {
    background-color: #161b22;
    border-right: 1px solid #21262d;
  }
  [data-testid="stSidebar"] * { color: #c9d1d9 !important; }

  /* ── Typography ── */
  h1, h2, h3 { color: #e6edf3 !important; letter-spacing: -0.02em; }
  p, label, span { color: #8b949e; }

  /* ── Inputs ── */
  [data-testid="stTextInput"] input,
  [data-testid="stTextArea"] textarea,
  [data-testid="stSelectbox"] select {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
  }
  [data-testid="stTextInput"] input:focus,
  [data-testid="stTextArea"] textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
  }

  /* ── Buttons ── */
  [data-testid="stButton"] > button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    transition: all 150ms ease-out !important;
    min-height: 44px !important;  /* touch target minimum */
  }
  [data-testid="stButton"] > button:hover {
    background-color: #1d4ed8 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
  }
  [data-testid="stButton"] > button:active { transform: translateY(0); }

  /* ── Dividers ── */
  hr { border-color: #21262d !important; margin: 24px 0; }

  /* ── Source cards ── */
  .source-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 150ms ease-out;
  }
  .source-card:hover { border-color: #30363d; }
  .source-card .file-path {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 13px;
    color: #79c0ff;
    font-weight: 500;
  }
  .source-card .lines {
    font-size: 12px;
    color: #8b949e;
    margin-top: 4px;
  }
  .source-card .excerpt {
    font-family: monospace;
    font-size: 12px;
    color: #8b949e;
    background: #0d1117;
    border-radius: 6px;
    padding: 10px 12px;
    margin-top: 12px;
    white-space: pre-wrap;
    word-break: break-all;
    border-left: 3px solid #21262d;
  }

  /* ── Score badge ── */
  .score-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
  .score-high  { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
  .score-mid   { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
  .score-low   { background: rgba(107,114,128,0.15); color: #6b7280; border: 1px solid rgba(107,114,128,0.3); }

  /* ── Pipeline badge ── */
  .pipeline-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  .pipeline-hybrid-rerank { background: rgba(139,92,246,0.15); color: #a78bfa; border: 1px solid rgba(139,92,246,0.3); }
  .pipeline-hybrid        { background: rgba(37,99,235,0.15);  color: #60a5fa; border: 1px solid rgba(37,99,235,0.3); }
  .pipeline-semantic      { background: rgba(107,114,128,0.15); color: #9ca3af; border: 1px solid rgba(107,114,128,0.3); }

  /* ── Metric cards ── */
  .metric-row {
    display: flex;
    gap: 12px;
    margin: 16px 0;
    flex-wrap: wrap;
  }
  .metric-card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 18px;
    min-width: 120px;
  }
  .metric-card .label {
    font-size: 11px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
  }
  .metric-card .value {
    font-size: 18px;
    font-weight: 700;
    color: #e6edf3;
    margin-top: 4px;
    font-variant-numeric: tabular-nums;
  }

  /* ── Alert boxes ── */
  .alert-error {
    background: rgba(239,68,68,0.1);
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 8px;
    padding: 14px 18px;
    color: #fca5a5;
    font-size: 14px;
  }
  .alert-success {
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 8px;
    padding: 14px 18px;
    color: #6ee7b7;
    font-size: 14px;
  }
  .alert-info {
    background: rgba(37,99,235,0.1);
    border: 1px solid rgba(37,99,235,0.3);
    border-radius: 8px;
    padding: 14px 18px;
    color: #93c5fd;
    font-size: 14px;
  }

  /* ── Answer box ── */
  .answer-box {
    background: #161b22;
    border: 1px solid #21262d;
    border-left: 3px solid #2563eb;
    border-radius: 10px;
    padding: 20px 24px;
    font-size: 15px;
    line-height: 1.7;
    color: #c9d1d9;
  }

  /* ── Section headers ── */
  .section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
  }
  .section-number {
    width: 28px; height: 28px;
    background: #2563eb;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700; color: white;
    flex-shrink: 0;
  }

  /* ── Checkbox / radio ── */
  [data-testid="stCheckbox"] label { color: #c9d1d9 !important; }

  /* ── Slider ── */
  [data-testid="stSlider"] { color: #c9d1d9; }

  /* ── Remove Streamlit branding ── */
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding-top: 2rem; max-width: 1200px; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────
for key, default in {
    "repo_url": "",
    "repo_indexed": False,
    "last_answer": None,
    "last_sources": [],
    "last_metrics": {},
    "ingest_stats": None,
    "api_healthy": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Helpers ───────────────────────────────────────────────────────────────
def api_post(url: str, payload: dict, timeout: int = 120) -> tuple[dict | None, str | None]:
    """POST to API, returns (data, error_message)."""
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        if r.status_code == 200:
            return r.json(), None
        try:
            detail = r.json().get("detail", r.text)
            if isinstance(detail, dict):
                detail = detail.get("detail", str(detail))
        except Exception:
            detail = r.text
        return None, f"HTTP {r.status_code} — {detail}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the API. Is the server running?"
    except requests.exceptions.Timeout:
        return None, "Request timed out. The repo may be large — try again."
    except Exception as e:
        return None, str(e)


def api_get(url: str, timeout: int = 10) -> tuple[dict | None, str | None]:
    try:
        r = requests.get(url, timeout=timeout)
        return r.json() if r.status_code == 200 else None, None
    except Exception:
        return None, "Cannot reach the API."


def score_class(score: float) -> str:
    if score >= 0.75: return "score-high"
    if score >= 0.5:  return "score-mid"
    return "score-low"


def pipeline_class(pipeline: str) -> str:
    if "rerank" in pipeline: return "pipeline-hybrid-rerank"
    if "hybrid" in pipeline: return "pipeline-hybrid"
    return "pipeline-semantic"


def pipeline_label(pipeline: str) -> str:
    mapping = {
        "hybrid+rerank": "Hybrid + Rerank",
        "semantic+rerank": "Semantic + Rerank",
        "hybrid": "Hybrid BM25",
        "semantic": "Semantic",
    }
    return mapping.get(pipeline, pipeline)


# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ GitRAG")
    st.markdown("<p style='color:#6b7280;font-size:13px;margin-top:-8px'>GitHub Codebase Q&A via RAG</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### Configuration")
    api_url = st.text_input(
        "API URL",
        value="http://localhost:7860",
        help="URL of the GitRAG FastAPI backend",
        placeholder="http://localhost:7860"
    )
    api_url = api_url.rstrip("/")

    # Health check
    if st.button("Check API Health", use_container_width=True):
        health, err = api_get(f"{api_url}/health")
        if health:
            status = health.get("status", "unknown")
            color = "#10b981" if status == "healthy" else "#f59e0b"
            st.markdown(f"""
            <div style='background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.2);
                        border-radius:8px;padding:12px;margin-top:8px;'>
              <div style='color:{color};font-weight:700;font-size:13px;'>● {status.upper()}</div>
              <div style='color:#6b7280;font-size:12px;margin-top:4px;'>
                v{health.get('version','?')} · up {int(health.get('uptime_seconds',0))}s
              </div>
              <div style='color:#6b7280;font-size:12px;'>
                ChromaDB: {health.get('chroma_status','?')}
              </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='alert-error'>❌ {err}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Metrics
    st.markdown("### Live Metrics")
    if st.button("Refresh Metrics", use_container_width=True):
        metrics, _ = api_get(f"{api_url}/metrics")
        if metrics:
            st.markdown(f"""
            <div style='display:flex;flex-direction:column;gap:8px;margin-top:8px;'>
              <div style='display:flex;justify-content:space-between;'>
                <span style='color:#6b7280;font-size:12px;'>Indexed repos</span>
                <span style='color:#e6edf3;font-weight:600;font-size:13px;'>{metrics.get('indexed_repos',0)}</span>
              </div>
              <div style='display:flex;justify-content:space-between;'>
                <span style='color:#6b7280;font-size:12px;'>Total chunks</span>
                <span style='color:#e6edf3;font-weight:600;font-size:13px;'>{metrics.get('total_chunks',0):,}</span>
              </div>
              <div style='display:flex;justify-content:space-between;'>
                <span style='color:#6b7280;font-size:12px;'>Total queries</span>
                <span style='color:#e6edf3;font-weight:600;font-size:13px;'>{metrics.get('total_queries',0)}</span>
              </div>
              <div style='display:flex;justify-content:space-between;'>
                <span style='color:#6b7280;font-size:12px;'>Avg latency</span>
                <span style='color:#e6edf3;font-weight:600;font-size:13px;'>{metrics.get('avg_query_latency_ms',0):.0f} ms</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style='font-size:12px;color:#484f58;line-height:1.6;'>
      <strong style='color:#6b7280;'>About</strong><br/>
      GitRAG indexes any public GitHub repo and answers developer questions with cited sources.<br/><br/>
      <strong style='color:#6b7280;'>Pipeline</strong><br/>
      GitHub API → AST Chunking → OpenAI Embeddings → ChromaDB → BM25+RRF → Cohere Rerank → Groq LLM
    </div>
    """, unsafe_allow_html=True)


# ── Main content ──────────────────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:32px;'>
  <h1 style='font-size:2rem;font-weight:800;color:#e6edf3;margin-bottom:6px;'>
    ⚡ GitRAG
  </h1>
  <p style='color:#8b949e;font-size:16px;margin:0;'>
    Ask questions about any public GitHub repository in natural language.
    Get answers with exact file paths and line numbers.
  </p>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1, 1], gap="large")

# ── LEFT COLUMN: Index a repo ─────────────────────────────────────────────
with col_left:
    st.markdown("""
    <div class='section-header'>
      <div class='section-number'>1</div>
      <h3 style='margin:0;font-size:1.1rem;color:#e6edf3;'>Index a Repository</h3>
    </div>
    """, unsafe_allow_html=True)

    repo_url_input = st.text_input(
        "GitHub Repository URL",
        value=st.session_state.repo_url,
        placeholder="https://github.com/tiangolo/fastapi",
        label_visibility="collapsed",
    )

    with st.expander("Advanced options", expanded=False):
        col_b, col_m = st.columns(2)
        with col_b:
            branch = st.text_input("Branch", value="main", help="Branch to index")
        with col_m:
            max_files = st.slider("Max files", 10, 500, 100, 10,
                                  help="Limit files to index (performance)")
        force_reindex = st.checkbox(
            "Force re-index",
            help="Re-index even if this repo is already cached"
        )

    ingest_btn = st.button("Index Repository", use_container_width=True, type="primary")

    if ingest_btn:
        if not repo_url_input or "github.com" not in repo_url_input:
            st.markdown("<div class='alert-error'>❌ Please enter a valid GitHub URL (github.com/...)</div>",
                        unsafe_allow_html=True)
        else:
            with st.spinner("Fetching files, chunking & embedding... This may take 30–120 seconds for large repos."):
                data, err = api_post(f"{api_url}/ingest", {
                    "repo_url": repo_url_input,
                    "branch": branch,
                    "max_files": max_files,
                    "force_reindex": force_reindex,
                })

            if err:
                st.markdown(f"<div class='alert-error'>❌ {err}</div>", unsafe_allow_html=True)
            elif data:
                st.session_state.repo_url = repo_url_input
                st.session_state.repo_indexed = True
                st.session_state.ingest_stats = data

                if data.get("was_cached"):
                    st.markdown("""
                    <div class='alert-info'>
                      ⚡ Already indexed — using cached version. Enable "Force re-index" to refresh.
                    </div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class='alert-success'>
                      ✅ Indexed successfully in {data.get('duration_ms', 0) / 1000:.1f}s
                    </div>""", unsafe_allow_html=True)

    # Show ingest stats if available
    if st.session_state.ingest_stats:
        d = st.session_state.ingest_stats
        st.markdown(f"""
        <div class='metric-row'>
          <div class='metric-card'>
            <div class='label'>Files</div>
            <div class='value'>{d.get('files_indexed', 0)}</div>
          </div>
          <div class='metric-card'>
            <div class='label'>Chunks</div>
            <div class='value'>{d.get('chunks_stored', 0):,}</div>
          </div>
          <div class='metric-card'>
            <div class='label'>Duration</div>
            <div class='value'>{d.get('duration_ms', 0) / 1000:.1f}s</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        if d.get("warnings"):
            for w in d["warnings"]:
                st.markdown(f"""
                <div style='background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);
                            border-radius:8px;padding:10px 14px;margin-top:8px;
                            color:#fcd34d;font-size:13px;'>
                  ⚠️ {w}
                </div>""", unsafe_allow_html=True)

        repo_id = d.get("repo_id", "")
        st.markdown(f"""
        <div style='margin-top:12px;font-size:12px;color:#484f58;font-family:monospace;'>
          repo_id: {repo_id}
        </div>""", unsafe_allow_html=True)


# ── RIGHT COLUMN: Ask a question ──────────────────────────────────────────
with col_right:
    st.markdown("""
    <div class='section-header'>
      <div class='section-number'>2</div>
      <h3 style='margin:0;font-size:1.1rem;color:#e6edf3;'>Ask a Question</h3>
    </div>
    """, unsafe_allow_html=True)

    question = st.text_area(
        "Your question",
        placeholder="How does authentication work?\nWhere is the database connection pool configured?\nWhat does the retry decorator do?",
        height=100,
        label_visibility="collapsed",
    )

    with st.expander("Search options", expanded=False):
        col_k, col_dummy = st.columns(2)
        with col_k:
            k = st.slider("Sources to retrieve (k)", 1, 10, 5,
                          help="How many code chunks to retrieve before generating the answer")
        use_hybrid   = st.checkbox("Hybrid search (BM25 + semantic)", value=True,
                                   help="Combines keyword search with semantic search via RRF fusion")
        use_reranking = st.checkbox("Cohere reranking", value=True,
                                    help="Re-scores retrieved chunks with Cohere Rerank v3.5 for higher precision")

    query_btn = st.button("Ask", use_container_width=True, type="primary")

    if query_btn:
        repo_to_query = repo_url_input or st.session_state.repo_url
        if not question or len(question.strip()) < 3:
            st.markdown("<div class='alert-error'>❌ Please enter a question (at least 3 characters).</div>",
                        unsafe_allow_html=True)
        elif not repo_to_query or "github.com" not in repo_to_query:
            st.markdown("<div class='alert-error'>❌ Please index a repository first (Step 1).</div>",
                        unsafe_allow_html=True)
        else:
            with st.spinner("Searching codebase and generating answer..."):
                data, err = api_post(f"{api_url}/query", {
                    "repo_url": repo_to_query,
                    "question": question.strip(),
                    "k": k,
                    "use_hybrid": use_hybrid,
                    "use_reranking": use_reranking,
                })

            if err:
                st.markdown(f"<div class='alert-error'>❌ {err}</div>", unsafe_allow_html=True)
            elif data:
                st.session_state.last_answer  = data.get("answer", "")
                st.session_state.last_sources = data.get("sources", [])
                st.session_state.last_metrics = {
                    "latency_ms":   data.get("latency_ms", 0),
                    "tokens_used":  data.get("tokens_used", 0),
                    "model":        data.get("model", ""),
                    "k_retrieved":  data.get("k_retrieved", 0),
                    "pipeline":     data.get("pipeline", "semantic"),
                }

    # Display answer
    if st.session_state.last_answer:
        m = st.session_state.last_metrics
        pipeline = m.get("pipeline", "semantic")

        # Metrics row
        p_cls   = pipeline_class(pipeline)
        p_label = pipeline_label(pipeline)
        st.markdown(f"""
        <div class='metric-row'>
          <div class='metric-card'>
            <div class='label'>Latency</div>
            <div class='value'>{m.get('latency_ms', 0):.0f} ms</div>
          </div>
          <div class='metric-card'>
            <div class='label'>Tokens</div>
            <div class='value'>{m.get('tokens_used', 0):,}</div>
          </div>
          <div class='metric-card'>
            <div class='label'>Sources</div>
            <div class='value'>{m.get('k_retrieved', 0)}</div>
          </div>
          <div class='metric-card' style='border-color:rgba(37,99,235,0.25);'>
            <div class='label'>Pipeline</div>
            <div style='margin-top:6px;'>
              <span class='pipeline-badge {p_cls}'>{p_label}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Answer
        import html
        answer_html = html.escape(st.session_state.last_answer).replace("\n", "<br/>")
        st.markdown(f"<div class='answer-box'>{answer_html}</div>", unsafe_allow_html=True)

        # Sources
        if st.session_state.last_sources:
            st.markdown(f"""
            <div style='margin-top:24px;margin-bottom:12px;'>
              <span style='color:#8b949e;font-size:13px;font-weight:600;
                           text-transform:uppercase;letter-spacing:0.08em;'>
                Sources ({len(st.session_state.last_sources)})
              </span>
            </div>
            """, unsafe_allow_html=True)

            for src in st.session_state.last_sources:
                score      = src.get("rerank_score") or src.get("similarity_score", 0)
                score_pct  = f"{score * 100:.1f}%"
                s_cls      = score_class(score)
                lang       = src.get("language", "")
                start_line = src.get("start_line", "?")
                end_line   = src.get("end_line", "?")
                excerpt    = html.escape(src.get("excerpt", "")[:180])

                score_label = "rerank" if src.get("rerank_score") else "similarity"

                st.markdown(f"""
                <div class='source-card'>
                  <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                    <div>
                      <div class='file-path'>{html.escape(src.get('file_path', ''))}</div>
                      <div class='lines'>Lines {start_line}–{end_line} · {lang}</div>
                    </div>
                    <span class='score-badge {s_cls}'>{score_label} {score_pct}</span>
                  </div>
                  <div class='excerpt'>{excerpt}</div>
                </div>
                """, unsafe_allow_html=True)


# ── Empty state when nothing indexed yet ──────────────────────────────────
if not st.session_state.repo_url and not st.session_state.last_answer:
    st.markdown("---")
    st.markdown("""
    <div style='text-align:center;padding:48px 24px;'>
      <div style='font-size:48px;margin-bottom:16px;'>⚡</div>
      <h3 style='color:#e6edf3;margin-bottom:8px;'>Get started</h3>
      <p style='color:#6b7280;max-width:440px;margin:0 auto;font-size:14px;line-height:1.7;'>
        Paste any public GitHub repo URL in Step 1, click <strong style='color:#c9d1d9;'>Index Repository</strong>,
        then ask a question in Step 2.<br/><br/>
        GitRAG will search the codebase semantically and return answers
        with exact file paths and line numbers.
      </p>
      <div style='margin-top:24px;display:flex;justify-content:center;gap:12px;flex-wrap:wrap;'>
        <code style='background:#161b22;border:1px solid #21262d;border-radius:6px;
                     padding:6px 12px;font-size:12px;color:#8b949e;'>
          github.com/tiangolo/fastapi
        </code>
        <code style='background:#161b22;border:1px solid #21262d;border-radius:6px;
                     padding:6px 12px;font-size:12px;color:#8b949e;'>
          github.com/pallets/flask
        </code>
        <code style='background:#161b22;border:1px solid #21262d;border-radius:6px;
                     padding:6px 12px;font-size:12px;color:#8b949e;'>
          github.com/django/django
        </code>
      </div>
    </div>
    """, unsafe_allow_html=True)
