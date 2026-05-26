import { useState, useCallback, useRef } from "react";
import { Loader2, ChevronDown, ChevronUp, AlertCircle, FileCode2, CheckCircle2, RotateCcw, RefreshCw } from "lucide-react";
import { Button } from "./ui/button.jsx";
import { Input } from "./ui/input.jsx";
import { cn } from "../lib/utils.js";
import { ingestRepo, queryRepo } from "../api.js";

const SUPPORTED_LANGS = "Python, JS/TS, C#, Java, C/C++, Go, Rust, Ruby, PHP, Swift, Kotlin, Dart";

function humanise(raw = "") {
  if (raw.includes("rate limit") || raw.includes("403"))
    return { title: "GitHub rate limit reached", body: "The backend hit GitHub's unauthenticated limit (60 req/h). Add GITHUB_TOKEN to your HuggingFace Space secrets.", hint: "HF Space settings → Repository secrets → GITHUB_TOKEN" };
  if (raw.includes("REPO_NOT_INDEXED") || raw.includes("not indexed"))
    return { title: "Repository not indexed", body: "Complete the index step first, then ask your question.", hint: null };
  if (raw.includes("No supported files"))
    return { title: "No supported files found", body: `The repository has no files in a supported language.`, hint: `Supported: ${SUPPORTED_LANGS}` };
  if (raw.includes("REPO_NOT_FOUND") || raw.includes("Repo not found") || raw.includes("404"))
    return { title: "Repository not found or private", body: "Make sure the repository exists and is set to Public.", hint: "GitHub repo settings → Danger Zone → Change visibility → Public" };
  if (raw.includes("timeout") || raw.includes("AbortError"))
    return { title: "Request timed out", body: "The backend may be cold-starting on HuggingFace. Retry in 30 seconds.", hint: null };
  if (raw.includes("Failed to fetch") || raw.includes("NetworkError"))
    return { title: "Cannot reach the backend", body: "Check your connection or the HuggingFace Space may be sleeping.", hint: null };
  return { title: "Something went wrong", body: raw, hint: null };
}

const PROGRESS = ["Cloning repository…", "Parsing files with AST…", "Generating embeddings…", "Storing in ChromaDB…", "Finalising index…"];
const REPOS = [
  { label: "tiangolo/fastapi", url: "https://github.com/tiangolo/fastapi" },
  { label: "pallets/flask",    url: "https://github.com/pallets/flask" },
  { label: "psf/requests",     url: "https://github.com/psf/requests" },
];
const QUESTIONS = ["How does authentication work?", "Where is the main entry point?", "How are errors handled?"];

function PillChip({ label, onClick }) {
  return (
    <button
      onClick={onClick}
      className="border border-c-hairline text-c-body-muted text-xs font-mono px-3 py-1 rounded-xl hover:border-c-ink hover:text-c-ink transition-colors touch-manipulation"
    >
      {label}
    </button>
  );
}

function SourceRow({ source, index }) {
  const [open, setOpen] = useState(false);
  const score = (source.rerank_score ?? source.similarity_score ?? 0).toFixed(3);
  return (
    <div className="border-b border-c-hairline last:border-b-0">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full min-h-[44px] flex items-center gap-3 py-3 hover:bg-c-stone/40 transition-colors text-left"
        aria-expanded={open}
      >
        <FileCode2 size={13} className="text-c-muted shrink-0" aria-hidden="true" />
        <span className="flex-1 font-mono text-xs text-c-ink overflow-hidden text-ellipsis whitespace-nowrap">
          {source.file_path}
        </span>
        <span className="font-mono text-[10px] text-c-muted tracking-mono uppercase mr-2">
          {source.start_line != null ? `L${source.start_line}` : ""}
        </span>
        <span className="font-mono text-xs text-c-muted mr-2">{score}</span>
        {open
          ? <ChevronUp size={12} className="text-c-muted shrink-0" aria-hidden="true" />
          : <ChevronDown size={12} className="text-c-muted shrink-0" aria-hidden="true" />
        }
      </button>
      {open && (
        <pre className="font-mono text-[12px] text-c-ink leading-relaxed px-5 pb-4 whitespace-pre-wrap break-words m-0 bg-c-stone/20">
          {source.excerpt}
        </pre>
      )}
    </div>
  );
}

function Skeleton({ className }) {
  return <div className={cn("skeleton", className)} />;
}

function ResultSkeleton() {
  return (
    <div className="py-8 px-0 space-y-3" aria-busy="true">
      <Skeleton className="h-3 w-1/4 mb-5" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-10/12" />
      <Skeleton className="h-4 w-4/5 mb-6" />
      <Skeleton className="h-3 w-1/5 mb-3" />
      <Skeleton className="h-10 w-full" />
      <Skeleton className="h-10 w-full" />
    </div>
  );
}

