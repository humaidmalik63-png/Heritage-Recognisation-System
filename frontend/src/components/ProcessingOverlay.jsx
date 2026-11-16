import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Compass, Cpu, Layers, Database, X, AlertTriangle, RefreshCw } from 'lucide-react';
import { DISPLAY_ANCHOR_COUNT } from '../constants/displayMetrics';

const STAGES = [
  { label: "Validating Image Byte Stream & Color Space...", icon: Search },
  { label: "Extracting EXIF GPS Metadata & Geodetic Coordinates...", icon: Compass },
  { label: "Computing 512-D Vision Features via CLIP ViT-B/32...", icon: Cpu },
  { label: "Evaluating Zero-Shot Architectural Gatekeeper...", icon: Layers },
  { label: `Searching ${DISPLAY_ANCHOR_COUNT}-Vector FAISS Inner-Product Index...`, icon: Database },
  { label: "Synthesizing Curatorial Dossier & Inked Stamps...", icon: Search },
];

export default function ProcessingOverlay({ previewUrl, onCancel }) {
  const [stageIndex, setStageIndex] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStageIndex((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
    }, 450);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((s) => s + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Escape key dismiss listener (A4)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && onCancel) {
        onCancel();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center bg-archive-charcoal/80 p-4 backdrop-blur-xs">
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ type: 'spring', stiffness: 280, damping: 24 }}
        className="relative w-full max-w-lg bg-archive-ivory border border-archive-hairline rounded-2xl shadow-2xl p-6 sm:p-8 text-center overflow-hidden"
      >
        {/* Reticle / Specimen Container */}
        {previewUrl && (
          <div className="relative w-40 h-40 sm:w-44 sm:h-44 mx-auto mb-5 rounded-xl border border-archive-hairline overflow-hidden bg-black/10 shadow-inner">
            <img
              src={previewUrl}
              alt="Scanning specimen"
              className="w-full h-full object-cover filter contrast-105"
            />
            {/* 1px Archival Scanline */}
            <div className="scanner-line"></div>
            {/* Optical Corner Reticles */}
            <div className="absolute top-1.5 left-1.5 w-2.5 h-2.5 border-t border-l border-archive-terracotta"></div>
            <div className="absolute top-1.5 right-1.5 w-2.5 h-2.5 border-t border-r border-archive-terracotta"></div>
            <div className="absolute bottom-1.5 left-1.5 w-2.5 h-2.5 border-b border-l border-archive-terracotta"></div>
            <div className="absolute bottom-1.5 right-1.5 w-2.5 h-2.5 border-b border-r border-archive-terracotta"></div>
          </div>
        )}

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-archive-parchment rounded-full border border-archive-hairline text-archive-terracotta font-mono text-[10px] tracking-stamp uppercase font-semibold mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-archive-terracotta animate-pulse"></span>
          <span>RECOGNITION PIPELINE ACTIVE</span>
          <span className="text-archive-stone font-mono text-[9px] ml-1">({elapsedSeconds}s)</span>
        </div>

        <h3 className="font-serif text-2xl font-bold text-archive-charcoal">
          Verifying Architectural Specimen
        </h3>

        {/* Dynamic Pipeline Telemetry Progress */}
        <div className="mt-5 bg-archive-alabaster/60 border border-archive-hairline rounded-xl p-3.5 text-left font-mono text-xs space-y-1.5 shadow-xs">
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

        {/* 25s warning & 45s honest retry prompt (A4) */}
        {elapsedSeconds >= 45 ? (
          <div className="mt-3.5 p-3 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-center justify-between gap-2 text-left">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-700 flex-shrink-0" />
              <span>Multi-tier curatorial synthesis is taking longer than expected. You may cancel and retry.</span>
            </div>
          </div>
        ) : elapsedSeconds >= 25 ? (
          <div className="mt-3.5 p-2.5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 text-[11px] flex items-center gap-2 text-left font-sans">
            <RefreshCw className="w-3.5 h-3.5 text-amber-700 animate-spin flex-shrink-0" />
            <span>Tier 2 Multimodal VLM analysis in progress. Synthesizing authoritative architectural dossier...</span>
          </div>
        ) : null}

        {/* Prominent Cancel Button & Escape hint (A4) */}
        <div className="mt-5 flex items-center justify-center gap-3">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-5 py-2 rounded-xl bg-[#171816] hover:bg-[#A9472D] text-white font-mono text-xs uppercase tracking-wider font-semibold transition-colors flex items-center gap-2 shadow-xs cursor-pointer active:scale-95"
            >
              <X className="w-4 h-4" />
              <span>Cancel Scan</span>
              <span className="text-[10px] text-white/60 font-mono hidden sm:inline">(ESC)</span>
            </button>
          )}
        </div>

        <p className="mt-3.5 text-[10px] font-mono text-archive-stone">
          Executing Two-Tier Hybrid Pipeline: Local CLIP (ViT-B/32) + FAISS & Multimodal VLM
        </p>
      </motion.div>
    </div>
  );
}
