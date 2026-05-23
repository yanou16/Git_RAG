"""
GitRAG — Streamlit Frontend
GitHub Codebase Q&A powered by RAG

Design system: Google Material Design 3 (Material You)
- Dark color scheme seeded from Google Blue (#1A73E8)
- md.sys.color.* tokens throughout — no raw hex in components
- Google Sans (brand) + Roboto Flex (plain) + JetBrains Mono (code)
- Shape scale: extra-small(4dp) → small(8dp) → medium(12dp) → large(16dp) → full(pill)
- MD3 Filled Button (primary CTA) / Filled Tonal Button (secondary)
- Surface container hierarchy for tonal elevation (dark: tint overlay)
- State layers: hover 8%, focus/press 12% — all via ::before pseudo-element
- Sentence-case button labels (MD3 abolished ALL CAPS from MD2)
- Lazy health check cached 60 s — no flash on load
"""

import streamlit as st
import requests
import time

# ── Constants ─────────────────────────────────────────────────────────────
DEFAULT_API_URL = "https://yanou16-gitgub-rag.hf.space"

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitRAG",
    page_icon="⬡",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── MD3 CSS ───────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto+Flex:opsz,wght@8..144,300;8..144,400;8..144,500;8..144,700&family=JetBrains+Mono:wght@400;500&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

/* ── MD3 Dark Color Scheme — seed: Google Blue #1A73E8 ── */
:root {
  --md-background:                 #101418;
  --md-on-background:              #E2E2E9;

  --md-surface:                    #101418;
  --md-on-surface:                 #E2E2E9;
  --md-surface-variant:            #42474E;
  --md-on-surface-variant:         #C2C7CE;

  --md-surface-c-lowest:           #0B0E12;
  --md-surface-c-low:              #181C20;
  --md-surface-c:                  #1C2026;
  --md-surface-c-high:             #272B30;
  --md-surface-c-highest:          #31353B;

  --md-primary:                    #9ECBFF;
  --md-on-primary:                 #003353;
  --md-primary-container:          #004B76;
  --md-on-primary-container:       #CBE6FF;

  --md-secondary:                  #B5C9DF;
  --md-on-secondary:               #1F333F;
  --md-secondary-container:        #354A57;
  --md-on-secondary-container:     #D1E5F3;

  --md-tertiary:                   #C3C2EA;
  --md-on-tertiary:                #2C2C52;
  --md-tertiary-container:         #434269;
  --md-on-tertiary-container:      #E0DFFF;

  --md-error:                      #FFB4AB;
  --md-on-error:                   #690005;
  --md-error-container:            #5C0007;
  --md-on-error-container:         #FFDAD6;

  --md-outline:                    #8C9198;
  --md-outline-variant:            #42474E;

  /* Custom success (not in MD3 spec) */
  --md-success:                    #86D788;
  --md-success-container:          #1A3A1C;
  --md-on-success-container:       #A2F5A4;

  /* MD3 Shape scale */
  --shape-xs:    4px;
  --shape-sm:    8px;
  --shape-md:    12px;
  --shape-lg:    16px;
  --shape-xl:    28px;
  --shape-full:  9999px;

  /* Typography */
  --font-brand:  'Google Sans', 'Roboto Flex', Roboto, sans-serif;
  --font-plain:  'Roboto Flex', Roboto, sans-serif;
  --font-mono:   'JetBrains Mono', 'Fira Code', monospace;

  /* MD3 Motion — emphasized easing */
  --ease-emphasized: cubic-bezier(0.2, 0, 0, 1);
  --dur-short3:      150ms;
  --dur-medium2:     300ms;
}

/* ── Base ── */
.stApp {
  background: var(--md-background) !important;
  font-family: var(--font-plain) !important;
  color: var(--md-on-background) !important;
}
#MainMenu, footer { visibility: hidden; }
.block-container {
  padding: 2rem 1.5rem 4rem !important;
  max-width: 800px !important;
}

/* ── Sidebar — MD3 Navigation Drawer ── */
[data-testid="stSidebar"] {
  background: var(--md-surface-c-low) !important;
  border-right: 1px solid var(--md-outline-variant) !important;
}

