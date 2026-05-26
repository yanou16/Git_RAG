const STEPS = [
  {
    num: "01",
    title: "Index your repo",
    desc: "Paste any public GitHub URL. GitRAG clones it, parses every file with AST-aware chunking, and stores vector embeddings in ChromaDB.",
    tag: "~20s",
  },
  {
    num: "02",
    title: "Hybrid retrieval",
    desc: "Your question is matched using semantic embeddings for intent and BM25 for exact terms, then fused with Reciprocal Rank Fusion.",
    tag: "BM25 + semantic",
  },
  {
    num: "03",
    title: "Cohere reranking",
    desc: "A cross-encoder model rescores the top 20 candidates so only the most relevant code chunks reach the LLM, cutting noise by 4x.",
    tag: "Top 20 to 5",
  },
  {
    num: "04",
    title: "Grounded answer",
    desc: "Groq's llama-3.3-70b generates a precise answer grounded in the actual code, with file paths and line numbers you can verify.",
    tag: "Groq llama-3.3-70b",
  },
];

const FEATURES = [
  {
    title: "No hallucination",
    desc: "Every answer is grounded in actual source code retrieved from your repository. If the answer isn't in the codebase, it won't be invented.",
  },
  {
    title: "Any language",
    desc: "Python, C#, Java, Go, Rust, TypeScript, Kotlin, Swift, Dart, Ruby and more. AST chunking understands structure, not just text.",
  },
  {
    title: "Fully open source",
    desc: "Deploy on HuggingFace Spaces, bring your own API keys, zero lock-in. The entire pipeline is readable and forkable on GitHub.",
  },
];

export default function HowItWorks() {
  return (
    <>
      {/* ── Pipeline rows ── */}
      <section
        id="how-it-works"
        className="bg-c-canvas py-24 px-8"
        aria-label="How it works"
      >
        <div className="max-w-5xl mx-auto">
          <p className="font-mono text-xs text-c-muted tracking-mono uppercase mb-6">
            The pipeline
          </p>
          <h2
            className="font-display font-light text-c-ink leading-snug tracking-display mb-16"
            style={{ fontSize: "clamp(36px, 5vw, 60px)", letterSpacing: "-0.015em" }}
          >
            Four stages, zero hallucination.
          </h2>

          {/* Rule-separated rows */}
          <div className="border-t border-c-hairline">
            {STEPS.map((step) => (
              <div
                key={step.num}
                className="border-b border-c-hairline py-8 grid gap-4"
                style={{ gridTemplateColumns: "56px 1fr auto" }}
              >
                <span className="font-mono text-sm text-c-muted pt-0.5">{step.num}</span>
                <div>
                  <h3 className="font-display font-normal text-xl text-c-ink leading-snug mb-2"
                      style={{ letterSpacing: "-0.01em" }}>
                    {step.title}
                  </h3>
                  <p className="text-base text-c-body-muted leading-[1.5] max-w-xl">
                    {step.desc}
                  </p>
                </div>
                <span className="font-mono text-xs text-c-muted tracking-mono uppercase self-center whitespace-nowrap">
                  {step.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Dark feature band ── */}
      <section
        className="bg-c-green py-24 px-8"
        aria-label="Capabilities"
      >
        <div className="max-w-5xl mx-auto">
          <h2
            className="font-display font-light text-white leading-none mb-16"
            style={{ fontSize: "clamp(36px, 5vw, 60px)", letterSpacing: "-0.015em" }}
          >
            Built for code.<br />Trained on intent.
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-t border-white/20">
            {FEATURES.map((f) => (
              <div key={f.title} className="border-b md:border-b-0 md:border-r border-white/20 pt-8 pr-8 pb-8 last:border-r-0">
                <h3 className="font-display font-normal text-white text-xl mb-3"
                    style={{ letterSpacing: "-0.01em" }}>
                  {f.title}
                </h3>
                <p className="text-[15px] text-white/55 leading-[1.5]">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
