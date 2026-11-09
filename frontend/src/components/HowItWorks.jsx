import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, ShieldCheck, BookOpen, AlertTriangle, ArrowRight, Layers, Database } from 'lucide-react';

const STAGES = [
  {
    step: '01',
    title: 'Visual Embedding & Vector Retrieval',
    subtitle: 'Hugging Face CLIP ViT-B/32 + FAISS',
    icon: Cpu,
    color: '#A9472D',
    description:
      'The uploaded photograph is preprocessed and converted into a 512-dimensional dense visual embedding via openai/clip-vit-base-patch32. The vector is normalized (L2) and queried against a 577-anchor faiss.IndexFlatIP index in under 15 milliseconds.',
    specs: ['512-D Dense Vector', '577 Anchor Embeddings', '< 15 ms Retrieval'],
  },
  {
    step: '02',
    title: 'Dual-Threshold Confidence & Margin Check',
    subtitle: 'Calibrated Rejection Engine',
    icon: ShieldCheck,
    color: '#536B57',
    description:
      'Cosine similarity scores are evaluated against a calibrated acceptance threshold (τ = 0.72). The system enforces candidate margin separation (Δ ≥ 0.05) to eliminate ambiguous ties, immediately rejecting non-architectural photos, modern receipts, and synthetic noise.',
    specs: ['τ_accept = 0.72 Threshold', 'Δ_margin ≥ 0.05 Separation', 'Zero Hallucination'],
  },
  {
    step: '03',
    title: 'Grounded Cultural Discovery & Epigraphy',
    subtitle: 'ASI & UNESCO Curatorial Database',
    icon: BookOpen,
    color: '#B99A5B',
    description:
      'Confirmed identifications link immediately to structured historical monographs, verified dynasties, architectural taxonomy, material composition, construction timelines, and geospatial coordinates referenced from official archival charters.',
    specs: ['100 Catalog Sites', 'Dynasty & Period Metadata', 'Architectural Taxonomy'],
  },
  {
    step: '04',
    title: 'Uncertainty Engine & Tier-2 VLM Adjudication',
    subtitle: 'Gemini 3.1 Flash-Lite + Exception Register',
    icon: AlertTriangle,
    color: '#A9472D',
    description:
      'Specimens with visual ambiguity, extreme angles, or close candidate competition are escalated to Gemini 3.1 Flash-Lite with structured JSON schema. Flagged ambiguities are automatically logged in the Curator Exception Review Registry for human inspection.',
    specs: ['Tier-2 Multimodal VLM', 'Structured JSON Schema', 'Human Review Ledger'],
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 lg:py-28 border-t border-[#E3DFD5] bg-[#F5F3ED]">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div>
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[#A9472D] font-bold mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-[#A9472D]"></span>
              <span>METHODOLOGY // SYSTEM ARCHITECTURE</span>
            </div>
            <h2 className="font-display font-semibold text-3xl sm:text-4xl lg:text-5xl text-[#171816] tracking-tight leading-[1.08]">
              How the Recognition Pipeline Operates.
            </h2>
          </div>
          <p className="max-w-md text-sm sm:text-base text-[#6E7069] leading-relaxed font-sans">
            A deterministic, two-tier visual recognition architecture designed to prioritize epistemic modesty, verifiable historical evidence, and zero hallucination.
          </p>
        </div>

        {/* 4 Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {STAGES.map((stage, idx) => {
            const Icon = stage.icon;
            return (
              <motion.div
                key={stage.step}
                initial={{ opacity: 0, y: 25 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ duration: 0.5, delay: idx * 0.08 }}
                className="bg-[#FFFEFA] border border-[#E3DFD5] rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 hover:border-[#171816]/30 hover:shadow-md"
              >
                <div>
                  {/* Step Number & Icon */}
                  <div className="flex items-center justify-between pb-4 border-b border-[#E3DFD5]/70 mb-4">
                    <span className="font-mono text-xs font-bold text-[#A9472D] tracking-wider">
                      STAGE // {stage.step}
                    </span>
                    <div
                      className="w-8 h-8 rounded-xl flex items-center justify-center"
                      style={{ backgroundColor: `${stage.color}15`, color: stage.color }}
                    >
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>

                  {/* Title & Subtitle */}
                  <h3 className="font-display font-semibold text-lg text-[#171816] leading-snug">
                    {stage.title}
                  </h3>
                  <p className="font-mono text-[11px] text-[#6E7069] uppercase font-semibold mt-1">
                    {stage.subtitle}
                  </p>

                  {/* Description */}
                  <p className="font-sans text-xs text-[#6E7069] leading-relaxed mt-3.5">
                    {stage.description}
                  </p>
                </div>

                {/* Specs badges */}
                <div className="pt-4 mt-5 border-t border-[#E3DFD5]/70 space-y-1.5">
                  {stage.specs.map((spec, sIdx) => (
                    <div
                      key={sIdx}
                      className="font-mono text-[10px] text-[#171816] bg-[#F5F3ED] px-2.5 py-1 rounded-md border border-[#E3DFD5]/60 flex items-center gap-1.5"
                    >
                      <span className="w-1 h-1 rounded-full bg-[#A9472D]"></span>
                      <span className="truncate">{spec}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Pipeline Summary Strip */}
        <div className="mt-12 bg-[#171816] text-[#F5F3ED] rounded-2xl p-6 sm:p-8 flex flex-col lg:flex-row items-center justify-between gap-6 shadow-xl">
          <div className="space-y-1 text-center lg:text-left">
            <span className="font-mono text-[11px] uppercase tracking-wider text-[#B99A5B] font-bold">
              HYBRID RECOGNITION GUARANTEE
            </span>
            <h4 className="font-display font-semibold text-xl sm:text-2xl text-white">
              Deterministic Vector Matching + Guardrailed Multimodal Adjudication
            </h4>
            <p className="font-sans text-xs sm:text-sm text-[#AAB9A4] max-w-2xl">
              Unlike generic AI chat models that guess on landmark identity, our pipeline requires physical vector similarity verification before any architectural claim is made.
            </p>
          </div>

          <a
            href="#recognition"
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-[#A9472D] hover:bg-[#8A3720] text-white text-xs font-mono uppercase tracking-wider font-semibold transition-colors duration-200 cursor-pointer flex-shrink-0 shadow-md"
          >
            <span>Test A Specimen Now</span>
            <ArrowRight className="w-4 h-4 text-[#B99A5B]" />
          </a>
        </div>
      </div>
    </section>
  );
}