/* ── Global text resets ── */
h1, h2, h3, h4 {
  font-family: var(--font-brand) !important;
  font-weight: 400 !important;
  color: var(--md-on-surface) !important;
}
p, li, span, div { font-family: var(--font-plain) !important; }

/* MD3 Label Medium (persistent field labels) */
label {
  font-family: var(--font-plain) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  line-height: 20px !important;
  letter-spacing: 0.1px !important;
  color: var(--md-on-surface-variant) !important;
}

/* ── MD3 Filled Text Field ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background: var(--md-surface-c-highest) !important;
  border: none !important;
  border-bottom: 1px solid var(--md-outline) !important;
  border-radius: var(--shape-xs) var(--shape-xs) 0 0 !important;
  color: var(--md-on-surface) !important;
  font-family: var(--font-plain) !important;
  font-size: 16px !important;
  padding: 20px 16px 8px !important;
  transition: border-bottom-color var(--dur-short3) var(--ease-emphasized) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-bottom: 2px solid var(--md-primary) !important;
  outline: none !important;
  box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
  color: var(--md-on-surface-variant) !important;
}

/* ── MD3 Filled Tonal Button (default) ── */
.stButton > button {
  background: var(--md-secondary-container) !important;
  color: var(--md-on-secondary-container) !important;
  border: none !important;
  border-radius: var(--shape-full) !important;
  font-family: var(--font-plain) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  letter-spacing: 0.1px !important;
  padding: 10px 24px !important;
  min-height: 40px !important;
  position: relative !important;
  overflow: hidden !important;
  transition: box-shadow var(--dur-short3) var(--ease-emphasized) !important;
}
/* State layer */
.stButton > button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--md-on-secondary-container);
  opacity: 0;
  border-radius: inherit;
  transition: opacity var(--dur-short3) var(--ease-emphasized);
}
.stButton > button:hover::before  { opacity: 0.08; }
.stButton > button:focus-visible::before { opacity: 0.12; }
.stButton > button:active::before { opacity: 0.12; }
.stButton > button:hover {
  box-shadow: 0 1px 2px rgba(0,0,0,.3), 0 1px 3px rgba(0,0,0,.2) !important;
}

/* ── MD3 Filled Button (primary action) ── */
[data-testid="baseButton-primary"] {
  background: var(--md-primary) !important;
  color: var(--md-on-primary) !important;
  border-radius: var(--shape-full) !important;
}
[data-testid="baseButton-primary"]::before {
  background: var(--md-on-primary) !important;
}
[data-testid="baseButton-primary"]:hover {
  box-shadow: 0 1px 2px rgba(0,0,0,.3), 0 2px 6px rgba(0,0,0,.2) !important;
}

/* ── Checkbox ── */
.stCheckbox label {
  font-size: 14px !important;
  font-weight: 400 !important;
  letter-spacing: 0 !important;
  color: var(--md-on-surface) !important;
}

/* ── Slider ── */
.stSlider label {
  font-size: 11px !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px !important;
  text-transform: uppercase !important;
  color: var(--md-on-surface-variant) !important;
}

/* ── Metric — Surface Container card ── */
[data-testid="stMetric"] {
  background: var(--md-surface-c) !important;
  border: none !important;
  border-radius: var(--shape-md) !important;
  padding: 16px !important;
}
[data-testid="stMetricLabel"] {
  font-family: var(--font-plain) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px !important;
  text-transform: none !important;
  color: var(--md-on-surface-variant) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--font-mono) !important;
  font-size: 20px !important;
  font-weight: 500 !important;
  color: var(--md-primary) !important;
}

/* ── Expander — Outlined card ── */
[data-testid="stExpander"] {
  background: var(--md-surface-c-low) !important;
  border: 1px solid var(--md-outline-variant) !important;
  border-radius: var(--shape-md) !important;
}
[data-testid="stExpander"] summary {
  font-family: var(--font-plain) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: var(--md-on-surface-variant) !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--md-outline-variant) !important;
  margin: 24px 0 !important;
}


/* ════════════════════════════════════════════════════════
   CUSTOM MD3 COMPONENTS
════════════════════════════════════════════════════════ */

