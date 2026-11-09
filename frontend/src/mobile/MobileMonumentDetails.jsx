import React from 'react';
import { X, MapPin, ScanLine, Compass, ShieldCheck, BookOpen, ExternalLink, Calendar, Landmark } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const LOCAL_THUMBNAILS = {
  taj_mahal: '/assets/heritage/taj-mahal.jpg',
  petra: '/assets/heritage/petra.jpg',
  colosseum: '/assets/heritage/colosseum.jpg',
  angkor_wat: '/assets/heritage/angkor-wat.jpg',
  great_wall_of_china: '/assets/heritage/great-wall.jpg',
  qutub_minar: '/assets/heritage/qutub-minar.jpg',
  hawa_mahal: '/assets/heritage/hawa-mahal.jpg',
  machu_picchu: '/assets/heritage/machu-picchu.jpg',
  ajanta_caves: '/assets/heritage/ajanta-caves.jpg',
  ellora_caves: '/assets/heritage/ellora-caves.jpg',
  golden_temple: '/assets/heritage/golden-temple.jpg',
  humayuns_tomb: '/assets/heritage/humayuns-tomb.jpg',
  konark_sun_temple: '/assets/heritage/konark-sun-temple.jpg',
  mysore_palace: '/assets/heritage/mysore-palace.jpg',
  parthenon: '/assets/heritage/parthenon.jpg',
  great_pyramid_of_giza: '/assets/heritage/pyramids-giza.jpg',
  red_fort: '/assets/heritage/red-fort.jpg',
  eiffel_tower: '/assets/heritage/eiffel-tower.jpg',
};

