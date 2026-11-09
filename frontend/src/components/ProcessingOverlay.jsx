import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Compass, Cpu, Layers, Database } from 'lucide-react';

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
    <div className="fixed inset-0 z-[120] flex items-center justify-center bg-archive-charcoal/80 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 280, damping: 24 }}
        className="relative w-full max-w-lg bg-archive-ivory border border-archive-hairline rounded shadow-2xl p-6 sm:p-8 text-center overflow-hidden"
      >
        {/* Reticle / Specimen Container */}
        {previewUrl && (
          <div className="relative w-44 h-44 mx-auto mb-5 rounded border border-archive-hairline overflow-hidden bg-black/10 shadow-inner">
            <img
              src={previewUrl}
              alt="Scanning specimen"
              className="w-full h-full object-cover filter contrast-105"
            />
            {/* 1px Razor-thin Archival Scanline */}
            <div className="scanner-line"></div>
            {/* Optical Corner Reticles */}
            <div className="absolute top-1.5 left-1.5 w-2.5 h-2.5 border-t border-l border-archive-terracotta"></div>
            <div className="absolute top-1.5 right-1.5 w-2.5 h-2.5 border-t border-r border-archive-terracotta"></div>
            <div className="absolute bottom-1.5 left-1.5 w-2.5 h-2.5 border-b border-l border-archive-terracotta"></div>
            <div className="absolute bottom-1.5 right-1.5 w-2.5 h-2.5 border-b border-r border-archive-terracotta"></div>
          </div>
        )}

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-archive-parchment rounded border border-archive-hairline text-archive-terracotta font-mono text-[10px] tracking-stamp uppercase font-semibold mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-archive-terracotta"></span>
          <span>RECOGNITION PIPELINE ACTIVE</span>
        </div>

        <h3 className="font-serif text-2xl font-bold text-archive-charcoal">
          Verifying Architectural Specimen
        </h3>

        {/* Dynamic Pipeline Telemetry Progress */}
        <div className="mt-5 bg-archive-alabaster/60 border border-archive-hairline rounded p-3.5 text-left font-mono text-xs space-y-1.5 shadow-xs">
          {STAGES.map((s, idx) => {
            const isDone = idx < stageIndex;
            const isCurrent = idx === stageIndex;
            return (
              <div
                key={idx}
                className={`flex items-center gap-2 transition-all ${
                  isDone
                    ? 'text-emerald-800 opacity-90'
                    : isCurrent
                    ? 'text-archive-terracotta font-semibold opacity-100'
                    : 'text-archive-muted opacity-40'
                }`}
              >
                <span className="w-3.5 text-center font-bold text-[11px]">
                  {isDone ? '✓' : isCurrent ? '›' : '·'}
                </span>
                <span className="truncate text-[11px]">{s.label}</span>
              </div>
            );
          })}
        </div>

        <p className="mt-4 text-[10px] font-mono text-archive-stone">
          Executing Two-Tier Hybrid Pipeline: Local CLIP (ViT-B/32) + FAISS & Multimodal VLM
        </p>
      </motion.div>
    </div>
  );
}