/* App bar — header */
.m3-app-bar {
  padding-bottom: 24px;
  margin-bottom: 32px;
  border-bottom: 1px solid var(--md-outline-variant);
}
.m3-display {
  font-family: var(--font-brand);
  font-size: 36px;
  font-weight: 400;
  line-height: 44px;
  letter-spacing: -0.25px;
  color: var(--md-on-surface);
  margin-bottom: 6px;
}
.m3-display em {
  font-style: normal;
  color: var(--md-primary);
}
.m3-body-large {
  font-size: 16px;
  font-weight: 400;
  line-height: 24px;
  letter-spacing: 0.5px;
  color: var(--md-on-surface-variant);
}

/* Navigation drawer header */
.m3-nav-header {
  padding-bottom: 20px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--md-outline-variant);
}
.m3-nav-title {
  font-family: var(--font-brand);
  font-size: 22px;
  font-weight: 400;
  line-height: 28px;
  color: var(--md-on-surface);
}
.m3-nav-subtitle {
  font-size: 12px;
  font-weight: 400;
  line-height: 16px;
  letter-spacing: 0.4px;
  color: var(--md-on-surface-variant);
  margin-top: 2px;
}

/* Section label — overline style (uppercase allowed for dense UI organization) */
.m3-overline {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--md-on-surface-variant);
  margin-bottom: 8px;
}

/* Status chip */
.m3-chip-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--shape-full);
  font-size: 13px;
  font-weight: 500;
  line-height: 18px;
  margin: 8px 0 4px;
}
.m3-chip-status--online {
  background: var(--md-success-container);
  color: var(--md-on-success-container);
}
.m3-chip-status--offline {
  background: var(--md-error-container);
  color: var(--md-on-error-container);
}
.m3-chip-status-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.m3-chip-status--online .m3-chip-status-dot {
  animation: m3-pulse 2s infinite;
  box-shadow: 0 0 0 3px rgba(134,215,136,.25);
}
@keyframes m3-pulse {
  0%,100% { opacity:1 } 50% { opacity:.4 }
}
.m3-status-meta {
  font-size: 11px;
  color: var(--md-on-surface-variant);
  padding-left: 2px;
  margin-bottom: 12px;
}

/* Alert banners — MD3 Color Containers */
.m3-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--shape-md);
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
  letter-spacing: 0.25px;
  margin: 8px 0;
}
.m3-banner--success {
  background: var(--md-success-container);
  color: var(--md-on-success-container);
}
.m3-banner--error {
  background: var(--md-error-container);
  color: var(--md-on-error-container);
}
.m3-banner--info {
  background: var(--md-primary-container);
  color: var(--md-on-primary-container);
}
.m3-banner-icon {
  font-family: 'Material Symbols Outlined';
  font-size: 20px;
  flex-shrink: 0;
  font-variation-settings: 'FILL' 1, 'wght' 400;
}

/* Answer — MD3 Elevated card (surface-container + shadow) */
.m3-answer-card {
  background: var(--md-surface-c);
  border-radius: var(--shape-lg);
  padding: 24px;
  font-size: 16px;
  line-height: 1.75;
  color: var(--md-on-surface);
  margin: 12px 0;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 1px 2px rgba(0,0,0,.3), 0 2px 6px rgba(0,0,0,.2);
}
.m3-answer-card code {
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  background: var(--md-surface-c-highest) !important;
  padding: 2px 6px !important;
  border-radius: var(--shape-xs) !important;
  color: var(--md-primary) !important;
}

/* Source cards — MD3 Filled card */
.m3-source-card {
  background: var(--md-surface-c-high);
  border-radius: var(--shape-md);
  padding: 16px;
  margin-bottom: 8px;
  position: relative;
  overflow: hidden;
  transition: background var(--dur-short3) var(--ease-emphasized);
}
.m3-source-card::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--md-on-surface);
  opacity: 0;
  transition: opacity var(--dur-short3) var(--ease-emphasized);
  pointer-events: none;
}
.m3-source-card:hover::before { opacity: 0.08; }
.m3-source-path {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--md-primary);
  margin-bottom: 8px;
  position: relative;
}
.m3-source-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  position: relative;
}
.m3-source-excerpt {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--md-on-surface-variant);
  background: var(--md-surface-c-highest);
  border-radius: var(--shape-xs);
  padding: 10px 12px;
  line-height: 1.6;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  position: relative;
}

