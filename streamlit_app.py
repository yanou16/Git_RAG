"""
GitRAG — Streamlit Frontend
GitHub Codebase Q&A powered by RAG

Design system: Google Material Design 3 — Light scheme
- Seed color: Google Blue #1558D0
- md.sys.color.* semantic tokens — no raw hex in components
- Google Sans (brand headings) + Roboto Flex (body) + JetBrains Mono (code)
- Shape scale: extra-small(4dp) → medium(12dp) → large(16dp) → full(pill)
- Elevation: box-shadow levels 1–3 (light scheme uses real shadows)
- Filled Button (primary) · Filled Tonal Button (secondary) · Text Button
- State layers via ::before — hover 8 %, focus/press 12 %
- Landing page: hero + how-it-works + tool + results
"""

import streamlit as st
import requests
import time

# ── Constants ─────────────────────────────────────────────────────────────
DEFAULT_API_URL = "https://yanou16-gitgub-rag.hf.space"

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitRAG — Ask your codebase",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── MD3 Light CSS ─────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto+Flex:opsz,wght@8..144,300;8..144,400;8..144,500;8..144,700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ══════════════════════════════════════════════════════════════
   MD3 LIGHT COLOR SCHEME — seed: Google Blue #1558D0
══════════════════════════════════════════════════════════════ */
:root {
  /* Background / Surface */
  --md-bg:               #FAFBFF;
  --md-on-bg:            #1A1C22;
  --md-surface:          #FAFBFF;
  --md-on-surface:       #1A1C22;
  --md-surface-variant:  #E1E2EC;
  --md-on-sv:            #44474F;

  /* Surface container hierarchy (tonal elevation) */
  --md-sc-lowest:        #FFFFFF;
  --md-sc-low:           #F1F3FA;
  --md-sc-:              #EBEDF4;
  --md-sc-high:          #E5E7EE;
  --md-sc-highest:       #DFE1E8;

  /* Primary */
  --md-primary:          #1558D0;
  --md-on-primary:       #FFFFFF;
  --md-primary-c:        #D8E2FF;
  --md-on-primary-c:     #001947;

  /* Secondary */
  --md-secondary:        #575E71;
  --md-on-secondary:     #FFFFFF;
  --md-secondary-c:      #DBE2F9;
  --md-on-secondary-c:   #131C2C;

  /* Tertiary */
  --md-tertiary:         #715573;
  --md-on-tertiary:      #FFFFFF;
  --md-tertiary-c:       #FBD7FC;
  --md-on-tertiary-c:    #29132D;

  /* Error */
  --md-error:            #BA1A1A;
  --md-on-error:         #FFFFFF;
  --md-error-c:          #FFDAD6;
  --md-on-error-c:       #410002;

  /* Outline */
  --md-outline:          #74777F;
  --md-outline-v:        #C4C6D0;

  /* Success (custom) */
  --md-success:          #146B2D;
  --md-success-c:        #C8F5CC;
  --md-on-success-c:     #002109;

  /* MD3 Shape scale */
  --shape-xs:   4px;
  --shape-sm:   8px;
  --shape-md:   12px;
  --shape-lg:   16px;
  --shape-xl:   28px;
  --shape-full: 9999px;

  /* Typography */
  --font-brand: 'Google Sans', Roboto, sans-serif;
  --font-plain: 'Roboto Flex', Roboto, sans-serif;
  --font-mono:  'JetBrains Mono', monospace;

  /* MD3 Motion */
  --ease-em:    cubic-bezier(0.2, 0, 0, 1);
  --dur-s3:     150ms;
  --dur-m2:     300ms;

  /* MD3 Elevation (light scheme uses real shadows) */
  --elev-1: 0 1px 2px rgba(0,0,0,.14), 0 1px 3px 1px rgba(0,0,0,.10);
  --elev-2: 0 1px 2px rgba(0,0,0,.14), 0 2px 6px 2px rgba(0,0,0,.10);
  --elev-3: 0 4px 8px 3px rgba(0,0,0,.10), 0 1px 3px rgba(0,0,0,.14);
}

/* ── Base ── */
.stApp {
  background: var(--md-bg) !important;
  font-family: var(--font-plain) !important;
  color: var(--md-on-bg) !important;
}
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Sidebar — MD3 Navigation Drawer ── */
[data-testid="stSidebar"] {
  background: var(--md-sc-low) !important;
  border-right: 1px solid var(--md-outline-v) !important;
}
[data-testid="stSidebar"] .block-container {
  padding: 1.5rem 1.25rem 2rem !important;
}

