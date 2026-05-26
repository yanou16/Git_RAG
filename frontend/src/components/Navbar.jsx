import { useState } from "react";
import { Github, X } from "lucide-react";
import { Button } from "./ui/button.jsx";

export default function Navbar({ onTryClick }) {
  const [barVisible, setBarVisible] = useState(true);

  return (
    <header className="sticky top-0 z-50">
      {/* Announcement bar */}
      {barVisible && (
        <div className="bg-c-black h-9 flex items-center justify-center px-8 relative">
          <p className="text-white text-xs font-sans">
            GitRAG now supports C#, Java, Rust, Go and 15 more languages.{" "}
            <a
              href="https://github.com/yanou16/Git_RAG"
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 ml-1 hover:text-c-coral transition-colors"
            >
              Star on GitHub
            </a>
          </p>
          <button
            onClick={() => setBarVisible(false)}
            className="absolute right-4 text-white/60 hover:text-white transition-colors"
            aria-label="Dismiss announcement"
          >
            <X size={13} aria-hidden="true" />
          </button>
        </div>
      )}

      {/* Nav */}
      <nav className="bg-white border-b border-c-hairline" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-8 h-16 flex items-center">

          {/* Logo */}
          <a href="#" className="flex items-center gap-2 no-underline shrink-0" aria-label="GitRAG">
            <div className="w-7 h-7 bg-c-primary rounded-sm flex items-center justify-center">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M2 7L5.5 10.5L12 4" stroke="white" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <span className="font-display font-medium text-[15px] text-c-ink tracking-tight">GitRAG</span>
          </a>

          {/* Center links */}
          <div className="flex-1 flex items-center justify-center gap-8">
            <a
              href="#how-it-works"
              className="text-sm text-c-body-muted hover:text-c-ink transition-colors no-underline"
            >
              How it works
            </a>
            <a
              href="#tool"
              className="text-sm text-c-body-muted hover:text-c-ink transition-colors no-underline"
            >
              Try it
            </a>
            <a
              href="https://github.com/yanou16/Git_RAG"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-c-body-muted hover:text-c-ink transition-colors no-underline flex items-center gap-1.5"
            >
              <Github size={14} aria-hidden="true" />
              GitHub
            </a>
          </div>

          {/* CTA */}
          <Button size="default" onClick={onTryClick} className="shrink-0">
            Try it free
          </Button>
        </div>
      </nav>
    </header>
  );
}
