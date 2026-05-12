"""
GitRAG — Streamlit Frontend
GitHub Codebase Q&A powered by RAG

Design system: Flat Dark — GitHub/Linear/Vercel aesthetic
- bg #0d1117 · surface #161b22 · accent #58a6ff
- Inter UI + JetBrains Mono code
- Contrast ≥ 4.5:1 (WCAG AA)
- 8dp spacing rhythm
- Lazy health check (cached 60s) — no error flash on load
- Default API URL points to live HuggingFace Space
"""

import streamlit as st
import requests
import time

# ── Constants ─────────────────────────────────────────────────────────────
DEFAULT_API_URL = "https://yanou16-gitgub-rag.hf.space"

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitRAG",
    page_icon="◈",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── CSS Design System ─────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Design tokens ── */
:root {
  --bg:            #0d1117;
  --bg-surface:    #161b22;
  --bg-code:       #1c2128;
  --border:        #30363d;
  --border-subtle: #21262d;
  --text-1:        #e6edf3;
  --text-2:        #8b949e;
  --text-3:        #6e7681;
  --accent:        #58a6ff;
  --accent-dim:    rgba(88,166,255,0.12);
  --success:       #3fb950;
  --success-dim:   rgba(63,185,80,0.1);
  --warning:       #d29922;
  --warning-dim:   rgba(210,153,34,0.1);
  --error:         #f85149;
  --error-dim:     rgba(248,81,73,0.08);
  --purple:        #bc8cff;
  --purple-dim:    rgba(188,140,255,0.12);
  --r-sm: 4px; --r-md: 8px; --r-lg: 12px;
  --font: 'Inter', system-ui, -apple-system, sans-serif;
  --mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
}

/* ── Base ── */
.stApp { background: var(--bg) !important; font-family: var(--font) !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2rem 1rem 4rem !important; max-width: 800px !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Text ── */
h1,h2,h3,h4 { font-family: var(--font) !important; font-weight: 600 !important; color: var(--text-1) !important; }
p, li, span, div { font-family: var(--font) !important; }
label { color: var(--text-2) !important; font-size: 12px !important; font-weight: 500 !important; letter-spacing: 0.04em !important; }

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    color: var(--text-1) !important;
    font-family: var(--font) !important;
    font-size: 14px !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-dim) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color: var(--text-3) !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--accent) !important;
    border: none !important;
    border-radius: var(--r-md) !important;
    color: #0d1117 !important;
    font-family: var(--font) !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    transition: background 0.15s, transform 0.1s !important;
    cursor: pointer !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover { background: #79b8ff !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* Secondary style via key trick */
.stButton [kind="secondary"] > button,
button[data-testid*="secondary"] {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-1) !important;
}

/* ── Checkboxes / Sliders ── */
.stCheckbox label { font-size: 13px !important; color: var(--text-1) !important; letter-spacing: 0 !important; }
.stSlider label { font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; color: var(--text-3) !important; }

/* ── Metric ── */
[data-testid="stMetric"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--r-md) !important;
    padding: 12px 16px !important;
}
[data-testid="stMetricLabel"] { color: var(--text-3) !important; font-size: 11px !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }
[data-testid="stMetricValue"] { color: var(--text-1) !important; font-family: var(--mono) !important; font-size: 20px !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: var(--r-md) !important;
}
[data-testid="stExpander"] summary { color: var(--text-2) !important; font-size: 13px !important; }

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid var(--border-subtle) !important; margin: 24px 0 !important; }

/* ── Custom classes ── */

/* Header */
.gr-header { border-bottom: 1px solid var(--border-subtle); padding-bottom: 20px; margin-bottom: 28px; }
.gr-logo { font-size: 22px; font-weight: 700; color: var(--text-1); letter-spacing: -0.5px; font-family: var(--font) !important; }
.gr-logo span { color: var(--accent); }
.gr-tagline { font-size: 13px; color: var(--text-2); margin-top: 4px; line-height: 1.5; }

/* Section label */
.gr-label {
    font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
    text-transform: uppercase; color: var(--text-3); margin-bottom: 8px;
}

