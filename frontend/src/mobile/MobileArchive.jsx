import React, { useState, useMemo } from 'react';
import { Search, MapPin, ScanLine, Filter, X, ChevronDown } from 'lucide-react';
import { LOCAL_HERITAGE_IMAGES } from '../constants/heritageImages';

export default function MobileArchive({ monuments = {}, readyCount = 101, onTestSample, onSelectMonument }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [visibleCount, setVisibleCount] = useState(16);

  const categories = [
    { id: 'all', label: `All ${readyCount || 101} Sites` },
    { id: 'asi', label: 'ASI National' },
    { id: 'unesco', label: 'UNESCO WHC' },
    { id: 'temple', label: 'Temples & Caves' },
    { id: 'fort', label: 'Forts & Palaces' },
    { id: 'global', label: 'Global Landmarks' },
  ];

  const entries = useMemo(() => {
    return Object.entries(monuments || {}).map(([key, item]) => ({
      key,
      ...item,
    }));
  }, [monuments]);

  const filtered = useMemo(() => {
    return entries.filter((item) => {
      // Search match
      const q = searchQuery.toLowerCase().trim();
      const name = (item.monument_name || '').toLowerCase();
      const style = (item.architectural_style || '').toLowerCase();
      const countryStr = (item.country || '').toLowerCase();
      const loc = typeof item.location === 'string'
        ? item.location.toLowerCase()
        : `${item.city_region || ''} ${item.state_province || ''} ${countryStr}`.toLowerCase();

      const matchesSearch = !q || name.includes(q) || style.includes(q) || loc.includes(q) || countryStr.includes(q);

      // Category match (A5)
      let matchesCategory = true;
      if (selectedCategory === 'asi') {
        matchesCategory = item.is_asi_protected === true;
      } else if (selectedCategory === 'unesco') {
        matchesCategory = item.is_unesco_site === true;
      } else if (selectedCategory === 'temple') {
        matchesCategory = /temple|cave|stupa|shrine|basilica/i.test(`${name} ${style}`);
      } else if (selectedCategory === 'fort') {
        matchesCategory = /fort|palace|citadel|castle/i.test(`${name} ${style}`);
      } else if (selectedCategory === 'global') {
        const isIndia = countryStr === 'india';
        matchesCategory = !isIndia;
      }

      return matchesSearch && matchesCategory;
    });
  }, [entries, searchQuery, selectedCategory]);

  const displayed = filtered.slice(0, visibleCount);

  return (
    <div className="space-y-4 pb-6">
      {/* Editorial Header */}
      <div className="pt-2 border-b border-[#E3DFD5]/60 pb-3">
        <span className="text-[10px] font-mono text-[#A9472D] uppercase font-bold tracking-wider">
          CANONICAL ARCHIVAL REGISTER
        </span>
        <h1 className="font-serif text-2xl font-bold text-[#171816] mt-0.5">
          Heritage Catalogue
        </h1>
        <p className="text-xs text-[#6E7069] mt-0.5">
          Indexed landmarks with 512-D visual vectors and grounded historical dossiers.
        </p>
      </div>

      {/* Search Input Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6E7069]" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by monument, state, country..."
          className="w-full pl-9 pr-9 py-2.5 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5] text-xs font-sans text-[#171816] placeholder:text-[#6E7069]/60 focus:outline-none focus:border-[#A9472D] shadow-2xs"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#6E7069] hover:text-[#171816]"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Swipeable Category Chips */}
      <div className="mobile-scroll-x gap-1.5 -mx-4 px-4 pb-1">
        {categories.map((cat) => {
          const isActive = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => {
                setSelectedCategory(cat.id);
                setVisibleCount(16);
              }}
              className={`px-3 py-1.5 rounded-full text-xs font-mono uppercase whitespace-nowrap transition-all flex-shrink-0 cursor-pointer ${
                isActive
                  ? 'bg-[#171816] text-[#FFFEFA] font-bold shadow-xs'
                  : 'bg-[#FFFEFA] text-[#6E7069] border border-[#E3DFD5] hover:text-[#171816]'
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Results Count Strip */}
      <div className="flex items-center justify-between text-[11px] font-mono text-[#6E7069]">
        {searchQuery || selectedCategory !== 'all' ? (
          <span>
            Found <span className="font-bold text-[#A9472D]">{filtered.length}</span> matching sites
          </span>
        ) : (
          <span>
            Showing <span className="font-bold text-[#171816]">{displayed.length}</span> of {filtered.length} monuments
          </span>
        )}
        {(searchQuery || selectedCategory !== 'all') && (
          <button
            onClick={() => {
              setSearchQuery('');
              setSelectedCategory('all');
            }}
            className="text-[#A9472D] underline font-medium"
          >
            Clear filter
          </button>
        )}
      </div>

      {/* 2-Column Compact Grid */}
      {displayed.length === 0 ? (
        <div className="p-8 text-center rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-2">
          <p className="font-serif text-base text-[#171816]">No monuments found</p>
          <p className="text-xs text-[#6E7069]">
            Try searching for another architectural style, location, or reset filters.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-2.5">
          {displayed.map((item) => {
            const thumb = LOCAL_HERITAGE_IMAGES[item.key] || null;
            const locationStr = typeof item.location === 'string' && item.location.trim()
              ? item.location
              : [item.city_region, item.state_province, item.country].filter(Boolean).join(', ') || 'Global Landmark';

            return (
              <div
                key={item.key}
                className="rounded-xl overflow-hidden bg-[#FFFEFA] border border-[#E3DFD5] shadow-xs flex flex-col justify-between"
              >
                {/* Thumbnail Header */}
                <div
                  onClick={() => onSelectMonument && onSelectMonument(item.key)}
                  className="relative aspect-4/3 w-full overflow-hidden bg-neutral-100 cursor-pointer group"
                >
                  {thumb ? (
                    <img
                      src={thumb}
                      alt={item.monument_name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-[#ECE8DD] p-2 text-center">
                      <span className="font-mono text-[9px] uppercase tracking-wider text-[#A9472D] font-bold">
                        {item.catalog_id || 'CATALOG'}
                      </span>
                      <span className="font-serif text-xs text-[#6E7069] line-clamp-1 mt-0.5">
                        {item.architectural_style || 'Heritage Site'}
                      </span>
                    </div>
                  )}
                  {/* Badge: ASI only for ASI protected; UNESCO only for UNESCO inscribed; otherwise true country (A6) */}
                  <span className="absolute top-1.5 left-1.5 px-1.5 py-0.2 rounded bg-black/60 backdrop-blur-xs text-[8px] font-mono text-white uppercase font-bold">
                    {item.is_asi_protected ? 'ASI' : (item.is_unesco_site ? 'UNESCO' : (item.country || 'HERITAGE'))}
                  </span>
                </div>

                {/* Card Content */}
                <div className="p-2.5 flex-1 flex flex-col justify-between">
                  <div onClick={() => onSelectMonument && onSelectMonument(item.key)} className="cursor-pointer">
                    <h3 className="font-display font-semibold text-xs text-[#171816] leading-snug line-clamp-2 hover:text-[#A9472D]">
                      {item.monument_name}
                    </h3>
                    <div className="flex items-center gap-1 text-[10px] text-[#6E7069] mt-1">
                      <MapPin className="w-2.5 h-2.5 text-[#A9472D] flex-shrink-0" />
                      <span className="truncate">{locationStr}</span>
                    </div>
                    {item.architectural_style && (
                      <p className="text-[9px] font-serif text-[#6E7069] mt-0.5 line-clamp-1 italic">
                        {item.architectural_style}
                      </p>
                    )}
                  </div>

                  {/* Card Actions */}
                  <div className="pt-2 mt-2 border-t border-[#E3DFD5]/60 flex items-center justify-between gap-1">
                    <button
                      onClick={() => onSelectMonument && onSelectMonument(item.key)}
                      className="text-[9px] font-mono uppercase text-[#6E7069] hover:text-[#171816] font-semibold"
                    >
                      Dossier
                    </button>
                    <button
                      onClick={() => onTestSample && onTestSample(item.key)}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#F5F3ED] hover:bg-[#171816] text-[#171816] hover:text-white text-[9px] font-mono uppercase font-semibold transition-colors active:scale-95"
                    >
                      <ScanLine className="w-2.5 h-2.5 text-[#B99A5B]" />
                      <span>Test</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Load More Button */}
      {filtered.length > visibleCount && (
        <div className="pt-2 text-center">
          <button
            onClick={() => setVisibleCount((prev) => prev + 16)}
            className="inline-flex items-center gap-1 px-4 py-2 rounded-xl border border-[#E3DFD5] bg-[#FFFEFA] text-xs font-mono text-[#171816] uppercase font-semibold active:scale-98 shadow-2xs"
          >
            <span>Load More ({filtered.length - visibleCount} remaining)</span>
            <ChevronDown className="w-3.5 h-3.5 text-[#6E7069]" />
          </button>
        </div>
      )}
    </div>
  );
}