/* ── Typography resets ── */
h1,h2,h3,h4 {
  font-family: var(--font-brand) !important;
  font-weight: 400 !important;
  color: var(--md-on-surface) !important;
}
p, li, span, div { font-family: var(--font-plain) !important; }
label {
  font-family: var(--font-plain) !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: var(--md-on-sv) !important;
  letter-spacing: 0.1px !important;
}

/* ── MD3 Filled Text Field ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background: var(--md-sc-highest) !important;
  border: none !important;
  border-bottom: 1px solid var(--md-outline) !important;
  border-radius: var(--shape-xs) var(--shape-xs) 0 0 !important;
  color: var(--md-on-surface) !important;
  font-family: var(--font-plain) !important;
  font-size: 16px !important;
  padding: 18px 16px 8px !important;
  box-shadow: none !important;
  transition: border-color var(--dur-s3) var(--ease-em) !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-bottom: 2px solid var(--md-primary) !important;
  outline: none !important;
  box-shadow: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
  color: var(--md-on-sv) !important;
}

/* ── MD3 Filled Tonal Button (default) ── */
.stButton > button {
  background: var(--md-secondary-c) !important;
  color: var(--md-on-secondary-c) !important;
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
  transition: box-shadow var(--dur-s3) var(--ease-em) !important;
}
.stButton > button::before {
  content: '';
  position: absolute; inset: 0;
  background: var(--md-on-secondary-c);
  opacity: 0;
  border-radius: inherit;
  transition: opacity var(--dur-s3) var(--ease-em);
  pointer-events: none;
}
.stButton > button:hover::before  { opacity: 0.08; }
.stButton > button:focus-visible::before { opacity: 0.12; }
.stButton > button:active::before { opacity: 0.12; }
.stButton > button:hover { box-shadow: var(--elev-1) !important; }

/* ── MD3 Filled Button — primary ── */
[data-testid="baseButton-primary"] {
  background: var(--md-primary) !important;
  color: var(--md-on-primary) !important;
}
[data-testid="baseButton-primary"]::before {
  background: var(--md-on-primary) !important;
}
[data-testid="baseButton-primary"]:hover {
  box-shadow: var(--elev-2) !important;
}

/* ── Checkbox ── */
.stCheckbox label {
  font-size: 14px !important;
  font-weight: 400 !important;
  color: var(--md-on-surface) !important;
  letter-spacing: 0 !important;
}

/* ── Slider ── */
.stSlider label {
  font-size: 11px !important;
  font-weight: 500 !important;
  letter-spacing: 0.8px !important;
  text-transform: uppercase !important;
  color: var(--md-on-sv) !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
  background: var(--md-sc-lowest) !important;
  border: none !important;
  border-radius: var(--shape-md) !important;
  padding: 16px !important;
  box-shadow: var(--elev-1) !important;
}
[data-testid="stMetricLabel"] {
  font-family: var(--font-plain) !important;
  font-size: 12px !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px !important;
  text-transform: none !important;
  color: var(--md-on-sv) !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--font-mono) !important;
  font-size: 20px !important;
  font-weight: 500 !important;
  color: var(--md-primary) !important;
}

/* ── Divider ── */
hr {
  border: none !important;
  border-top: 1px solid var(--md-outline-v) !important;
  margin: 32px 0 !important;
}


/* ════════════════════════════════════════════════════════════
   LANDING PAGE COMPONENTS
════════════════════════════════════════════════════════════ */

/* ── Wrapper for main content ── */
.m3-page { max-width: 900px; margin: 0 auto; padding: 0 24px 64px; }