/* MD3 Assist Chips */
.m3-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--shape-full);
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
  letter-spacing: 0.1px;
  white-space: nowrap;
}
.m3-chip--primary {
  background: var(--md-primary-container);
  color: var(--md-on-primary-container);
}
.m3-chip--secondary {
  background: var(--md-secondary-container);
  color: var(--md-on-secondary-container);
}
.m3-chip--tertiary {
  background: var(--md-tertiary-container);
  color: var(--md-on-tertiary-container);
}
.m3-chip--surface {
  background: var(--md-surface-c-highest);
  color: var(--md-on-surface-variant);
  border: 1px solid var(--md-outline-variant);
}

/* Score coloring */
.sc-hi { color: var(--md-success) !important; }
.sc-md { color: #FFC166 !important; }
.sc-lo { color: var(--md-on-surface-variant) !important; }

/* Pipeline pill */
.m3-pipeline-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: var(--shape-full);
  font-size: 12px;
  font-weight: 500;
  background: var(--md-tertiary-container);
  color: var(--md-on-tertiary-container);
}

/* Empty state */
.m3-empty {
  text-align: center;
  padding: 64px 24px;
}
.m3-empty-icon {
  font-family: 'Material Symbols Outlined';
  font-size: 72px;
  color: var(--md-on-surface-variant);
  opacity: 0.4;
  margin-bottom: 20px;
  display: block;
  font-variation-settings: 'FILL' 0, 'wght' 200, 'GRAD' -25;
}
.m3-empty-headline {
  font-family: var(--font-brand);
  font-size: 24px;
  font-weight: 400;
  line-height: 32px;
  color: var(--md-on-surface);
  margin-bottom: 8px;
}
.m3-empty-body {
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
  letter-spacing: 0.25px;
  color: var(--md-on-surface-variant);
  max-width: 360px;
  margin: 0 auto 28px;
}
.m3-suggestion-row {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}
.m3-suggestion-chip {
  background: var(--md-surface-c-high);
  border: 1px solid var(--md-outline-variant);
  border-radius: var(--shape-full);
  padding: 6px 14px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 400;
  color: var(--md-secondary);
}

/* Sidebar pipeline info block */
.m3-pipeline-card {
  background: var(--md-surface-c);
  border-radius: var(--shape-md);
  padding: 14px 16px;
  margin-top: 4px;
}
.m3-pipeline-card-title {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--md-on-surface-variant);
  margin-bottom: 8px;
}
.m3-pipeline-step {
  font-size: 12px;
  line-height: 1.9;
  color: var(--md-on-surface-variant);
}
.m3-pipeline-step b {
  color: var(--md-secondary);
  font-weight: 500;
}
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
            snippet = raw[:300].strip() if raw else "No response body"
            return None, f"[{status}] {snippet}"
    except Exception as e:
        return None, str(e)


def pipeline_badge(p: str) -> str:
    if "rerank" in p and "hybrid" in p:
        label = "Hybrid + rerank"
    elif "hybrid" in p:
        label = "Hybrid"
    elif "rerank" in p:
        label = "Semantic + rerank"
    else:
        label = "Semantic"
    return f'<span class="m3-pipeline-pill">{label}</span>'


def score_cls(v: float) -> str:
    return "sc-hi" if v >= 0.8 else ("sc-md" if v >= 0.5 else "sc-lo")


def banner(kind: str, icon: str, text: str) -> str:
    return (
        f'<div class="m3-banner m3-banner--{kind}">'
        f'<span class="m3-banner-icon">{icon}</span>'
        f'<span>{text}</span>'
        f'</div>'
    )


