import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Filter, MapPin, ScanLine, ArrowUpRight, Compass, Database, Globe, ChevronDown } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function ExploreArchive({ monuments = {}, onTestSample, onOpenCatalogDrawer }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [regionFilter, setRegionFilter] = useState('ALL'); // 'ALL' | 'INDIA' | 'INTERNATIONAL'
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [visibleCount, setVisibleCount] = useState(12);

  const entries = useMemo(() => Object.entries(monuments), [monuments]);

  // Extract categories dynamically
  const categories = useMemo(() => {
    const set = new Set();
    entries.forEach(([_, item]) => {
      if (item.category) set.add(item.category);
    });
    return Array.from(set).sort();
  }, [entries]);

  // Filtered monuments
  const filtered = useMemo(() => {
    return entries.filter(([key, item]) => {
      const isIndia = (item.country || '').toLowerCase() === 'india';
      if (regionFilter === 'INDIA' && !isIndia) return false;
      if (regionFilter === 'INTERNATIONAL' && isIndia) return false;

      if (categoryFilter !== 'ALL' && item.category !== categoryFilter) return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const nameMatch = (item.monument_name || '').toLowerCase().includes(q);
        const locMatch = (item.location || `${item.city_region || ''} ${item.country || ''}`).toLowerCase().includes(q);
        const styleMatch = (item.architectural_style || '').toLowerCase().includes(q);
        const catMatch = (item.category || '').toLowerCase().includes(q);
        return nameMatch || locMatch || styleMatch || catMatch;
      }
      return true;
    });
  }, [entries, regionFilter, categoryFilter, searchQuery]);

  const displayed = filtered.slice(0, visibleCount);

  const handleTestInScanner = (key) => {
    if (onTestSample) {
      onTestSample(key);
      const el = document.getElementById('recognition');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <section id="archive" className="py-20 lg:py-28 border-t border-[#E3DFD5] bg-[#FFFEFA]">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-6">
          <div>
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[#A9472D] font-bold mb-3">
              <Database className="w-3.5 h-3.5 text-[#A9472D]" />
              <span>THE RECOGNITION ARCHIVE // 100 MONUMENT SITES</span>
            </div>
            <h2 className="font-display font-semibold text-3xl sm:text-4xl lg:text-5xl text-[#171816] tracking-tight leading-[1.08]">
              Explore the Indexed Corpus.
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onOpenCatalogDrawer}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl border border-[#171816] bg-[#171816] text-[#F5F3ED] hover:bg-[#A9472D] hover:border-[#A9472D] text-xs font-mono uppercase tracking-wider font-semibold transition-colors duration-200 cursor-pointer shadow-sm"
            >
              <Globe className="w-3.5 h-3.5 text-[#B99A5B]" />
              <span>Open Full Registry & Map ({entries.length})</span>
            </button>
          </div>
        </div>

        {/* Filter Bar */}
        <div className="bg-[#F5F3ED] border border-[#E3DFD5] rounded-2xl p-4 sm:p-5 mb-8">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-[#6E7069] absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by landmark name, city, dynasty, or style..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 text-sm bg-[#FFFEFA] border border-[#E3DFD5] rounded-xl text-[#171816] placeholder:text-[#6E7069] focus:outline-none focus:border-[#A9472D] focus:ring-1 focus:ring-[#A9472D]"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-[#6E7069] hover:text-[#171816] font-mono"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Filter Buttons */}
            <div className="flex flex-wrap items-center gap-2">
              {/* Region Selector */}
              <div className="inline-flex rounded-xl border border-[#E3DFD5] bg-[#FFFEFA] p-0.5 text-xs font-mono">
                {['ALL', 'INDIA', 'INTERNATIONAL'].map((r) => (
                  <button
                    key={r}
                    onClick={() => setRegionFilter(r)}
                    className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer uppercase font-medium ${
                      regionFilter === r
                        ? 'bg-[#171816] text-[#F5F3ED]'
                        : 'text-[#6E7069] hover:text-[#171816]'
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>

              {/* Category Dropdown */}
              {categories.length > 0 && (
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="px-3 py-2 text-xs font-mono uppercase bg-[#FFFEFA] border border-[#E3DFD5] rounded-xl text-[#171816] focus:outline-none focus:border-[#A9472D]"
                >
                  <option value="ALL">All Categories ({entries.length})</option>
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono text-[#6E7069] mt-3 pt-3 border-t border-[#E3DFD5]/60">
            <span>
              Showing <strong className="text-[#171816]">{displayed.length}</strong> of{' '}
              <strong className="text-[#171816]">{filtered.length}</strong> indexed monuments
            </span>
            <span>EMBEDDINGS: OPENAI CLIP-VIT-B/32 (512-D)</span>
          </div>
        </div>

        {/* Monument Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          {displayed.map(([key, item]) => {
            const isReady = item.recognition_readiness === 'RECOGNITION_READY';
            const locationStr = item.location || `${item.city_region || ''}, ${item.country || ''}`;

            return (
              <div
                key={key}
                className="group bg-[#FFFEFA] border border-[#E3DFD5] rounded-xl p-4 flex flex-col justify-between transition-all duration-200 hover:border-[#171816]/30 hover:shadow-md"
              >
                <div>
                  {/* Card Header with Category & Readiness */}
                  <div className="flex items-center justify-between text-[10px] font-mono pb-2 border-b border-[#E3DFD5]/70 mb-2.5">
                    <span className="uppercase text-[#A9472D] font-bold tracking-wider truncate max-w-[140px]">
                      {item.category || 'HERITAGE SITE'}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[9px] uppercase font-bold ${
                        isReady
                          ? 'bg-[#536B57]/10 text-[#536B57]'
                          : 'bg-[#B99A5B]/15 text-[#8A6F27]'
                      }`}
                    >
                      {isReady ? 'FAISS Ready' : 'Metadata Only'}
                    </span>
                  </div>

                  {/* Title & Location */}
                  <h4 className="font-display font-semibold text-base text-[#171816] leading-snug group-hover:text-[#A9472D] transition-colors">
                    {item.monument_name}
                  </h4>
                  <div className="flex items-center gap-1.5 text-xs text-[#6E7069] font-sans mt-1">
                    <MapPin className="w-3 h-3 text-[#A9472D] flex-shrink-0" />
                    <span className="truncate">{locationStr}</span>
                  </div>

                  {item.architectural_style && (
                    <p className="text-[11px] font-serif text-[#6E7069] mt-2 line-clamp-1 italic">
                      {item.architectural_style}
                    </p>
                  )}
                </div>

                {/* Card Action */}
                <div className="pt-3 mt-3 border-t border-[#E3DFD5]/70 flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-[#6E7069]">
                    {item.anchor_image_count ? `${item.anchor_image_count} Anchors` : 'Catalog Item'}
                  </span>
                  {isReady ? (
                    <button
                      onClick={() => handleTestInScanner(key)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#F5F3ED] hover:bg-[#171816] text-[#171816] hover:text-[#F5F3ED] text-[11px] font-mono uppercase tracking-wider font-semibold transition-colors duration-200 cursor-pointer"
                      title="Load and verify in scanner"
                    >
                      <ScanLine className="w-3 h-3 text-[#B99A5B]" />
                      <span>Test Scan</span>
                    </button>
                  ) : (
                    <span className="text-[10px] font-mono text-[#6E7069]/60 uppercase">Indexed</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Load More Button */}
        {filtered.length > visibleCount && (
          <div className="mt-10 text-center">
            <button
              onClick={() => setVisibleCount((prev) => prev + 12)}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl border border-[#E3DFD5] bg-[#FFFEFA] hover:bg-[#F5F3ED] text-[#171816] text-xs font-mono uppercase tracking-wider font-semibold transition-colors duration-200 cursor-pointer shadow-sm"
            >
              <span>Load More Monuments ({filtered.length - visibleCount} remaining)</span>
              <ChevronDown className="w-3.5 h-3.5 text-[#6E7069]" />
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