/* ── Hero section ── */
.m3-hero {
  padding: 56px 0 48px;
  text-align: center;
}
.m3-hero-logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: var(--md-primary-c);
  color: var(--md-on-primary-c);
  padding: 8px 20px;
  border-radius: var(--shape-full);
  font-family: var(--font-brand);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.5px;
  margin-bottom: 24px;
}
.m3-hero-logo-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--md-primary);
}
.m3-display-large {
  font-family: var(--font-brand);
  font-size: 48px;
  font-weight: 400;
  line-height: 56px;
  letter-spacing: -0.25px;
  color: var(--md-on-surface);
  margin-bottom: 16px;
}
.m3-display-large em {
  font-style: normal;
  color: var(--md-primary);
}
.m3-hero-sub {
  font-family: var(--font-plain);
  font-size: 18px;
  font-weight: 400;
  line-height: 28px;
  color: var(--md-on-sv);
  max-width: 560px;
  margin: 0 auto 32px;
}
.m3-hero-chips {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 0;
}
.m3-tech-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 14px;
  border-radius: var(--shape-full);
  background: var(--md-sc-low);
  border: 1px solid var(--md-outline-v);
  font-size: 13px;
  font-weight: 500;
  color: var(--md-on-sv);
}
.m3-tech-chip-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
}

/* ── How it works ── */
.m3-section-label {
  font-family: var(--font-plain);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--md-primary);
  margin-bottom: 8px;
  text-align: center;
}
.m3-section-title {
  font-family: var(--font-brand);
  font-size: 28px;
  font-weight: 400;
  line-height: 36px;
  color: var(--md-on-surface);
  text-align: center;
  margin-bottom: 32px;
}
.m3-step-card {
  background: var(--md-sc-lowest);
  border-radius: var(--shape-lg);
  padding: 24px;
  box-shadow: var(--elev-1);
  height: 100%;
  position: relative;
  overflow: hidden;
}
.m3-step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--md-primary-c);
  color: var(--md-on-primary-c);
  font-family: var(--font-brand);
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 14px;
}
.m3-step-title {
  font-family: var(--font-brand);
  font-size: 17px;
  font-weight: 500;
  color: var(--md-on-surface);
  margin-bottom: 6px;
  line-height: 24px;
}
.m3-step-body {
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
  color: var(--md-on-sv);
}
.m3-step-card-accent {
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
  background: var(--md-primary);
  border-radius: 4px 0 0 4px;
}

/* ── Tool section ── */
.m3-tool-header {
  background: var(--md-primary-c);
  border-radius: var(--shape-lg) var(--shape-lg) 0 0;
  padding: 20px 28px 16px;
  margin-bottom: 0;
}
.m3-tool-header-title {
  font-family: var(--font-brand);
  font-size: 20px;
  font-weight: 500;
  color: var(--md-on-primary-c);
}
.m3-tool-header-sub {
  font-size: 14px;
  color: var(--md-primary);
  margin-top: 2px;
  font-weight: 500;
}
.m3-tool-body {
  background: var(--md-sc-lowest);
  border-radius: 0 0 var(--shape-lg) var(--shape-lg);
  padding: 28px;
  box-shadow: var(--elev-2);
  margin-bottom: 32px;
}

/* Step badge inside tool */
.m3-step-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--md-primary);
  letter-spacing: 0.1px;
  margin-bottom: 12px;
}
.m3-step-badge-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--md-primary);
  color: var(--md-on-primary);
  font-size: 11px;
  font-weight: 700;
}

/* Overline for labels */
.m3-overline {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--md-on-sv);
  margin-bottom: 8px;
}

/* ── Alert banners ── */
.m3-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  border-radius: var(--shape-md);
  font-size: 14px;
  font-weight: 400;
  line-height: 20px;
  margin: 10px 0;
}
.m3-banner--success {
  background: var(--md-success-c);
  color: var(--md-on-success-c);
}
.m3-banner--error {
  background: var(--md-error-c);
  color: var(--md-on-error-c);
}
.m3-banner--info {
  background: var(--md-primary-c);
  color: var(--md-on-primary-c);
}
.m3-banner-icon { font-size: 16px; flex-shrink: 0; line-height: 20px; }

