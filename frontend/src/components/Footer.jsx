import { Github, Linkedin } from "lucide-react";

const LINKS = [
  {
    heading: "Product",
    items: [
      { label: "How it works", href: "#how-it-works" },
      { label: "Try it free",  href: "#tool" },
    ],
  },
  {
    heading: "Open source",
    items: [
      { label: "GitHub",         href: "https://github.com/yanou16/Git_RAG", external: true },
      { label: "API docs",       href: "https://yanou16-gitgub-rag.hf.space/docs", external: true },
      { label: "Backend status", href: "https://yanou16-gitgub-rag.hf.space/health", external: true },
    ],
  },
  {
    heading: "Stack",
    items: [
      { label: "FastAPI",  href: "https://fastapi.tiangolo.com", external: true },
      { label: "ChromaDB", href: "https://www.trychroma.com",    external: true },
      { label: "Groq",     href: "https://groq.com",             external: true },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="bg-c-primary text-white/50 px-4 sm:px-8 pt-14 sm:pt-20 pb-10" aria-label="Footer">
      <div className="max-w-5xl mx-auto">

        {/* Top: brand + link columns */}
        <div className="border-b border-white/10 pb-12 sm:pb-16 flex flex-col gap-10 md:grid md:grid-cols-[1fr_auto] md:gap-12">

          {/* Brand */}
          <div>
            <p className="font-mono text-[10px] text-c-coral tracking-mono uppercase mb-4">
              GitRAG
            </p>
            <p
              className="font-display font-light text-white leading-tight mb-6"
              style={{ fontSize: "clamp(24px, 3.5vw, 42px)", letterSpacing: "-0.015em" }}
            >
              Ask your codebase<br />anything.
            </p>
            <div className="flex flex-col gap-3">
              <a
                href="https://github.com/yanou16/Git_RAG"
                target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors no-underline"
              >
                <Github size={14} aria-hidden="true" />
                View source on GitHub
              </a>
              <a
                href="https://www.linkedin.com/in/rayane-louzazna-b7752b224"
                target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors no-underline"
              >
                <Linkedin size={14} aria-hidden="true" />
                Rayane Louzazna
              </a>
            </div>
          </div>

          {/* Link columns — wrap on mobile */}
          <div className="flex flex-wrap gap-8 sm:gap-12 md:gap-16 pt-1">
            {LINKS.map((col) => (
              <div key={col.heading} className="min-w-[100px]">
                <p className="font-mono text-[10px] text-white/30 tracking-mono uppercase mb-4">
                  {col.heading}
                </p>
                <ul className="space-y-3 list-none p-0 m-0">
                  {col.items.map((item) => (
                    <li key={item.label}>
                      <a
                        href={item.href}
                        {...(item.external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                        className="text-sm text-white/50 hover:text-white transition-colors no-underline"
                      >
                        {item.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <p className="font-mono text-xs text-white/25">
            &copy; {new Date().getFullYear()} GitRAG. Open source under MIT.
          </p>
          <p className="font-mono text-xs text-white/25">
            Hosted on{" "}
            <a href="https://huggingface.co/spaces" target="_blank" rel="noopener noreferrer" className="hover:text-white/50 transition-colors">
              HuggingFace Spaces
            </a>
            {" "}· Frontend on{" "}
            <a href="https://vercel.com" target="_blank" rel="noopener noreferrer" className="hover:text-white/50 transition-colors">
              Vercel
            </a>
          </p>
        </div>

      </div>
    </footer>
  );
}