# ── Session state ─────────────────────────────────────────────────────────
DEFAULTS = {
    "api_url":      DEFAULT_API_URL,
    "repo_url":     "",
    "repo_indexed": False,
    "answer":       None,
    "sources":      [],
    "metrics":      {},
    "health_ok":    None,
    "health_data":  {},
    "health_ts":    0.0,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Inject CSS ────────────────────────────────────────────────────────────
st.markdown(CSS, unsafe_allow_html=True)


# ── Sidebar — MD3 Navigation Drawer ──────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="m3-nav-header">'
        '  <div class="m3-nav-title">⬡ GitRAG</div>'
        '  <div class="m3-nav-subtitle">GitHub codebase Q&A</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # API Endpoint
    st.markdown('<div class="m3-overline">API endpoint</div>', unsafe_allow_html=True)
    new_url = st.text_input(
        "api_url_input", label_visibility="collapsed",
        value=st.session_state.api_url,
        placeholder="https://yanou16-gitgub-rag.hf.space",
        key="api_url_input",
    )
    if new_url and new_url != st.session_state.api_url:
        st.session_state.api_url  = new_url
        st.session_state.health_ok = None
        st.session_state.health_ts = 0.0

    # Health check — cached 60 s
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
            '<div class="m3-chip-status m3-chip-status--online">'
            '  <span class="m3-chip-status-dot"></span> API online'
            '</div>'
            f'<div class="m3-status-meta">v{v} · {q} queries served</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="m3-chip-status m3-chip-status--offline">'
            '  <span class="m3-chip-status-dot"></span> Offline'
            '</div>'
            '<div class="m3-status-meta">Check the URL above</div>',
            unsafe_allow_html=True,
        )

    if st.button("Refresh status", use_container_width=True):
        st.session_state.health_ts = 0.0
        st.rerun()

    st.markdown("---")

    # Search settings
    st.markdown('<div class="m3-overline">Search</div>', unsafe_allow_html=True)
    k             = st.slider("Results (k)", 1, 20, 5)
    use_hybrid    = st.checkbox("Hybrid search (BM25 + RRF)", value=True)
    use_reranking = st.checkbox("Cohere reranking", value=True)

    st.markdown("---")

    # Index settings
    st.markdown('<div class="m3-overline">Index</div>', unsafe_allow_html=True)
    max_files     = st.slider("Max files", 10, 300, 100)
    branch        = st.text_input("Branch", value="main", placeholder="main")
    force_reindex = st.checkbox("Force re-index")

    st.markdown("---")

    st.markdown(
        '<div class="m3-pipeline-card">'
        '  <div class="m3-pipeline-card-title">Pipeline</div>'
        '  <div class="m3-pipeline-step">'
        '    <b>GitHub</b> → AST chunks<br>'
        '    → <b>ChromaDB</b> (HNSW)<br>'
        '    → <b>BM25</b> + RRF fusion<br>'
        '    → <b>Cohere</b> rerank<br>'
        '    → <b>Groq</b> llama-3.3-70b'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Main area ─────────────────────────────────────────────────────────────

# App bar header
st.markdown(
    '<div class="m3-app-bar">'
    '  <div class="m3-display">⬡ Git<em>RAG</em></div>'
    '  <div class="m3-body-large">'
    '    Ask natural-language questions about any public GitHub repository.<br>'
    '    Answers grounded in actual source code — exact file paths &amp; line numbers.'
    '  </div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Step 1 — Repository URL ───────────────────────────────────────────────
st.markdown('<div class="m3-overline">Repository URL</div>', unsafe_allow_html=True)

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
            banner("error", "error", "Enter a valid GitHub URL — <code>https://github.com/owner/repo</code>"),
            unsafe_allow_html=True,
        )
    elif not st.session_state.health_ok:
        st.markdown(
            banner("error", "wifi_off", "API is offline. Update the endpoint in the sidebar and refresh status."),
            unsafe_allow_html=True,
        )
    else:
        repo_slug = repo.split("github.com/")[-1]
        with st.spinner(f"Indexing {repo_slug}…"):
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
                "Already indexed — using cached index."
                if cached else
                f"Indexed <strong>{files} files</strong> · <strong>{chunks} chunks</strong>"
            )
            st.markdown(banner("success", "check_circle", msg), unsafe_allow_html=True)
        else:
            st.markdown(banner("error", "error", err), unsafe_allow_html=True)

st.markdown("---")

# ── Step 2 — Question ─────────────────────────────────────────────────────
st.markdown('<div class="m3-overline">Question</div>', unsafe_allow_html=True)