/* ── Status chip (sidebar) ── */
.m3-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--shape-full);
  font-size: 13px;
  font-weight: 500;
  margin: 8px 0 4px;
}
.m3-status--on  { background: var(--md-success-c);  color: var(--md-on-success-c); }
.m3-status--off { background: var(--md-error-c); color: var(--md-on-error-c); }
.m3-status-dot  { width:7px; height:7px; border-radius:50%; background:currentColor; flex-shrink:0; }
.m3-status--on .m3-status-dot { animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
.m3-status-meta { font-size:11px; color:var(--md-on-sv); padding-left:2px; margin-bottom:12px; }

/* ── Answer card — Elevated ── */
.m3-answer-card {
  background: var(--md-sc-lowest);
  border-radius: var(--shape-lg);
  padding: 24px 28px;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.75;
  color: var(--md-on-surface);
  margin: 12px 0;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: var(--elev-2);
}
.m3-answer-card code {
  font-family: var(--font-mono) !important;
  font-size: 13px !important;
  background: var(--md-sc-high) !important;
  padding: 2px 6px !important;
  border-radius: var(--shape-xs) !important;
  color: var(--md-primary) !important;
}

/* ── Source cards — Filled ── */
.m3-source-card {
  background: var(--md-sc-low);
  border-radius: var(--shape-md);
  padding: 16px 18px;
  margin-bottom: 8px;
  border-left: 3px solid var(--md-primary-c);
  transition: box-shadow var(--dur-s3) var(--ease-em), border-color var(--dur-s3) var(--ease-em);
}
.m3-source-card:hover {
  box-shadow: var(--elev-1);
  border-left-color: var(--md-primary);
}
.m3-source-path {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--md-primary);
  margin-bottom: 8px;
}
.m3-source-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.m3-source-excerpt {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--md-on-sv);
  background: var(--md-sc-high);
  border-radius: var(--shape-xs);
  padding: 10px 12px;
  line-height: 1.6;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

/* ── MD3 Chips ── */
.m3-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--shape-full);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.1px;
  white-space: nowrap;
}
.m3-chip--primary  { background: var(--md-primary-c);   color: var(--md-on-primary-c); }
.m3-chip--secondary{ background: var(--md-secondary-c); color: var(--md-on-secondary-c); }
.m3-chip--tertiary { background: var(--md-tertiary-c);  color: var(--md-on-tertiary-c); }
.m3-chip--surface  {
  background: var(--md-sc-high);
  color: var(--md-on-sv);
  border: 1px solid var(--md-outline-v);
}

/* Score coloring */
.sc-hi { color: var(--md-success)  !important; font-weight: 600 !important; }
.sc-md { color: #B8860B !important; font-weight: 600 !important; }
.sc-lo { color: var(--md-on-sv)    !important; }

/* Pipeline pill */
.m3-pipeline {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: var(--shape-full);
  font-size: 12px;
  font-weight: 500;
  background: var(--md-tertiary-c);
  color: var(--md-on-tertiary-c);
}

/* ── Nav drawer elements ── */
.m3-nav-title {
  font-family: var(--font-brand);
  font-size: 20px;
  font-weight: 500;
  color: var(--md-on-surface);
  padding-bottom: 4px;
}
.m3-nav-sub {
  font-size: 12px;
  color: var(--md-on-sv);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--md-outline-v);
  margin-bottom: 16px;
}
.m3-pipeline-card {
  background: var(--md-sc-);
  border-radius: var(--shape-md);
  padding: 14px 16px;
  margin-top: 4px;
}
.m3-pipeline-card-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--md-on-sv);
  margin-bottom: 8px;
}
.m3-pipeline-step {
  font-size: 12px;
  line-height: 1.9;
  color: var(--md-on-sv);
}
.m3-pipeline-step b { color: var(--md-primary); font-weight: 500; }

/* ── Empty state ── */
.m3-empty {
  text-align: center;
  padding: 52px 24px;
  background: var(--md-sc-low);
  border-radius: var(--shape-lg);
  border: 1px dashed var(--md-outline-v);
}
.m3-empty-icon { font-size: 52px; margin-bottom: 16px; display: block; opacity: .6; }
.m3-empty-headline {
  font-family: var(--font-brand);
  font-size: 22px;
  font-weight: 400;
  color: var(--md-on-surface);
  margin-bottom: 8px;
}
.m3-empty-body {
  font-size: 14px;
  color: var(--md-on-sv);
  line-height: 20px;
  max-width: 380px;
  margin: 0 auto 24px;
}
.m3-suggestion-row { display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }
.m3-suggestion-chip {
  background: var(--md-sc-lowest);
  border: 1px solid var(--md-outline-v);
  border-radius: var(--shape-full);
  padding: 6px 14px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--md-secondary);
  box-shadow: var(--elev-1);
}

