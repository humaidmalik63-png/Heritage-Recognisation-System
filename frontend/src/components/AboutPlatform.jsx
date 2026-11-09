import React from 'react';
import { ShieldCheck, Database, Cpu, Sparkles, Scale, Server, CheckCircle2, Award } from 'lucide-react';

export default function AboutPlatform({ health, monumentsCount = 100 }) {
  const isHealthy = health?.status === 'ok' || health?.status === 'healthy';
  const vectorCount = health?.faiss_vectors || health?.vectors_count || 577;
  const clipModel = health?.clip_model || 'openai/clip-vit-base-patch32';
  const tier2Model = health?.gemini_model || 'gemini-3.1-flash-lite';

  return (
    <section id="about" className="py-20 lg:py-28 border-t border-[#E3DFD5] bg-[#FFFEFA]">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div>
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[#A9472D] font-bold mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-[#A9472D]"></span>
              <span>INSTITUTIONAL CHARTER // MISSION & STANDARDS</span>
            </div>
            <h2 className="font-display font-semibold text-3xl sm:text-4xl lg:text-5xl text-[#171816] tracking-tight leading-[1.08]">
              Preserving Cultural Identity With Epistemic Rigour.
            </h2>
          </div>
          <p className="max-w-md text-sm sm:text-base text-[#6E7069] leading-relaxed font-sans">
            Developed as an open, grounded cultural recognition platform designed to eliminate hallucinations, respect architectural sovereignty, and provide verifiable historical monographs.
          </p>
        </div>

        {/* 2-Column Institutional & Architectural Content */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start mb-16">
          {/* Left Column: Philosophical Foundation (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            <div className="bg-[#F5F3ED] border border-[#E3DFD5] rounded-3xl p-6 sm:p-8">
              <h3 className="font-display font-semibold text-2xl text-[#171816] mb-3">
                The Curatorial Archive Initiative
              </h3>
              <p className="font-sans text-sm sm:text-base text-[#6E7069] leading-relaxed mb-4">
                Monument recognition systems frequently fail in two critical dimensions: they confabulate certainty on ambiguous visual fragments, and they disconnect visual identification from grounded cultural scholarship.
              </p>
              <p className="font-sans text-sm text-[#6E7069] leading-relaxed">
                Our platform enforces a strict epistemic standard: every architectural attribution is verified against calibrated 512-dimensional vector bounds. If an image depicts an out-of-catalog site, severe occlusion, or architectural ambiguity, the system flags the specimen for human curator inspection rather than synthesizing false claims.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-6 mt-6 border-t border-[#E3DFD5]">
                <div className="space-y-1">
                  <span className="font-mono text-[10px] text-[#A9472D] font-bold uppercase block">
                    GOVERNANCE
                  </span>
                  <h4 className="font-serif text-sm font-semibold text-[#171816]">
                    Human-in-the-Loop
                  </h4>
                  <p className="font-sans text-xs text-[#6E7069]">
                    Ambiguous scans log directly to the Curator Exception Ledger.
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="font-mono text-[10px] text-[#B99A5B] font-bold uppercase block">
                    GROUNDING
                  </span>
                  <h4 className="font-serif text-sm font-semibold text-[#171816]">
                    ASI & UNESCO Citations
                  </h4>
                  <p className="font-sans text-xs text-[#6E7069]">
                    Every factual assertion links to verified archival registries.
                  </p>
                </div>

                <div className="space-y-1">
                  <span className="font-mono text-[10px] text-[#536B57] font-bold uppercase block">
                    PRECISION
                  </span>
                  <h4 className="font-serif text-sm font-semibold text-[#171816]">
                    Calibrated Margin
                  </h4>
                  <p className="font-sans text-xs text-[#6E7069]">
                    Cosine margin separation prevents ambiguous attribution ties.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Live Backend Telemetry (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-[#171816] text-[#F5F3ED] rounded-3xl p-6 sm:p-7 shadow-xl border border-[#171816]">
              <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-5">
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-[#B99A5B]" />
                  <span className="font-mono text-xs uppercase tracking-wider font-bold">
                    LIVE SYSTEM TELEMETRY
                  </span>
                </div>
                <div className="flex items-center gap-1.5 font-mono text-[11px]">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                    }`}
                  />
                  <span className={isHealthy ? 'text-emerald-400' : 'text-amber-400'}>
                    {isHealthy ? 'ENGINE ONLINE' : 'STANDBY'}
                  </span>
                </div>
              </div>

              {/* Telemetry rows */}
              <div className="space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                  <span className="text-[#6E7069]">Vector Database</span>
                  <span className="text-white font-bold">{vectorCount} L2-Normalized Vectors</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                  <span className="text-[#6E7069]">Monuments Catalog</span>
                  <span className="text-white font-bold">{monumentsCount} Heritage Sites</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                  <span className="text-[#6E7069]">Tier-1 CLIP Encoder</span>
                  <span className="text-[#B99A5B] font-bold truncate max-w-[190px]">
                    {clipModel}
                  </span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                  <span className="text-[#6E7069]">Tier-2 Multimodal VLM</span>
                  <span className="text-[#A9C8D4] font-bold">{tier2Model}</span>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                  <span className="text-[#6E7069]">Acceptance Threshold</span>
                  <span className="text-white font-bold">τ ≥ 0.72 (Margin Δ ≥ 0.05)</span>
                </div>
              </div>

              <div className="mt-5 pt-4 border-t border-white/10 text-[11px] font-mono text-white/50 text-center">
                FASTAPI v0.115 • FAISS-CPU • Uvicorn 8001
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