export default function MobileMonumentDetails({ monumentKey, monumentData, onClose, onTestSample }) {
  if (!monumentKey || !monumentData) return null;

  const item = monumentData;
  const thumb = LOCAL_THUMBNAILS[monumentKey] || null;

  const locationStr = typeof item.location === 'object'
    ? `${item.location?.district ? item.location.district + ', ' : ''}${item.location?.state || ''}, ${item.location?.country || ''}`
    : item.location || 'India';

  const coords = item.coordinates || null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 backdrop-blur-xs">
        <motion.div
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ type: 'spring', damping: 28, stiffness: 300 }}
          className="w-full max-h-[92vh] bg-[#F5F3ED] rounded-t-3xl overflow-hidden flex flex-col shadow-2xl border-t border-[#E3DFD5]"
        >
          {/* Header Bar */}
          <div className="relative aspect-16/10 w-full overflow-hidden bg-neutral-900 flex-shrink-0">
            {thumb ? (
              <img
                src={thumb}
                alt={item.monument_name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-[#ECE8DD] p-4 text-center">
                <Landmark className="w-12 h-12 text-[#B99A5B]/50" />
              </div>
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent pointer-events-none" />

            {/* Close Button */}
            <button
              onClick={onClose}
              className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/60 text-white flex items-center justify-center backdrop-blur-md active:scale-90 transition-transform"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Top Badge */}
            <div className="absolute top-3 left-3 flex items-center gap-1.5">
              <span className="px-2 py-0.5 rounded-full bg-white/90 text-[9px] font-mono text-[#171816] font-bold uppercase tracking-wider">
                {item.catalog_id || 'CATALOGUED SITE'}
              </span>
            </div>

            {/* Bottom Title on Image */}
            <div className="absolute bottom-3 left-4 right-4 text-white">
              <h2 className="font-serif text-xl xs:text-2xl font-bold leading-tight drop-shadow-xs">
                {item.monument_name}
              </h2>
              <div className="flex items-center gap-1 text-xs text-white/90 mt-0.5">
                <MapPin className="w-3 h-3 text-[#B99A5B] flex-shrink-0" />
                <span className="truncate">{locationStr}</span>
              </div>
            </div>
          </div>

          {/* Scrollable Dossier Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs font-sans">
            {/* Metadata Badges Grid */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5]">
                <span className="text-[9px] font-mono text-[#6E7069] uppercase block font-semibold">
                  ARCHITECTURAL STYLE
                </span>
                <p className="font-medium text-[#171816] mt-0.5 text-xs">
                  {item.architectural_style || 'Historic Vernacular'}
                </p>
              </div>

              <div className="p-2.5 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5]">
                <span className="text-[9px] font-mono text-[#6E7069] uppercase block font-semibold">
                  HISTORICAL ERA
                </span>
                <p className="font-medium text-[#171816] mt-0.5 text-xs">
                  {item.built_by_or_era || 'Historical Antiquity'}
                </p>
              </div>
            </div>

            {/* Curatorial Monograph */}
            <div className="p-3.5 rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-1.5">
              <div className="flex items-center gap-1.5 text-[10px] font-mono uppercase text-[#A9472D] font-bold">
                <BookOpen className="w-3 h-3" />
                <span>Historical Curatorial Monograph</span>
              </div>
              <p className="text-xs text-[#171816] leading-relaxed font-serif">
                {item.historical_summary || item.verified_description || 'Detailed architectural records indexed in canonical heritage archive.'}
              </p>
            </div>

            {/* Detected Structural Features */}
            {Array.isArray(item.structural_features_detected) && item.structural_features_detected.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[10px] font-mono text-[#6E7069] uppercase font-bold tracking-wider">
                  CANONICAL ARCHITECTURAL MOTIFS
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {item.structural_features_detected.map((feat, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 rounded-lg bg-[#ECE8DD] text-[#171816] text-[10px] font-medium"
                    >
                      {feat}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Geodetic Cartography */}
            {coords && (
              <div className="p-3 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5] flex items-center justify-between text-xs">
                <div>
                  <span className="text-[9px] font-mono text-[#6E7069] uppercase block">
                    GEODETIC COORDINATES
                  </span>
                  <span className="font-mono text-xs font-semibold text-[#171816]">
                    {coords.lat ? `${coords.lat.toFixed(4)}° N, ${coords.lng.toFixed(4)}° E` : 'Geolocated'}
                  </span>
                </div>
                {coords.lat && coords.lng && (
                  <a
                    href={`https://www.openstreetmap.org/?mlat=${coords.lat}&mlon=${coords.lng}&zoom=16`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#F5F3ED] hover:bg-[#171816] text-[#171816] hover:text-white font-mono text-[10px] font-semibold transition-colors"
                  >
                    <span>OSM Map</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            )}

            {/* Preservation & Legal Framework */}
            <div className="p-2.5 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5] flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <div className="text-[11px]">
                <p className="font-semibold text-[#171816]">
                  {item.preservation_status || 'UNESCO / ASI Protected Cultural Heritage'}
                </p>
                <p className="text-[10px] text-[#6E7069]">
                  Protected under AMASR Act 1958 & UNESCO World Heritage Convention.
                </p>
              </div>
            </div>
          </div>

          {/* Action Footer Plate */}
          <div className="p-3 bg-[#FFFEFA] border-t border-[#E3DFD5] flex items-center gap-2 mobile-safe-bottom">
            <button
              onClick={() => {
                onClose();
                if (onTestSample) onTestSample(monumentKey);
              }}
              className="flex-1 py-3 px-4 rounded-xl bg-[#A9472D] hover:bg-[#8F3720] text-white font-mono text-xs uppercase font-bold tracking-wider flex items-center justify-center gap-2 shadow-xs active:scale-98 transition-transform cursor-pointer"
            >
              <ScanLine className="w-4 h-4" />
              <span>Load Into Scanner</span>
            </button>
            <button
              onClick={onClose}
              className="py-3 px-4 rounded-xl border border-[#E3DFD5] bg-[#F5F3ED] text-[#171816] font-mono text-xs uppercase font-semibold active:scale-98"
            >
              Dismiss
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