/* Status dots */
.dot-ok  { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--success); margin-right:6px; box-shadow:0 0 6px rgba(63,185,80,.5); }
.dot-err { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--error);   margin-right:6px; }
.dot-chk { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--warning); margin-right:6px; animation:blink 2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

/* Alerts */
.gr-ok   { background:var(--success-dim); border:1px solid rgba(63,185,80,.3);  border-radius:var(--r-md); padding:11px 14px; color:#3fb950; font-size:13px; margin:8px 0; }
.gr-err  { background:var(--error-dim);   border:1px solid rgba(248,81,73,.3); border-radius:var(--r-md); padding:11px 14px; color:#f85149; font-size:13px; margin:8px 0; }
.gr-info { background:var(--accent-dim);  border:1px solid rgba(88,166,255,.2); border-radius:var(--r-md); padding:11px 14px; color:var(--text-2); font-size:13px; margin:8px 0; }

/* Answer box */
.gr-answer {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--r-lg);
    padding: 20px 22px;
    font-size: 14px; line-height: 1.75;
    color: var(--text-1); margin: 12px 0;
    white-space: pre-wrap; word-break: break-word;
}

/* Source card */
.gr-source {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--r-md);
    padding: 13px 15px; margin-bottom: 8px;
    transition: border-color .15s;
}
.gr-source:hover { border-color: var(--border); }
.gr-path { font-family: var(--mono); font-size: 12px; color: var(--accent); font-weight: 500; margin-bottom: 5px; }
.gr-meta { display:flex; gap:10px; align-items:center; margin-bottom:8px; flex-wrap:wrap; }
.gr-excerpt {
    font-family: var(--mono); font-size: 11.5px; color: var(--text-2);
    background: var(--bg-code); border-radius: var(--r-sm); padding: 8px 11px;
    line-height: 1.55; overflow:hidden;
    display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical;
}

