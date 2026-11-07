import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  MapPin,
  Landmark,
  Clock,
  Layers,
  ChevronRight,
  Compass,
  Search,
  Globe,
  Filter,
  CheckCircle2,
  FileText,
  Navigation
} from 'lucide-react';
import MonumentMap from './MonumentMap';

export default function CatalogDrawer({ isOpen, onClose, monuments }) {
  const [selectedKey, setSelectedKey] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [regionFilter, setRegionFilter] = useState('ALL'); // 'ALL', 'INDIA', 'INTERNATIONAL'
  const [readinessFilter, setReadinessFilter] = useState('ALL'); // 'ALL', 'READY', 'METADATA'
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const monumentEntries = useMemo(() => Object.entries(monuments || {}), [monuments]);

  // Extract unique categories
  const categories = useMemo(() => {
    const cats = new Set();
    monumentEntries.forEach(([_, item]) => {
      if (item.category) cats.add(item.category);
    });
    return Array.from(cats).sort();
  }, [monumentEntries]);

  // Filtered entries
  const filteredEntries = useMemo(() => {
    return monumentEntries.filter(([key, item]) => {
      // 1. Region filter
      const isIndia = (item.country || '').toLowerCase() === 'india';
      if (regionFilter === 'INDIA' && !isIndia) return false;
      if (regionFilter === 'INTERNATIONAL' && isIndia) return false;

      // 2. Readiness filter
      const isReady = item.recognition_readiness === 'RECOGNITION_READY';
      if (readinessFilter === 'READY' && !isReady) return false;
      if (readinessFilter === 'METADATA' && isReady) return false;

      // 3. Category filter
      if (categoryFilter !== 'ALL' && item.category !== categoryFilter) return false;

      // 4. Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const nameMatch = (item.monument_name || '').toLowerCase().includes(q);
        const keyMatch = key.toLowerCase().includes(q);
        const countryMatch = (item.country || '').toLowerCase().includes(q);
        const locMatch = (item.location || `${item.city_region || ''} ${item.state_province || ''}`).toLowerCase().includes(q);
        const styleMatch = (item.architectural_style || '').toLowerCase().includes(q);
        const altMatch = Array.isArray(item.alternate_names) && item.alternate_names.some(a => a.toLowerCase().includes(q));

        if (!nameMatch && !keyMatch && !countryMatch && !locMatch && !styleMatch && !altMatch) {
          return false;
        }
      }

      return true;
    });
  }, [monumentEntries, regionFilter, readinessFilter, categoryFilter, searchQuery]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex justify-end">
        {/* Backdrop Fade */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-archive-charcoal/50 backdrop-blur-sm"
        />

        {/* Slide-in Drawer */}
        <motion.div
          initial={{ x: '100%' }}
          animate={{ x: 0 }}
          exit={{ x: '100%' }}
          transition={{ type: 'spring', stiffness: 220, damping: 25 }}
          className="relative w-full max-w-3xl bg-archive-ivory h-full shadow-2xl flex flex-col border-l border-archive-hairline overflow-hidden z-10"
        >
          {/* Header */}
          <div className="px-6 py-5 bg-archive-parchment/80 border-b border-archive-hairline flex items-center justify-between">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-stamp text-archive-terracotta font-bold flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5" />
                <span>ASI & GLOBAL HERITAGE REGISTRY // PHASE 8.6</span>
              </div>
              <h2 className="font-serif text-2xl font-bold text-archive-charcoal mt-0.5">
                Authoritative 100-Site Catalogue
              </h2>
              <div className="text-xs font-mono text-archive-stone mt-0.5">
                50 Indian Flagship Monuments • 50 International Wonders
              </div>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onClose}
              className="p-2 text-archive-stone hover:text-archive-charcoal hover:bg-white rounded border border-transparent hover:border-archive-hairline transition-all shadow-xs"
              aria-label="Close archive drawer"
            >
              <X className="w-5 h-5" />
            </motion.button>
          </div>

          {/* Search & Filter Toolbar */}
          <div className="px-6 py-3.5 bg-archive-alabaster border-b border-archive-hairline space-y-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-archive-stone absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search monuments by name, alternate name, city, style..."
                className="w-full pl-9 pr-8 py-2 text-xs bg-white border border-archive-hairline rounded text-archive-charcoal placeholder:text-archive-muted focus:outline-none focus:border-archive-terracotta transition-colors shadow-xs"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-archive-muted hover:text-archive-charcoal text-xs"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Filter Tabs & Selectors */}
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              {/* Region Selector */}
              <div className="inline-flex rounded border border-archive-hairline bg-white p-0.5 shadow-xs font-mono text-[11px]">
                <button
                  onClick={() => setRegionFilter('ALL')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    regionFilter === 'ALL'
                      ? 'bg-archive-charcoal text-white font-semibold'
                      : 'text-archive-stone hover:text-archive-charcoal'
                  }`}
                >
                  All (100)
                </button>
                <button
                  onClick={() => setRegionFilter('INDIA')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    regionFilter === 'INDIA'
                      ? 'bg-archive-terracotta text-white font-semibold'
                      : 'text-archive-stone hover:text-archive-charcoal'
                  }`}
                >
                  India (50)
                </button>
                <button
                  onClick={() => setRegionFilter('INTERNATIONAL')}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    regionFilter === 'INTERNATIONAL'
                      ? 'bg-sky-800 text-white font-semibold'
                      : 'text-archive-stone hover:text-archive-charcoal'
                  }`}
                >
                  Global (50)
                </button>
              </div>

              {/* Readiness Filter */}
              <div className="inline-flex rounded border border-archive-hairline bg-white p-0.5 shadow-xs font-mono text-[11px]">
                <button
                  onClick={() => setReadinessFilter('ALL')}
                  className={`px-2 py-1 rounded transition-colors ${
                    readinessFilter === 'ALL' ? 'bg-archive-alabaster font-semibold text-archive-charcoal' : 'text-archive-stone'
                  }`}
                >
                  All Status
                </button>
                <button
                  onClick={() => setReadinessFilter('READY')}
                  className={`px-2 py-1 rounded transition-colors ${
                    readinessFilter === 'READY' ? 'bg-emerald-100 text-emerald-900 font-semibold' : 'text-archive-stone'
                  }`}
                >
                  Vector Ready
                </button>
                <button
                  onClick={() => setReadinessFilter('METADATA')}
                  className={`px-2 py-1 rounded transition-colors ${
                    readinessFilter === 'METADATA' ? 'bg-amber-100 text-amber-900 font-semibold' : 'text-archive-stone'
                  }`}
                >
                  Metadata Only
                </button>
              </div>

              {/* Category Dropdown */}
              <div className="flex items-center gap-1.5 font-mono text-[11px]">
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="bg-white border border-archive-hairline rounded px-2 py-1 text-archive-charcoal focus:outline-none focus:border-archive-terracotta shadow-xs"
                >
                  <option value="ALL">All Categories</option>
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Status bar */}
            <div className="flex items-center justify-between text-[11px] font-mono text-archive-muted pt-1">
              <span>Showing {filteredEntries.length} of {monumentEntries.length} registered sites</span>
              {(searchQuery || regionFilter !== 'ALL' || readinessFilter !== 'ALL' || categoryFilter !== 'ALL') && (
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setRegionFilter('ALL');
                    setReadinessFilter('ALL');
                    setCategoryFilter('ALL');
                  }}
                  className="text-archive-terracotta hover:underline font-semibold"
                >
                  Reset Filters
                </button>
              )}
            </div>
          </div>

          {/* List Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-3">
            {filteredEntries.length === 0 ? (
              <div className="bg-white border border-dashed border-archive-hairline rounded p-12 text-center text-archive-muted font-mono text-xs">
                No heritage monuments match your current filter parameters.
              </div>
            ) : (
              <div className="divide-y divide-archive-hairline border border-archive-hairline rounded bg-white overflow-hidden shadow-sm">
                {filteredEntries.map(([key, item]) => {
                  const isSelected = selectedKey === key;
                  const isIndia = (item.country || '').toLowerCase() === 'india';
                  const isReady = item.recognition_readiness === 'RECOGNITION_READY';
                  const locString = item.location || (item.city_region ? `${item.city_region}, ${item.country}` : item.country);
                  const lat = item.coordinates?.lat;
                  const lng = item.coordinates?.lng;

                  return (
                    <div
                      key={key}
                      className={`transition-colors ${
                        isSelected ? 'bg-archive-alabaster/70' : 'hover:bg-archive-parchment/20'
                      }`}
                    >
                      {/* Row Header */}
                      <div
                        onClick={() => setSelectedKey(isSelected ? null : key)}
                        className="p-4 cursor-pointer flex items-start justify-between gap-4"
                      >
                        <div className="flex-1 min-w-0">
                          {/* Badges */}
                          <div className="flex flex-wrap items-center gap-1.5 mb-1">
                            <span className="font-mono text-[10px] text-archive-terracotta font-semibold uppercase tracking-wider">
                              KEY: {key}
                            </span>
                            <span className={`font-mono text-[9px] uppercase px-1.5 py-0.2 rounded font-bold ${
                              isIndia ? 'bg-orange-50 text-orange-800 border border-orange-200' : 'bg-sky-50 text-sky-800 border border-sky-200'
                            }`}>
                              {item.country || 'Global'}
                            </span>
                            {item.category && (
                              <span className="font-mono text-[9px] uppercase px-1.5 py-0.2 rounded bg-archive-parchment text-archive-stone border border-archive-hairline">
                                {item.category}
                              </span>
                            )}
                            <span className={`font-mono text-[9px] uppercase px-1.5 py-0.2 rounded font-semibold ${
                              isReady
                                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                                : 'bg-slate-100 text-slate-700 border border-slate-200'
                            }`}>
                              {isReady ? 'Vector Anchored' : 'Metadata Only'}
                            </span>
                          </div>

                          <h3 className="font-serif text-lg sm:text-xl font-bold text-archive-charcoal leading-tight">
                            {item.monument_name}
                          </h3>

                          {item.alternate_names && item.alternate_names.length > 0 && (
                            <div className="text-[11px] font-sans text-archive-stone/80 italic mt-0.5 truncate">
                              Also: {item.alternate_names.slice(0, 2).join(' • ')}
                            </div>
                          )}

                          <div className="flex items-center gap-1.5 text-xs text-archive-stone mt-1">
                            <MapPin className="w-3.5 h-3.5 text-archive-terracotta/70 flex-shrink-0" />
                            <span className="truncate">{locString}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 flex-shrink-0 pt-1">
                          {lat !== undefined && lng !== undefined && (
                            <span className="font-mono text-[10px] bg-archive-parchment px-2 py-0.5 border border-archive-hairline rounded text-archive-stone hidden sm:inline-block">
                              {lat.toFixed(2)}° N, {lng.toFixed(2)}° E
                            </span>
                          )}
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
                          className="px-4 pb-5 pt-1 space-y-3.5 text-xs border-t border-archive-hairline/60 bg-white/70"
                        >
                          {/* Metadata Grid */}
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono pt-2">
                            <div className="bg-archive-ivory p-2.5 rounded border border-archive-hairline">
                              <span className="text-[10px] text-archive-muted uppercase block">Architectural Style</span>
                              <span className="font-semibold text-archive-charcoal flex items-center gap-1.5 mt-0.5">
                                <Landmark className="w-3.5 h-3.5 text-archive-terracotta flex-shrink-0" />
                                <span className="truncate">{item.architectural_style || 'Classical Heritage'}</span>
                              </span>
                            </div>

                            <div className="bg-archive-ivory p-2.5 rounded border border-archive-hairline">
                              <span className="text-[10px] text-archive-muted uppercase block">Epoch / Dynasty</span>
                              <span className="font-semibold text-archive-charcoal flex items-center gap-1.5 mt-0.5">
                                <Clock className="w-3.5 h-3.5 text-archive-terracotta flex-shrink-0" />
                                <span className="truncate">{item.historical_period || item.built_by_or_era || 'Historic Period'}</span>
                              </span>
                            </div>
                          </div>

                          {/* Curatorial Monograph */}
                          <div>
                            <span className="font-mono text-[10px] uppercase text-archive-muted tracking-wider block mb-1">
                              Curatorial Monograph
                            </span>
                            <p className="font-sans text-archive-stone leading-relaxed bg-archive-ivory p-3 rounded border border-archive-hairline/70 text-xs">
                              {item.verified_description || item.historical_summary}
                            </p>
                          </div>

                          {/* Preservation Status & Grounded Citations */}
                          <div className="bg-archive-parchment/40 p-3 rounded border border-archive-hairline space-y-1.5">
                            <div className="font-mono text-[10px] uppercase tracking-wider text-archive-stone font-bold">
                              Preservation Framework & Sources:
                            </div>
                            <div className="text-[11px] font-sans text-archive-charcoal">
                              {item.preservation_status || 'Centrally Protected Monument / World Heritage Inscription'}
                            </div>
                            {item.sources && (
                              <ul className="list-disc list-inside text-[10px] font-mono text-archive-muted pt-1 space-y-0.5">
                                {item.sources.map((src, i) => (
                                  <li key={i}>{src}</li>
                                ))}
                              </ul>
                            )}
                          </div>

                          {/* Embedded Interactive Map for Selected Monument */}
                          {item.coordinates && (
                            <div className="pt-2">
                              <div className="font-mono text-[10px] uppercase tracking-wider text-archive-stone font-bold mb-2 flex items-center justify-between">
                                <span className="flex items-center gap-1">
                                  <Navigation className="w-3 h-3 text-archive-terracotta" />
                                  Geodetic Coordinates ({item.coordinates.lat.toFixed(4)}°, {item.coordinates.lng.toFixed(4)}°)
                                </span>
                                <span className="text-archive-muted font-normal">OpenStreetMap Satellite Geodesy</span>
                              </div>
                              <MonumentMap
                                coordinates={item.coordinates}
                                monumentName={item.monument_name}
                                location={locString}
                                catalogId={key.toUpperCase()}
                              />
                            </div>
                          )}
                        </motion.div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 bg-archive-parchment/70 border-t border-archive-hairline flex items-center justify-between text-xs font-mono text-archive-muted">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
              <span>100 UNIQUE SITES • 100% AUDITED REPOSITORY</span>
            </span>
            <button
              onClick={onClose}
              className="px-4 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline rounded font-medium transition-colors shadow-xs"
            >
              Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