export default function Tool() {
  const [step, setStep]         = useState("idle");
  const [repoUrl, setRepoUrl]   = useState("");
  const [question, setQuestion] = useState("");
  const [ingestMeta, setIngestMeta] = useState(null);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState(null);
  const [progIdx, setProgIdx]   = useState(0);
  const timerRef                = useRef(null);

  const startProgress = () => {
    setProgIdx(0);
    timerRef.current = setInterval(() => {
      setProgIdx(i => { if (i >= PROGRESS.length - 1) { clearInterval(timerRef.current); return i; } return i + 1; });
    }, 6000);
  };

  const handleIngest = useCallback(async () => {
    if (!repoUrl.trim()) return;
    setError(null); setStep("ingesting"); startProgress();
    try {
      const data = await ingestRepo({ repoUrl: repoUrl.trim() });
      clearInterval(timerRef.current); setIngestMeta(data); setStep("ready");
    } catch (err) {
      clearInterval(timerRef.current); setError(humanise(err.message)); setStep("idle");
    }
  }, [repoUrl]);

  const handleQuery = useCallback(async () => {
    if (!question.trim()) return;
    setError(null); setStep("querying");
    try {
      const data = await queryRepo({ repoUrl: repoUrl.trim(), question: question.trim(), useHybrid: true, useReranking: true });
      setResult(data); setStep("done");
    } catch (err) {
      setError(humanise(err.message)); setStep("ready");
    }
  }, [repoUrl, question]);

  const reset = () => { clearInterval(timerRef.current); setStep("idle"); setRepoUrl(""); setQuestion(""); setIngestMeta(null); setResult(null); setError(null); };

  const repoReady  = ["ready","querying","done"].includes(step);
  const isIngesting = step === "ingesting";
  const isQuerying  = step === "querying";

  return (
    <section id="tool" className="bg-c-canvas py-24 px-8" aria-label="Interactive demo">
      <div className="max-w-3xl mx-auto">
        <p className="font-mono text-xs text-c-muted tracking-mono uppercase mb-6">Live demo</p>
        <h2
          className="font-display font-light text-c-ink leading-snug mb-4"
          style={{ fontSize: "clamp(32px, 4.5vw, 48px)", letterSpacing: "-0.015em" }}
        >
          Try it right now.
        </h2>
        <p className="text-base text-c-body-muted leading-[1.5] mb-14">
          Index any public GitHub repo in under a minute, then ask anything.
        </p>

        {/* ── STEP 1 ── */}
        <div className="border-t border-c-hairline pt-8 mb-8">
          <div className="flex items-baseline gap-4 mb-5">
            <span className="font-mono text-xs text-c-muted tracking-mono uppercase">01</span>
            <h3 className="font-display font-normal text-lg text-c-ink" style={{ letterSpacing: "-0.01em" }}>
              {repoReady ? "Repository indexed" : "Index a repository"}
            </h3>
          </div>

          {/* ── Success banner ── */}
          {repoReady && ingestMeta && (
            <div className="flex items-center gap-3 bg-c-pale-green border border-c-hairline rounded px-4 py-3 mb-4">
              <CheckCircle2 size={14} className="text-green-700 shrink-0" aria-hidden="true" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-green-900 leading-none mb-1">
                  {ingestMeta.was_cached ? "Already indexed — loaded from cache" : "Indexed successfully"}
                </p>
                <p className="font-mono text-xs text-green-700">
                  {ingestMeta.files_indexed > 0 && <>{ingestMeta.files_indexed} files · </>}
                  {ingestMeta.chunks_stored > 0 && <>{ingestMeta.chunks_stored.toLocaleString()} chunks</>}
                  {ingestMeta.duration_ms > 0 && !ingestMeta.was_cached && <> · {(ingestMeta.duration_ms / 1000).toFixed(1)}s</>}
                </p>
              </div>
            </div>
          )}

          {!repoReady ? (
            <>
              <div className="flex gap-2 mb-3">
                <Input
                  id="repo-url" type="url"
                  value={repoUrl} onChange={e => setRepoUrl(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleIngest()}
                  placeholder="https://github.com/owner/repo"
                  disabled={isIngesting} autoComplete="url"
                />
                <Button
                  onClick={handleIngest}
                  disabled={isIngesting || !repoUrl.trim()}
                  className="shrink-0"
                >
                  {isIngesting
                    ? <><Loader2 size={13} className="spin" aria-hidden="true" /> Indexing…</>
                    : "Index repo"
                  }
                </Button>
              </div>
              {isIngesting && (
                <p className="text-xs text-c-muted font-mono flex items-center gap-2 mb-2">
                  <Loader2 size={11} className="spin" aria-hidden="true" />
                  {PROGRESS[progIdx]}
                </p>
              )}
              {!isIngesting && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-c-muted">Try:</span>
                  {REPOS.map(r => <PillChip key={r.url} label={r.label} onClick={() => setRepoUrl(r.url)} />)}
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center gap-3">
              <code className="flex-1 border border-c-hairline bg-c-stone/30 px-3 py-2 text-xs text-c-body-muted font-mono overflow-hidden text-ellipsis whitespace-nowrap rounded">
                {repoUrl}
              </code>
              <button
                onClick={reset}
                className="border border-c-hairline p-2 text-c-muted hover:text-c-ink hover:border-c-ink transition-colors rounded touch-manipulation"
                aria-label="Reset"
                title="Index a different repository"
              >
                <RotateCcw size={13} aria-hidden="true" />
              </button>
            </div>
          )}
        </div>

        {/* ── STEP 2 ── */}
        <div className="border-t border-c-hairline pt-8">
          <div className="flex items-baseline gap-4 mb-5">
            <span className="font-mono text-xs text-c-muted tracking-mono uppercase">02</span>
            <h3
              className={cn("font-display font-normal text-lg", repoReady ? "text-c-ink" : "text-c-muted")}
              style={{ letterSpacing: "-0.01em" }}
            >
              Ask a question
            </h3>
          </div>

          <div className="flex gap-2 mb-3">
            <Input
              id="question" type="text"
              value={question} onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === "Enter" && repoReady && handleQuery()}
              placeholder="How does authentication work?"
              disabled={!repoReady || isQuerying}
            />
            <Button
              onClick={handleQuery}
              disabled={!repoReady || isQuerying || !question.trim()}
              className="shrink-0"
            >
              {isQuerying
                ? <><Loader2 size={13} className="spin" aria-hidden="true" /> Asking…</>
                : "Ask"
              }
            </Button>
          </div>

          {repoReady && !isQuerying && step !== "done" && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs text-c-muted">Examples:</span>
              {QUESTIONS.map(q => <PillChip key={q} label={q} onClick={() => setQuestion(q)} />)}
            </div>
          )}
        </div>

        {/* ── Error ── */}
        {error && (
          <div className="border-t border-c-hairline pt-8 mt-8" role="alert">
            <div className="border border-c-hairline bg-white p-5 rounded-sm">
              <div className="flex items-start gap-3">
                <AlertCircle size={14} className="text-c-error shrink-0 mt-0.5" aria-hidden="true" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-c-ink mb-1">{error.title}</p>
                  <p className="text-sm text-c-body-muted leading-relaxed">{error.body}</p>
                  {error.hint && (
                    <p className="mt-2 font-mono text-xs text-c-muted bg-c-stone px-3 py-2 rounded leading-relaxed">
                      {error.hint}
                    </p>
                  )}
                </div>
                <button onClick={() => setError(null)} className="text-c-muted hover:text-c-ink text-lg leading-none" aria-label="Dismiss">×</button>
              </div>
              <div className="mt-4 ml-5">
                <Button variant="outline" size="sm" onClick={step === "idle" ? handleIngest : handleQuery}>
                  <RefreshCw size={11} aria-hidden="true" /> Retry
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ── Skeleton ── */}
        {isQuerying && (
          <div className="border-t border-c-hairline mt-8">
            <ResultSkeleton />
          </div>
        )}

        {/* ── Answer ── */}
        {result && step === "done" && (
          <div className="border-t border-c-hairline pt-8 mt-8">
            <div className="flex items-center gap-3 mb-6">
              <span className="font-mono text-xs text-c-muted tracking-mono uppercase">Answer</span>
              <span className="font-mono text-xs text-c-muted border border-c-hairline px-2 py-0.5 rounded">{result.pipeline}</span>
              <span className="font-mono text-xs text-c-muted">{result.latency_ms}ms</span>
              <span className="font-mono text-xs text-c-muted">{result.tokens_used} tokens</span>
            </div>

            <div className="border border-c-hairline bg-c-pale-green/60 p-6 rounded-sm text-[15px] text-c-ink leading-[1.7] mb-8 whitespace-pre-wrap">
              {result.answer}
            </div>

            {result.sources?.length > 0 && (
              <>
                <p className="font-mono text-[10px] text-c-muted tracking-mono uppercase mb-3">
                  Sources ({result.sources.length})
                </p>
                <div className="border border-c-hairline rounded-sm mb-6 overflow-hidden">
                  {result.sources.map((s, i) => <SourceRow key={i} source={s} index={i} />)}
                </div>
              </>
            )}

            <Button
              variant="outline"
              onClick={() => { setQuestion(""); setResult(null); setStep("ready"); }}
            >
              Ask another question
            </Button>
          </div>
        )}
      </div>
    </section>
  );
}