/* Badges */
.b { display:inline-flex; align-items:center; padding:2px 8px; border-radius:20px; font-size:11px; font-weight:600; }
.b-blue   { background:var(--accent-dim);   color:#58a6ff; border:1px solid rgba(88,166,255,.3); }
.b-purple { background:var(--purple-dim);   color:#bc8cff; border:1px solid rgba(188,140,255,.3); }
.b-green  { background:var(--success-dim);  color:#3fb950; border:1px solid rgba(63,185,80,.3); }
.b-gray   { background:rgba(110,118,129,.12); color:#8b949e; border:1px solid rgba(110,118,129,.25); }
.b-orange { background:var(--warning-dim);  color:#d29922; border:1px solid rgba(210,153,34,.3); }

/* Score coloring */
.sc-hi { color:#3fb950 !important; } .sc-md { color:#d29922 !important; } .sc-lo { color:#6e7681 !important; }

/* Empty state */
.gr-empty { text-align:center; padding:52px 24px; }
.gr-empty-icon { font-size:36px; opacity:.35; margin-bottom:14px; }
.gr-empty-title { font-size:15px; font-weight:600; color:var(--text-2); margin-bottom:8px; }
.gr-empty-desc { font-size:13px; color:var(--text-3); line-height:1.6; max-width:360px; margin:0 auto 20px; }
.gr-chips { display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }
.gr-chip { background:var(--bg-surface); border:1px solid var(--border); border-radius:20px; padding:4px 12px; font-size:11.5px; color:var(--text-2); font-family:var(--mono); }

/* Code in answer */
.gr-answer code { font-family:var(--mono) !important; font-size:12px !important; background:var(--bg-code) !important; padding:2px 5px !important; border-radius:3px !important; color:var(--accent) !important; }
</style>
"""

# ── Helpers ───────────────────────────────────────────────────────────────
def api_call(base: str, method: str, endpoint: str, payload: dict = None, timeout: int = 120):
    url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        if method == "POST":
            r = requests.post(url, json=payload, timeout=timeout)
        else:
            r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to `{base}`. Is the API running?"
    except requests.exceptions.Timeout:
        return None, "Request timed out. The repo may be large — try again."
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        # Try to extract the real error message from the response body
        raw = e.response.text or ""
        try:
            body = e.response.json()
            detail = body.get("detail", body)
            if isinstance(detail, dict):
                code = detail.get("code", "")
                msg  = detail.get("detail", str(detail))
                if code == "REPO_NOT_INDEXED":
                    return None, "REPO_NOT_INDEXED"
                return None, f"[{status}] {msg}"
            if isinstance(detail, str):
                if "REPO_NOT_INDEXED" in detail:
                    return None, "REPO_NOT_INDEXED"
                return None, f"[{status}] {detail}"
            return None, f"[{status}] {detail}"
        except Exception:
            # Raw response (e.g. HTML 502 from HF proxy)
            snippet = raw[:300].strip() if raw else "No response body"
            return None, f"[{status}] {snippet}"
    except Exception as e:
        return None, str(e)


def pipeline_badge(p: str) -> str:
    if "rerank" in p and "hybrid" in p:
        return '<span class="b b-purple">hybrid + rerank</span>'
    if "hybrid" in p:
        return '<span class="b b-blue">hybrid</span>'
    if "rerank" in p:
        return '<span class="b b-orange">semantic + rerank</span>'
    return '<span class="b b-gray">semantic</span>'


def score_cls(v: float) -> str:
    return "sc-hi" if v >= 0.8 else ("sc-md" if v >= 0.5 else "sc-lo")


# ── Session state ─────────────────────────────────────────────────────────
DEFAULTS = {
    "api_url":        DEFAULT_API_URL,
    "repo_url":       "",
    "repo_indexed":   False,
    "answer":         None,
    "sources":        [],
    "metrics":        {},
    "health_ok":      None,
    "health_data":    {},
    "health_ts":      0.0,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── CSS inject ────────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="margin-bottom:16px">'
        '<div style="font-size:16px;font-weight:700;color:#e6edf3;letter-spacing:-.3px">◈ GitRAG</div>'
        '<div style="font-size:11px;color:#6e7681;margin-top:2px">GitHub Codebase Q&A</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── API URL ──
    st.markdown('<div class="gr-label">API Endpoint</div>', unsafe_allow_html=True)
    new_url = st.text_input(
        "api_url_input", label_visibility="collapsed",
        value=st.session_state.api_url,
        placeholder="https://yanou16-gitgub-rag.hf.space",
        key="api_url_input",
    )
    if new_url and new_url != st.session_state.api_url:
        st.session_state.api_url  = new_url
        st.session_state.health_ok = None
        st.session_state.health_ts  = 0.0

    # ── Health (cached 60 s) ──
    now = time.time()
    if now - st.session_state.health_ts > 60 or st.session_state.health_ok is None:
        data, err = api_call(st.session_state.api_url, "GET", "/health", timeout=8)
        st.session_state.health_ok   = (data is not None and data.get("status") == "healthy")
        st.session_state.health_data = data or {}
        st.session_state.health_ts   = now

    if st.session_state.health_ok:
        v = st.session_state.health_data.get("version", "1.0")
        q = st.session_state.health_data.get("total_queries", 0)
        st.markdown(
            f'<div style="display:flex;align-items:center;margin:8px 0 2px">'
            f'<span class="dot-ok"></span>'
            f'<span style="font-size:12px;color:#3fb950;font-weight:500">API Online</span>'
            f'</div>'
            f'<div style="font-size:11px;color:#6e7681;padding-left:13px;margin-bottom:8px">'
            f'v{v} · {q} queries served</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="display:flex;align-items:center;margin:8px 0 2px">'
            '<span class="dot-err"></span>'
            '<span style="font-size:12px;color:#f85149;font-weight:500">Offline</span>'
            '</div>'
            '<div style="font-size:11px;color:#6e7681;padding-left:13px;margin-bottom:8px">'
            'Check the URL above</div>',
            unsafe_allow_html=True,
        )

    if st.button("Refresh Status", use_container_width=True):
        st.session_state.health_ts = 0.0
        st.rerun()

    st.markdown("---")

    # ── Search settings ──
    st.markdown('<div class="gr-label">Search Settings</div>', unsafe_allow_html=True)
    k             = st.slider("Results (k)", 1, 20, 5)
    use_hybrid    = st.checkbox("Hybrid search  (BM25 + RRF)", value=True)
    use_reranking = st.checkbox("Cohere reranking", value=True)

    st.markdown("---")

    # ── Index settings ──
    st.markdown('<div class="gr-label">Index Settings</div>', unsafe_allow_html=True)
    max_files     = st.slider("Max files", 10, 300, 100)
    branch        = st.text_input("Branch", value="main", placeholder="main")
    force_reindex = st.checkbox("Force re-index")

    st.markdown("---")
    st.markdown(
        '<div style="font-size:11px;color:#6e7681;line-height:1.7">'
        'Pipeline<br>'
        '<span style="color:#8b949e">GitHub → AST chunks<br>'
        '→ ChromaDB (HNSW)<br>'
        '→ BM25 + RRF fusion<br>'
        '→ Cohere rerank<br>'
        '→ Groq llama-3.3-70b</span>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────
# Header
st.markdown(
    '<div class="gr-header">'
    '<div class="gr-logo">◈ Git<span>RAG</span></div>'
    '<div class="gr-tagline">'
    'Ask natural-language questions about any public GitHub repository.<br>'
    'Answers grounded in actual source code — exact file paths &amp; line numbers.'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Step 1 — Repo URL + Index ─────────────────────────────────────────────
st.markdown('<div class="gr-label">Repository URL</div>', unsafe_allow_html=True)

col_url, col_btn = st.columns([5, 1])
with col_url:
    repo_url = st.text_input(
        "repo_url_main", label_visibility="collapsed",
        value=st.session_state.repo_url,
        placeholder="https://github.com/owner/repo",
    )
    if repo_url != st.session_state.repo_url:
        st.session_state.repo_url     = repo_url
        st.session_state.repo_indexed = False
        st.session_state.answer       = None
        st.session_state.sources      = []

with col_btn:
    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
    index_clicked = st.button("Index", use_container_width=True)

# Index action
if index_clicked:
    repo = st.session_state.repo_url.strip()
    if not repo.startswith("https://github.com/"):
        st.markdown(
            '<div class="gr-err">Enter a valid GitHub URL — <code>https://github.com/owner/repo</code></div>',
            unsafe_allow_html=True,
        )
    elif not st.session_state.health_ok:
        st.markdown(
            f'<div class="gr-err">API is offline. Update the endpoint in the sidebar and refresh status.</div>',
            unsafe_allow_html=True,
        )
    else:
        repo_slug = repo.split("github.com/")[-1]
        with st.spinner(f"Indexing {repo_slug} …"):
            data, err = api_call(
                st.session_state.api_url, "POST", "/ingest",
                payload={
                    "repo_url":      repo,
                    "branch":        branch,
                    "max_files":     max_files,
                    "force_reindex": force_reindex,
                },
                timeout=300,
            )

        if data:
            st.session_state.repo_indexed = True
            files  = data.get("files_processed", data.get("files_indexed", "?"))
            chunks = data.get("chunks_indexed",  data.get("chunks_stored",  "?"))
            cached = data.get("already_indexed", False)
            msg = (
                f"Already indexed — using cached index."
                if cached else
                f"Indexed <strong>{files} files</strong> · <strong>{chunks} chunks</strong>"
            )
            st.markdown(f'<div class="gr-ok">{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="gr-err">{err}</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Step 2 — Question ─────────────────────────────────────────────────────
st.markdown('<div class="gr-label">Question</div>', unsafe_allow_html=True)

question = st.text_area(
    "question_input", label_visibility="collapsed",
    placeholder=(
        "How does authentication work?\n"
        "Where is JWT token validation?\n"
        "Explain the database connection pooling strategy…"
    ),
    height=96,
)

ask_clicked = st.button("Ask Question", type="primary")

if ask_clicked:
    repo = st.session_state.repo_url.strip()
    q    = (question or "").strip()

    if not repo:
        st.markdown('<div class="gr-err">Enter a GitHub repository URL first.</div>', unsafe_allow_html=True)
    elif len(q) < 3:
        st.markdown('<div class="gr-err">Question must be at least 3 characters.</div>', unsafe_allow_html=True)
    elif not st.session_state.health_ok:
        st.markdown('<div class="gr-err">API is offline — check the sidebar.</div>', unsafe_allow_html=True)
    else:
        with st.spinner("Searching codebase…"):
            data, err = api_call(
                st.session_state.api_url, "POST", "/query",
                payload={
                    "repo_url":      repo,
                    "question":      q,
                    "k":             k,
                    "use_hybrid":    use_hybrid,
                    "use_reranking": use_reranking,
                },
                timeout=120,
            )

        if data:
            st.session_state.answer  = data.get("answer", "")
            st.session_state.sources = data.get("sources", [])
            st.session_state.metrics = {
                "latency_ms":  data.get("latency_ms", 0),
                "tokens_used": data.get("tokens_used", 0),
                "k_retrieved": data.get("k_retrieved", 0),
                "pipeline":    data.get("pipeline", "semantic"),
            }
        elif err == "REPO_NOT_INDEXED":
            st.markdown(
                '<div class="gr-err">Repository not indexed yet — click <strong>Index</strong> first.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f'<div class="gr-err">{err}</div>', unsafe_allow_html=True)


# ── Results ───────────────────────────────────────────────────────────────
if st.session_state.answer:
    m = st.session_state.metrics
    pipeline = m.get("pipeline", "semantic")

    # Metrics row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latency",  f"{m.get('latency_ms', 0):.0f} ms")
    c2.metric("Tokens",   m.get("tokens_used", 0))
    c3.metric("Sources",  m.get("k_retrieved", 0))
    c4.metric("Pipeline", pipeline)

    st.markdown("---")

    # Answer
    st.markdown('<div class="gr-label">Answer</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="gr-answer">{st.session_state.answer}</div>',
        unsafe_allow_html=True,
    )

    # Sources
    sources = st.session_state.sources
    if sources:
        st.markdown(
            f'<div class="gr-label" style="margin-top:20px">Sources &nbsp;'
            f'<span style="color:#8b949e;font-weight:400;text-transform:none;letter-spacing:0;font-size:12px">({len(sources)} chunks)</span>'
            f'&nbsp;{pipeline_badge(pipeline)}</div>',
            unsafe_allow_html=True,
        )

        for src in sources:
            path       = src.get("file_path", "unknown")
            start      = src.get("start_line")
            end        = src.get("end_line")
            lang       = src.get("language", "")
            rerank_sc  = src.get("rerank_score")
            sim_sc     = src.get("similarity_score", 0.0)
            excerpt    = (src.get("excerpt") or "").strip()

            disp_score  = rerank_sc if rerank_sc is not None else sim_sc
            score_label = "rerank" if rerank_sc is not None else "sim"
            lines_str   = f"L{start}–{end}" if start and end else ""
            sc          = score_cls(disp_score)

            lang_badge = f'<span class="b b-gray">{lang}</span>' if lang else ""
            line_span  = f'<span style="color:var(--text-3);font-size:11px">{lines_str}</span>' if lines_str else ""
            score_span = (
                f'<span class="{sc}" style="font-size:11px;font-weight:600;margin-left:auto">'
                f'{score_label} {disp_score:.3f}</span>'
            )

            st.markdown(
                f'<div class="gr-source">'
                f'  <div class="gr-path">{path}</div>'
                f'  <div class="gr-meta">{lang_badge}{line_span}{score_span}</div>'
                f'  <div class="gr-excerpt">{excerpt}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

else:
    # ── Empty state ──
    st.markdown(
        '<div class="gr-empty">'
        '  <div class="gr-empty-icon">⟨/⟩</div>'
        '  <div class="gr-empty-title">Ready to search your codebase</div>'
        '  <div class="gr-empty-desc">'
        '    Paste a GitHub repo URL above, click Index, then ask any question about the code.'
        '  </div>'
        '  <div class="gr-chips">'
        '    <span class="gr-chip">tiangolo/fastapi</span>'
        '    <span class="gr-chip">pallets/flask</span>'
        '    <span class="gr-chip">django/django</span>'
        '    <span class="gr-chip">yanou16/Git_RAG</span>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )
