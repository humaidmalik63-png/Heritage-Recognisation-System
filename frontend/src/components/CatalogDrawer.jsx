import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, MapPin, Landmark, Clock, Layers, ChevronRight, Compass } from 'lucide-react';

export default function CatalogDrawer({ isOpen, onClose, monuments }) {
  const [selectedKey, setSelectedKey] = useState(null);

  if (!isOpen) return null;

  const monumentEntries = Object.entries(monuments || {});

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop Fade */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-archive-charcoal/40 backdrop-blur-sm"
        />

        {/* Slide-in Drawer */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', stiffness: 220, damping: 25 }}
          className="relative w-full max-w-2xl bg-archive-ivory h-full shadow-2xl flex flex-col border-l border-archive-hairline overflow-hidden z-10"
        >
          {/* Header */}
          <div className="px-6 py-5 bg-archive-parchment/70 border-b border-archive-hairline flex items-center justify-between">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-stamp text-archive-terracotta font-bold">
                ASI REGISTRY CATALOGUE
              </div>
              <h2 className="font-serif text-2xl font-bold text-archive-charcoal">
                Indexed Flagship Monuments ({monumentEntries.length})
              </h2>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onClose}
              className="p-2 text-archive-stone hover:text-archive-charcoal hover:bg-white rounded border border-transparent hover:border-archive-hairline transition-all"
              aria-label="Close archive drawer"
            >
              <X className="w-5 h-5" />
            </motion.button>
          </div>

          {/* List Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            <p className="text-xs text-archive-stone font-sans leading-relaxed bg-archive-alabaster p-3.5 rounded border border-archive-hairline">
              The on-device FAISS vector matrix is seeded with 50 precomputed 512-D visual anchors (4 exterior aspects + 1 normalized geometric centroid per monument) guaranteeing offline, high-speed tier-1 retrieval.
            </p>

            {/* List with logic grouping */}
            <div className="divide-y divide-archive-hairline border border-archive-hairline rounded bg-white overflow-hidden shadow-sm">
              {monumentEntries.map(([key, item]) => {
                const isSelected = selectedKey === key;
                return (
                  <div
                    key={key}
                    className={`transition-colors ${
                      isSelected ? 'bg-archive-alabaster/60' : 'hover:bg-archive-parchment/20'
                    }`}
                  >
                    <div
                      onClick={() => setSelectedKey(isSelected ? null : key)}
                      className="p-4 cursor-pointer flex items-start justify-between gap-4"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-archive-terracotta font-semibold uppercase tracking-wider">
                            KEY: {key}
                          </span>
                        </div>
                        <h3 className="font-serif text-xl font-bold text-archive-charcoal mt-0.5">
                          {item.monument_name}
                        </h3>
                        <div className="flex items-center gap-1.5 text-xs text-archive-stone mt-1">
                          <MapPin className="w-3.5 h-3.5 text-archive-terracotta/70 flex-shrink-0" />
                          <span>{item.location}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-3 flex-shrink-0">
                        <span className="font-mono text-[10px] bg-archive-parchment px-2 py-0.5 border border-archive-hairline rounded text-archive-stone">
                          {item.coordinates.lat.toFixed(4)}° N
                        </span>
                        <ChevronRight
                          className={`w-4 h-4 text-archive-muted transition-transform duration-200 ${
                            isSelected ? 'rotate-90 text-archive-terracotta' : ''
                          }`}
                        />
                      </div>
                    </div>

                    {/* Accordion Detail Reveal */}
                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="px-4 pb-4 pt-1 space-y-3 text-xs"
                      >
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono">
                          <div className="bg-archive-ivory p-2.5 rounded border border-archive-hairline">
                            <span className="text-[10px] text-archive-muted uppercase block">Architecture</span>
                            <span className="font-semibold text-archive-charcoal flex items-center gap-1.5 mt-0.5">
                              <Landmark className="w-3.5 h-3.5 text-archive-terracotta flex-shrink-0" />
                              <span className="truncate">{item.architectural_style}</span>
                            </span>
                          </div>

                          <div className="bg-archive-ivory p-2.5 rounded border border-archive-hairline">
                            <span className="text-[10px] text-archive-muted uppercase block">Built By / Period</span>
                            <span className="font-semibold text-archive-charcoal flex items-center gap-1.5 mt-0.5">
                              <Clock className="w-3.5 h-3.5 text-archive-terracotta flex-shrink-0" />
                              <span className="truncate">{item.built_by_or_era}</span>
                            </span>
                          </div>
                        </div>

                        <div>
                          <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block mb-1">
                            Curatorial Monograph
                          </span>
                          <p className="font-sans text-archive-stone leading-relaxed bg-archive-ivory p-3 rounded border border-archive-hairline/70">
                            {item.historical_summary}
                          </p>
                        </div>

                        <div>
                          <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block mb-1.5">
                            Structural Traits Detected
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {item.structural_features_detected.map((feat, i) => (
                              <span
                                key={i}
                                className="font-mono text-[10px] bg-white border border-archive-hairline px-2 py-0.5 rounded text-archive-charcoal"
                              >
                                • {feat}
                              </span>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 bg-archive-parchment/60 border-t border-archive-hairline flex items-center justify-between text-xs font-mono text-archive-muted">
            <span>OFFICIAL ASI REGISTER ARCHIVE</span>
            <button
              onClick={onClose}
              className="px-4 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