/* ── Results section label row ── */
.m3-results-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 28px 0 16px;
}
.m3-results-title {
  font-family: var(--font-brand);
  font-size: 20px;
  font-weight: 500;
  color: var(--md-on-surface);
}

/* Divider with label */
.m3-divider-label {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 32px 0 24px;
}
.m3-divider-line {
  flex: 1;
  height: 1px;
  background: var(--md-outline-v);
}
.m3-divider-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--md-on-sv);
  letter-spacing: 0.5px;
  white-space: nowrap;
}
</style>
"""

# ── Helpers ───────────────────────────────────────────────────────────────
def api_call(base: str, method: str, endpoint: str, payload: dict = None, timeout: int = 120):
    url = f"{base.rstrip('/')}/{endpoint.lstrip('/')}"
    try:
        r = requests.post(url, json=payload, timeout=timeout) if method == "POST" else requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to `{base}`. Is the API running?"
    except requests.exceptions.Timeout:
        return None, "Request timed out — the repo may be large. Try again."
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
        label = "Hybrid BM25"
    elif "rerank" in p:
        label = "Semantic + rerank"
    else:
        label = "Semantic"
    return f'<span class="m3-pipeline">{label}</span>'


def score_cls(v: float) -> str:
    return "sc-hi" if v >= 0.8 else ("sc-md" if v >= 0.5 else "sc-lo")


def banner(kind: str, icon: str, text: str) -> str:
    return (
        f'<div class="m3-banner m3-banner--{kind}">'
        f'<span class="m3-banner-icon">{icon}</span>'
        f'<div>{text}</div>'
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
        '<div class="m3-nav-title">⬡ GitRAG</div>'
        '<div class="m3-nav-sub">GitHub codebase Q&A</div>',
        unsafe_allow_html=True,
    )

    # API endpoint
    st.markdown('<div class="m3-overline">API endpoint</div>', unsafe_allow_html=True)
    new_url = st.text_input(
        "api_url_input", label_visibility="collapsed",
        value=st.session_state.api_url,
        placeholder="https://yanou16-gitgub-rag.hf.space",
        key="api_url_input",
    )
    if new_url and new_url != st.session_state.api_url:
        st.session_state.api_url   = new_url
        st.session_state.health_ok = None
        st.session_state.health_ts = 0.0

    # Health (cached 60 s)
    now = time.time()
    if now - st.session_state.health_ts > 60 or st.session_state.health_ok is None:
        data, _ = api_call(st.session_state.api_url, "GET", "/health", timeout=8)
        st.session_state.health_ok   = (data is not None and data.get("status") == "healthy")
        st.session_state.health_data = data or {}
        st.session_state.health_ts   = now

    if st.session_state.health_ok:
        v = st.session_state.health_data.get("version", "1.0")
        q = st.session_state.health_data.get("total_queries", 0)
        st.markdown(
            '<div class="m3-status m3-status--on">'
            '<span class="m3-status-dot"></span> API online'
            '</div>'
            f'<div class="m3-status-meta">v{v} · {q} queries served</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="m3-status m3-status--off">'
            '<span class="m3-status-dot"></span> Offline'
            '</div>'
            '<div class="m3-status-meta">Check the URL above</div>',
            unsafe_allow_html=True,
        )

    if st.button("Refresh status", use_container_width=True):
        st.session_state.health_ts = 0.0
        st.rerun()

    st.markdown("---")

    st.markdown('<div class="m3-overline">Search settings</div>', unsafe_allow_html=True)
    k             = st.slider("Results (k)", 1, 20, 5)
    use_hybrid    = st.checkbox("Hybrid search (BM25 + RRF)", value=True)
    use_reranking = st.checkbox("Cohere reranking", value=True)

    st.markdown("---")

    st.markdown('<div class="m3-overline">Index settings</div>', unsafe_allow_html=True)
    max_files     = st.slider("Max files", 10, 300, 100)
    branch        = st.text_input("Branch", value="main", placeholder="main")
    force_reindex = st.checkbox("Force re-index")

    st.markdown("---")

    st.markdown(
        '<div class="m3-pipeline-card">'
        '<div class="m3-pipeline-card-title">RAG pipeline</div>'
        '<div class="m3-pipeline-step">'
        '<b>GitHub API</b> → clone &amp; parse<br>'
        '→ <b>AST chunking</b> (tree-sitter)<br>'
        '→ <b>ChromaDB</b> HNSW index<br>'
        '→ <b>BM25</b> + RRF fusion<br>'
        '→ <b>Cohere</b> reranking<br>'
        '→ <b>Groq</b> llama-3.3-70b'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ── Main ─────────────────────────────────────────────────────────────────
st.markdown('<div class="m3-page">', unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="m3-hero">'
    '  <div class="m3-hero-logo">'
    '    <span class="m3-hero-logo-dot"></span>'
    '    Powered by RAG · BM25 · Cohere · Groq'
    '  </div>'
    '  <div class="m3-display-large">Ask anything about<br>any <em>GitHub codebase</em></div>'
    '  <div class="m3-hero-sub">'
    '    Paste a public GitHub URL, click Index, then ask natural-language questions.<br>'
    '    GitRAG finds the exact files, functions and line numbers that answer you.'
    '  </div>'
    '  <div class="m3-hero-chips">'
    '    <span class="m3-tech-chip"><span class="m3-tech-chip-dot" style="background:#1558D0"></span>Embedding search</span>'
    '    <span class="m3-tech-chip"><span class="m3-tech-chip-dot" style="background:#715573"></span>BM25 keyword search</span>'
    '    <span class="m3-tech-chip"><span class="m3-tech-chip-dot" style="background:#146B2D"></span>Cohere reranking</span>'
    '    <span class="m3-tech-chip"><span class="m3-tech-chip-dot" style="background:#B8860B"></span>Groq LLM answers</span>'
    '  </div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── HOW IT WORKS ─────────────────────────────────────────────────────────
st.markdown(
    '<div class="m3-section-label">How it works</div>'
    '<div class="m3-section-title">Three steps to understand any codebase</div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        '<div class="m3-step-card">'
        '  <div class="m3-step-card-accent"></div>'
        '  <div class="m3-step-number">1</div>'
        '  <div class="m3-step-title">Paste a GitHub URL</div>'
        '  <div class="m3-step-body">Any public repository — FastAPI, Django, your own project. Copy the URL from your browser.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        '<div class="m3-step-card">'
        '  <div class="m3-step-card-accent"></div>'
        '  <div class="m3-step-number">2</div>'
        '  <div class="m3-step-title">Index the repo</div>'
        '  <div class="m3-step-body">GitRAG fetches the code, splits it into smart chunks with AST parsing, and builds a searchable vector index. Takes ~30 s.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        '<div class="m3-step-card">'
        '  <div class="m3-step-card-accent"></div>'
        '  <div class="m3-step-number">3</div>'
        '  <div class="m3-step-title">Ask your question</div>'
        '  <div class="m3-step-body">Type any question in plain English. GitRAG retrieves the most relevant code chunks and uses an LLM to answer with exact file paths &amp; line numbers.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

# ── TOOL ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="m3-divider-label">'
    '  <div class="m3-divider-line"></div>'
    '  <div class="m3-divider-text">TRY IT NOW</div>'
    '  <div class="m3-divider-line"></div>'
    '</div>',
    unsafe_allow_html=True,
)

# Step 1 — Index
st.markdown(
    '<div class="m3-tool-header">'
    '  <div class="m3-tool-header-title">Step 1 — Index a repository</div>'
    '  <div class="m3-tool-header-sub">Paste a GitHub URL and click Index. Already indexed? Skip to step 2.</div>'
    '</div>',
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="m3-tool-body">', unsafe_allow_html=True)

    col_url, col_btn = st.columns([5, 1])
    with col_url:
        repo_url = st.text_input(
            "Repository URL", label_visibility="visible",
            value=st.session_state.repo_url,
            placeholder="https://github.com/tiangolo/fastapi",
        )
        if repo_url != st.session_state.repo_url:
            st.session_state.repo_url     = repo_url
            st.session_state.repo_indexed = False
            st.session_state.answer       = None
            st.session_state.sources      = []
    with col_btn:
        st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
        index_clicked = st.button("Index", use_container_width=True)

    if index_clicked:
        repo = st.session_state.repo_url.strip()
        if not repo.startswith("https://github.com/"):
            st.markdown(
                banner("error", "⚠️", "Enter a valid GitHub URL — <code>https://github.com/owner/repo</code>"),
                unsafe_allow_html=True,
            )
        elif not st.session_state.health_ok:
            st.markdown(
                banner("error", "🔌", "API is offline. Update the endpoint in the sidebar and refresh status."),
                unsafe_allow_html=True,
            )
        else:
            repo_slug = repo.split("github.com/")[-1]
            with st.spinner(f"Indexing {repo_slug} — this takes ~30 seconds for medium repos…"):
                data, err = api_call(
                    st.session_state.api_url, "POST", "/ingest",
                    payload={"repo_url": repo, "branch": branch,
                             "max_files": max_files, "force_reindex": force_reindex},
                    timeout=300,
                )
            if data:
                st.session_state.repo_indexed = True
                files  = data.get("files_processed", data.get("files_indexed", "?"))
                chunks = data.get("chunks_indexed",  data.get("chunks_stored",  "?"))
                cached = data.get("already_indexed", False)
                msg = (
                    "Already indexed — cached index loaded instantly."
                    if cached else
                    f"Indexed <strong>{files} files</strong> · <strong>{chunks} chunks</strong> — ready to query!"
                )
                st.markdown(banner("success", "✓", msg), unsafe_allow_html=True)
            else:
                st.markdown(banner("error", "✗", err), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# Step 2 — Question
st.markdown(
    '<div class="m3-tool-header" style="margin-top:12px">'
    '  <div class="m3-tool-header-title">Step 2 — Ask your question</div>'
    '  <div class="m3-tool-header-sub">Ask anything in plain English about the indexed repo.</div>'
    '</div>',
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="m3-tool-body">', unsafe_allow_html=True)

    question = st.text_area(
        "Your question", label_visibility="visible",
        placeholder=(
            "How does authentication work?\n"
            "Where is the JWT token validation?\n"
            "Explain the database connection pooling strategy…"
        ),
        height=100,
    )
    ask_clicked = st.button("Ask question", type="primary")

    if ask_clicked:
        repo = st.session_state.repo_url.strip()
        q    = (question or "").strip()
        if not repo:
            st.markdown(banner("error", "⚠️", "Enter and index a GitHub repository URL first (step 1)."), unsafe_allow_html=True)
        elif len(q) < 3:
            st.markdown(banner("error", "⚠️", "Please type a question (at least 3 characters)."), unsafe_allow_html=True)
        elif not st.session_state.health_ok:
            st.markdown(banner("error", "🔌", "API is offline — check the sidebar."), unsafe_allow_html=True)
        else:
            with st.spinner("Searching the codebase and generating answer…"):
                data, err = api_call(
                    st.session_state.api_url, "POST", "/query",
                    payload={"repo_url": repo, "question": q, "k": k,
                             "use_hybrid": use_hybrid, "use_reranking": use_reranking},
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
                    banner("error", "🗄️", "Repository not indexed yet — complete step 1 first."),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(banner("error", "✗", err), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ── RESULTS ───────────────────────────────────────────────────────────────
if st.session_state.answer:
    m        = st.session_state.metrics
    pipeline = m.get("pipeline", "semantic")

    # Metric cards
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Response time", f"{m.get('latency_ms', 0):.0f} ms")
    mc2.metric("Tokens used",   m.get("tokens_used", 0))
    mc3.metric("Sources found", m.get("k_retrieved", 0))
    mc4.metric("Pipeline",      pipeline)

    # Answer
    st.markdown(
        '<div class="m3-results-header">'
        '  <div class="m3-results-title">Answer</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="m3-answer-card">{st.session_state.answer}</div>',
        unsafe_allow_html=True,
    )

    # Sources
    sources = st.session_state.sources
    if sources:
        st.markdown(
            f'<div class="m3-results-header">'
            f'  <div class="m3-results-title">Source code references</div>'
            f'  <span style="font-size:14px;color:var(--md-on-sv)">{len(sources)} chunks</span>'
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
            line_span  = f'<span style="font-size:11px;color:var(--md-on-sv)">{lines_str}</span>' if lines_str else ""
            score_span = (
                f'<span class="{sc}" style="font-size:11px;margin-left:auto">'
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
        '  <span class="m3-empty-icon">⬡</span>'
        '  <div class="m3-empty-headline">Results will appear here</div>'
        '  <div class="m3-empty-body">'
        '    Follow steps 1 and 2 above. Start with one of these popular repos:'
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

st.markdown('</div>', unsafe_allow_html=True)  # close .m3-page
