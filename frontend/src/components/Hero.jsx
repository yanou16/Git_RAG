import { Button } from "./ui/button.jsx";

/* Agent console card lines */
const CONSOLE = [
  { role: "label", text: "QUERY" },
  { role: "query", text: "How does the routing system work?" },
  { role: "divider" },
  { role: "label", text: "PIPELINE" },
  { role: "step",  tag: "01", text: "Semantic embedding       0.14s" },
  { role: "step",  tag: "02", text: "BM25 keyword match       0.03s" },
  { role: "step",  tag: "03", text: "RRF fusion + rerank      0.22s" },
  { role: "divider" },
  { role: "label", text: "ANSWER" },
  { role: "answer", text: "The routing system maps URL patterns to view\nfunctions using @app.route(), which internally\ncalls add_url_rule() on the Werkzeug Map." },
  { role: "divider" },
  { role: "src",  text: "routing.py:45   app.py:120   helpers.py:88" },
];

const STATS = [
  { val: "15+",    label: "languages" },
  { val: "3-stage", label: "pipeline" },
  { val: "< 30s",  label: "per query" },
];

export default function Hero({ onTryClick }) {
  return (
    <section className="bg-c-canvas" aria-label="Hero">
      {/* ── Top: monumental type ── */}
      <div className="max-w-7xl mx-auto px-8 pt-20 pb-16 text-center">
        <p className="font-mono text-xs text-c-muted tracking-mono uppercase mb-8">
          AI Code Search
        </p>

        <h1
          className="font-display font-light text-c-ink leading-none tracking-hero mx-auto"
          style={{ fontSize: "clamp(52px, 7vw, 96px)", maxWidth: "14ch", letterSpacing: "-0.02em" }}
        >
          Ask your codebase anything.
        </h1>

        <p className="text-lg text-c-body-muted leading-[1.4] max-w-lg mx-auto mt-7 mb-10">
          GitRAG indexes repositories with embeddings, then answers questions
          with exact source references, understanding intent not just keywords.
        </p>

        <div className="flex items-center justify-center gap-8">
          <Button size="lg" onClick={onTryClick}>
            Try it free
          </Button>
          <a
            href="https://github.com/yanou16/Git_RAG"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-c-ink underline underline-offset-2 hover:text-c-primary transition-colors"
          >
            View source
          </a>
        </div>
      </div>

      {/* ── Agent console card ── */}
      <div className="max-w-5xl mx-auto px-8 pb-24">
        <div
          className="bg-c-primary rounded-lg overflow-hidden"
          style={{ boxShadow: "0 32px 64px rgba(23,23,28,0.18)" }}
        >
          {/* Card header */}
          <div className="border-b border-white/10 px-6 py-4 flex items-center gap-3">
            <div className="flex gap-1.5" aria-hidden="true">
              <span className="w-2.5 h-2.5 rounded-full bg-white/20" />
              <span className="w-2.5 h-2.5 rounded-full bg-white/20" />
              <span className="w-2.5 h-2.5 rounded-full bg-white/20" />
            </div>
            <span className="font-mono text-[11px] text-white/30 tracking-mono uppercase ml-2">
              GitRAG console
            </span>
            <span className="ml-auto flex items-center gap-1.5 text-[11px] font-mono text-c-coral">
              <span className="w-1.5 h-1.5 rounded-full bg-c-coral" aria-hidden="true" />
              live
            </span>
          </div>

          {/* Card body */}
          <div className="px-6 py-6 font-mono text-[13px] leading-[1.8] space-y-1">
            {CONSOLE.map((line, i) => {
              if (line.role === "divider")
                return <div key={i} className="border-t border-white/10 my-4" aria-hidden="true" />;
              if (line.role === "label")
                return (
                  <p key={i} className="text-white/30 text-[10px] tracking-mono uppercase mb-1">
                    {line.text}
                  </p>
                );
              if (line.role === "query")
                return (
                  <p key={i} className="text-white font-sans text-sm">
                    "{line.text}"
                    <span className="cursor" aria-hidden="true" />
                  </p>
                );
              if (line.role === "step")
                return (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-c-coral text-[10px] tracking-mono">{line.tag}</span>
                    <span className="text-white/50">{line.text}</span>
                    <span className="ml-auto text-[10px] text-c-coral/70">done</span>
                  </div>
                );
              if (line.role === "answer")
                return (
                  <p key={i} className="text-white/90 font-sans text-sm leading-relaxed whitespace-pre-line">
                    {line.text}
                  </p>
                );
              if (line.role === "src")
                return (
                  <p key={i} className="text-c-coral/80 text-[11px]">{line.text}</p>
                );
              return null;
            })}
          </div>

          {/* Stats strip */}
          <div className="border-t border-white/10 px-6 py-4 flex gap-10">
            {STATS.map(s => (
              <div key={s.label}>
                <div className="font-display text-white font-light text-xl leading-none tracking-tight">
                  {s.val}
                </div>
                <div className="font-mono text-[10px] text-white/30 uppercase tracking-mono mt-1">
                  {s.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