question = st.text_area(
    "question_input", label_visibility="collapsed",
    placeholder=(
        "How does authentication work?\n"
        "Where is JWT token validation?\n"
        "Explain the database connection pooling strategy…"
    ),
    height=96,
)

ask_clicked = st.button("Ask question", type="primary")

if ask_clicked:
    repo = st.session_state.repo_url.strip()
    q    = (question or "").strip()

    if not repo:
        st.markdown(banner("error", "error", "Enter a GitHub repository URL first."), unsafe_allow_html=True)
    elif len(q) < 3:
        st.markdown(banner("error", "error", "Question must be at least 3 characters."), unsafe_allow_html=True)
    elif not st.session_state.health_ok:
        st.markdown(banner("error", "wifi_off", "API is offline — check the sidebar."), unsafe_allow_html=True)
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
                banner("error", "database", "Repository not indexed yet — click <strong>Index</strong> first."),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(banner("error", "error", err), unsafe_allow_html=True)


# ── Results ───────────────────────────────────────────────────────────────
if st.session_state.answer:
    m        = st.session_state.metrics
    pipeline = m.get("pipeline", "semantic")

    # Metric cards (MD3 Surface Container)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latency",  f"{m.get('latency_ms', 0):.0f} ms")
    c2.metric("Tokens",   m.get("tokens_used", 0))
    c3.metric("Sources",  m.get("k_retrieved", 0))
    c4.metric("Pipeline", pipeline)

    st.markdown("---")

    # Answer
    st.markdown('<div class="m3-overline">Answer</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="m3-answer-card">{st.session_state.answer}</div>',
        unsafe_allow_html=True,
    )

    # Sources
    sources = st.session_state.sources
    if sources:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-top:24px;margin-bottom:12px">'
            f'  <span class="m3-overline" style="margin-bottom:0">Sources</span>'
            f'  <span style="font-size:12px;color:var(--md-on-surface-variant)">({len(sources)} chunks)</span>'
            f'  {pipeline_badge(pipeline)}'
            f'</div>',
            unsafe_allow_html=True,
        )

        for src in sources:
            path      = src.get("file_path", "unknown")
            start     = src.get("start_line")
            end       = src.get("end_line")
            lang      = src.get("language", "")
            rerank_sc = src.get("rerank_score")
            sim_sc    = src.get("similarity_score", 0.0)
            excerpt   = (src.get("excerpt") or "").strip()

            disp_score  = rerank_sc if rerank_sc is not None else sim_sc
            score_label = "rerank" if rerank_sc is not None else "sim"
            lines_str   = f"L{start}–{end}" if start and end else ""
            sc          = score_cls(disp_score)

            lang_chip  = f'<span class="m3-chip m3-chip--surface">{lang}</span>' if lang else ""
            line_span  = (
                f'<span style="font-size:11px;color:var(--md-on-surface-variant)">{lines_str}</span>'
                if lines_str else ""
            )
            score_span = (
                f'<span class="{sc}" style="font-size:11px;font-weight:600;margin-left:auto">'
                f'{score_label} {disp_score:.3f}</span>'
            )

            st.markdown(
                f'<div class="m3-source-card">'
                f'  <div class="m3-source-path">{path}</div>'
                f'  <div class="m3-source-meta">{lang_chip}{line_span}{score_span}</div>'
                f'  <div class="m3-source-excerpt">{excerpt}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

else:
    # Empty state
    st.markdown(
        '<div class="m3-empty">'
        '  <span class="m3-empty-icon">code</span>'
        '  <div class="m3-empty-headline">Ready to search your codebase</div>'
        '  <div class="m3-empty-body">'
        '    Paste a GitHub repo URL above, click Index, then ask any question about the code.'
        '  </div>'
        '  <div class="m3-suggestion-row">'
        '    <span class="m3-suggestion-chip">tiangolo/fastapi</span>'
        '    <span class="m3-suggestion-chip">pallets/flask</span>'
        '    <span class="m3-suggestion-chip">django/django</span>'
        '    <span class="m3-suggestion-chip">yanou16/Git_RAG</span>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )
