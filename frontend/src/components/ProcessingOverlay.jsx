import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Loader2, Search, Cpu, Database, Compass, Layers } from 'lucide-react';

const STAGES = [
  { label: "Validating Image Byte Stream & Color Space...", icon: Search },
  { label: "Extracting EXIF GPS Metadata & Geodetic Coordinates...", icon: Compass },
  { label: "Computing 512-D Vision Features via CLIP ViT-B/32...", icon: Cpu },
  { label: "Evaluating Zero-Shot Architectural Gatekeeper...", icon: Layers },
  { label: "Searching 50-Anchor FAISS Inner-Product Vector Index...", icon: Database },
  { label: "Synthesizing Curatorial Dossier & Inked Stamps...", icon: Search },
];

export default function ProcessingOverlay({ previewUrl }) {
  const [stageIndex, setStageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 450);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-archive-charcoal/75 backdrop-blur-md p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 260, damping: 20 }}
        className="relative w-full max-w-lg bg-archive-ivory border border-archive-hairline rounded shadow-2xl p-6 sm:p-8 text-center overflow-hidden liquid-glass"
      >
        {/* Reticle / Specimen Container */}
        {previewUrl && (
          <div className="relative w-44 h-44 mx-auto mb-6 rounded border border-archive-hairline overflow-hidden bg-black/10 shadow-inner">
            <img
              src={previewUrl}
              alt="Scanning specimen"
              className="w-full h-full object-cover filter contrast-105"
            />
            {/* Animated Laser Scanning Line */}
            <div className="scanner-line"></div>
            {/* Optical Corner Reticles */}
            <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-archive-terracotta"></div>
            <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-archive-terracotta"></div>
            <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-archive-terracotta"></div>
            <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-archive-terracotta"></div>
          </div>
        )}

        <div className="inline-flex items-center gap-2 px-3 py-1 bg-archive-parchment rounded border border-archive-hairline text-archive-terracotta font-mono text-[10px] tracking-stamp uppercase font-semibold mb-2">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>RECOGNITION PIPELINE ACTIVE</span>
        </div>

        <h3 className="font-serif text-2xl font-bold text-archive-charcoal">
          Verifying Architectural Specimen
        </h3>

        {/* Dynamic Pipeline Telemetry Progress */}
        <div className="mt-6 bg-white/70 border border-archive-hairline rounded p-4 text-left font-mono text-xs space-y-2 shadow-inner">
          {STAGES.map((s, idx) => {
            const isDone = idx < stageIndex;
            const isCurrent = idx === stageIndex;
            const StageIcon = s.icon;
            return (
              <div
                key={idx}
                className={`flex items-center gap-2.5 transition-all ${
                  isDone
                    ? 'text-emerald-700 opacity-90'
                    : isCurrent
                    ? 'text-archive-terracotta font-semibold opacity-100'
                    : 'text-archive-muted opacity-40'
                }`}
              >
                <span className="w-4 text-center font-bold">
                  {isDone ? '✓' : isCurrent ? '▶' : '·'}
                </span>
                <span className="truncate">{s.label}</span>
              </div>
            );
          })}
        </div>

        <p className="mt-4 text-[11px] font-mono text-archive-stone">
          Executing Two-Tier Hybrid Pipeline: Local CLIP (ViT-B/32) + FAISS & Gemini 2.5 Flash VLM
        </p>
      </motion.div>
    </div>
  );
}
