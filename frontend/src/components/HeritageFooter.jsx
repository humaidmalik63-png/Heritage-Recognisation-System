import React from 'react';
import { Landmark, ArrowUp, ShieldCheck, Database, Layers } from 'lucide-react';

export default function HeritageFooter({ onOpenCatalog, onOpenExceptions }) {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-[#171816] text-[#F5F3ED] border-t border-[#2A2B28] pt-16 pb-12">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Footer Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10 pb-12 border-b border-white/10">
          {/* Brand Column (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center gap-2.5">
              <span className="font-display font-bold text-2xl tracking-tight text-white">
                HERITAGE<span className="text-[#A9472D]">.</span>
              </span>
              <span className="font-mono text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-white/10 text-[#B99A5B]">
                ARCHIVAL SYSTEM
              </span>
            </div>
            <p className="font-sans text-xs sm:text-sm text-[#AAB9A4] leading-relaxed max-w-sm">
              Visual Heritage Recognition & Grounded Cultural Discovery Platform. A deterministic two-tier recognition framework pairing 512-D visual embeddings with verifiable historical epigraphy.
            </p>
            <div className="pt-2 flex items-center gap-2 font-mono text-[11px] text-[#6E7069]">
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>100-Site Multimodal Corpus • 577 FAISS Anchors</span>
            </div>
          </div>

          {/* Nav Links Column (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            <h4 className="font-mono text-xs uppercase tracking-wider text-[#B99A5B] font-bold">
              PLATFORM
            </h4>
            <ul className="space-y-2 text-xs font-sans text-[#AAB9A4]">
              <li>
                <a href="#discover" className="hover:text-white transition-colors">
                  Curated Landmarks
                </a>
              </li>
              <li>
                <a href="#archive" className="hover:text-white transition-colors">
                  Indexed Corpus (100)
                </a>
              </li>
              <li>
                <a href="#recognition" className="hover:text-white transition-colors">
                  Recognition Portal
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-white transition-colors">
                  Pipeline Architecture
                </a>
              </li>
              <li>
                <a href="#about" className="hover:text-white transition-colors">
                  Institutional Charter
                </a>
              </li>
            </ul>
          </div>

          {/* Curatorial Tools Column (2 cols) */}
          <div className="lg:col-span-2 space-y-3">
            <h4 className="font-mono text-xs uppercase tracking-wider text-[#B99A5B] font-bold">
              CURATORIAL
            </h4>
            <ul className="space-y-2 text-xs font-sans text-[#AAB9A4]">
              <li>
                <button
                  onClick={onOpenCatalog}
                  className="hover:text-white transition-colors text-left cursor-pointer"
                >
                  Monument Registry Drawer
                </button>
              </li>
              <li>
                <button
                  onClick={onOpenExceptions}
                  className="hover:text-white transition-colors text-left cursor-pointer"
                >
                  Exception Review Ledger
                </button>
              </li>
              <li>
                <a href="/history" className="hover:text-white transition-colors">
                  Archival Survey Log
                </a>
              </li>
            </ul>
          </div>

          {/* Grounding & Citations Column (3 cols) */}
          <div className="lg:col-span-3 space-y-3">
            <h4 className="font-mono text-xs uppercase tracking-wider text-[#B99A5B] font-bold">
              GROUNDED SCHOLARSHIP
            </h4>
            <ul className="space-y-2 text-xs font-sans text-[#AAB9A4]">
              <li>Archaeological Survey of India (ASI)</li>
              <li>UNESCO World Heritage Convention</li>
              <li>ICOMOS Venice & Burra Charters</li>
              <li>OpenAI CLIP ViT-B/32 (Hugging Face)</li>
              <li>Meta FAISS Vector Similarity Engine</li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-[#6E7069] gap-4">
          <div className="flex items-center gap-2">
            <span>© 2026 THE CURATORIAL ARCHIVE</span>
            <span>•</span>
            <span>VISUAL HERITAGE RECOGNITION PLATFORM</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-[11px] text-[#AAB9A4]">LOCAL HYBRID PIPELINE</span>
            <button
              onClick={scrollToTop}
              className="inline-flex items-center gap-1.5 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-white transition-colors cursor-pointer"
              title="Return to top"
            >
              <ArrowUp className="w-3.5 h-3.5" />
              <span className="text-[11px]">Top</span>
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}
