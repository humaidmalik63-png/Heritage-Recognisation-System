import React from 'react';
import { Camera, Compass, ArrowRight, ShieldCheck, MapPin, Sparkles, ChevronRight, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../context/AuthContext';

const FEATURED_MONUMENTS = [
  {
    key: 'taj_mahal',
    name: 'Taj Mahal',
    location: 'Agra, India',
    style: 'Mughal Architecture',
    image: '/assets/heritage/taj-mahal.jpg',
    era: '1631–1653 CE',
  },
  {
    key: 'petra',
    name: 'Petra (Al-Khazneh)',
    location: 'Ma\'an, Jordan',
    style: 'Nabataean Rock-Cut',
    image: '/assets/heritage/petra.jpg',
    era: '1st Century BCE',
  },
  {
    key: 'ajanta_caves',
    name: 'Ajanta Caves',
    location: 'Maharashtra, India',
    style: 'Rock-cut Buddhist',
    image: '/assets/heritage/ajanta-caves.jpg',
    era: '2nd c. BCE – 5th c. CE',
  },
  {
    key: 'colosseum',
    name: 'Colosseum',
    location: 'Rome, Italy',
    style: 'Classical Roman',
    image: '/assets/heritage/colosseum.jpg',
    era: '70–80 CE',
  },
  {
    key: 'angkor_wat',
    name: 'Angkor Wat',
    location: 'Siem Reap, Cambodia',
    style: 'Khmer Architecture',
    image: '/assets/heritage/angkor-wat.jpg',
    era: '12th Century CE',
  },
  {
    key: 'qutub_minar',
    name: 'Qutub Minar',
    location: 'New Delhi, India',
    style: 'Indo-Islamic Afghan',
    image: '/assets/heritage/qutub-minar.jpg',
    era: '1192–1220 CE',
  },
  {
    key: 'machu_picchu',
    name: 'Machu Picchu',
    location: 'Cusco, Peru',
    style: 'Inca Dry-Stone',
    image: '/assets/heritage/machu-picchu.jpg',
    era: '1450 CE',
  },
  {
    key: 'hawa_mahal',
    name: 'Hawa Mahal',
    location: 'Jaipur, India',
    style: 'Rajput & Mughal',
    image: '/assets/heritage/hawa-mahal.jpg',
    era: '1799 CE',
  },
];

export default function MobileDiscover({ onSelectTab, onTestSample, onSelectMonument }) {
  const { history } = useAuth();
  const recentScans = Array.isArray(history) ? history.slice(0, 5) : [];

  return (
    <div className="space-y-6 pb-6">
      {/* Editorial Eyebrow */}
      <div className="pt-2 flex items-center justify-between text-[10px] font-mono tracking-wider text-[#6E7069] border-b border-[#E3DFD5]/60 pb-2">
        <span className="uppercase text-[#A9472D] font-bold">● ARCHIVAL ACCESSION PORTAL</span>
        <span>SERIES 2026</span>
      </div>

      {/* Hero Heading & Narrative */}
      <div className="space-y-2">
        <h1 className="font-serif text-3xl xs:text-4xl leading-[1.08] tracking-tight text-[#171816]">
          Every place <br />
          <span className="italic font-normal text-[#A9472D]">holds a story.</span>
        </h1>
        <p className="font-sans text-xs xs:text-sm text-[#6E7069] leading-relaxed max-w-sm">
          Discover the world&apos;s cultural heritage through visual recognition, grounded historical knowledge and intelligent cultural exploration across 100 canonical monuments.
        </p>
      </div>

      {/* Dominant 4:3 Heritage Architectural Sanctuary Image */}
      <div className="relative rounded-2xl overflow-hidden border border-[#E3DFD5] shadow-xs bg-[#FFFEFA]">
        <div className="aspect-4/3 w-full relative">
          <img
            src="/assets/heritage/taj-mahal.jpg"
            alt="Taj Mahal sanctuary view"
            className="w-full h-full object-cover filter contrast-[1.03]"
            loading="eager"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />

          {/* Archival metadata overlay plate */}
          <div className="absolute top-3 left-3 flex items-center gap-1.5">
            <span className="px-2 py-0.5 rounded-full bg-white/90 backdrop-blur-md text-[9px] font-mono text-[#171816] font-semibold uppercase tracking-wider border border-white/60">
              SPECIMEN 01 // TAJ MAHAL
            </span>
          </div>

          <div className="absolute bottom-3 left-3 right-3 text-white">
            <div className="flex items-center gap-1 text-[11px] font-mono text-white/80">
              <MapPin className="w-3 h-3 text-[#B99A5B]" />
              <span>Agra, Uttar Pradesh, India</span>
            </div>
            <p className="font-serif text-sm font-medium mt-0.5 drop-shadow-xs">
              Mughal Ivory-White Marble Mausoleum (1631–1653 CE)
            </p>
          </div>
        </div>
      </div>

      {/* Dual Touch Actions */}
      <div className="grid grid-cols-2 gap-2.5">
        <button
          onClick={() => onSelectTab('recognise')}
          className="flex items-center justify-center gap-2 py-3 px-3 rounded-xl bg-[#A9472D] hover:bg-[#8F3720] text-white font-mono text-xs font-semibold tracking-wider uppercase shadow-xs transition-transform active:scale-97 cursor-pointer"
        >
          <Camera className="w-4 h-4" />
          <span>Recognise</span>
        </button>

        <button
          onClick={() => onSelectTab('archive')}
          className="flex items-center justify-center gap-2 py-3 px-3 rounded-xl bg-[#FFFEFA] hover:bg-[#F5F3ED] text-[#171816] border border-[#E3DFD5] font-mono text-xs font-semibold tracking-wider uppercase shadow-2xs transition-transform active:scale-97 cursor-pointer"
        >
          <Compass className="w-4 h-4 text-[#B99A5B]" />
          <span>100 Sites</span>
        </button>
      </div>

      {/* Featured Heritage Horizontal Carousel */}
      <section className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-serif text-lg font-semibold text-[#171816]">
              Featured Monuments
            </h2>
            <p className="text-[10px] font-mono text-[#6E7069] uppercase tracking-wider">
              SWIPE TO EXPLORE // CANONICAL ACCESSIONS
            </p>
          </div>
          <button
            onClick={() => onSelectTab('archive')}
            className="flex items-center gap-1 text-xs font-mono text-[#A9472D] font-semibold"
          >
            <span>All 100</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="mobile-scroll-x gap-3 -mx-4 px-4 pb-2">
          {FEATURED_MONUMENTS.map((item) => (
            <div
              key={item.key}
              className="mobile-snap-item w-[220px] rounded-xl overflow-hidden bg-[#FFFEFA] border border-[#E3DFD5] shadow-xs flex flex-col justify-between"
            >
              <div className="relative aspect-16/10 w-full overflow-hidden bg-neutral-100">
                <img
                  src={item.image}
                  alt={item.name}
                  className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                  loading="lazy"
                />
                <span className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-xs text-[8px] font-mono text-white uppercase tracking-wider">
                  {item.era}
                </span>
              </div>

              <div className="p-3 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="font-display font-semibold text-sm text-[#171816] leading-snug line-clamp-1">
                    {item.name}
                  </h3>
                  <div className="flex items-center gap-1 text-[11px] text-[#6E7069] mt-0.5">
                    <MapPin className="w-2.5 h-2.5 text-[#A9472D] flex-shrink-0" />
                    <span className="truncate">{item.location}</span>
                  </div>
                  <p className="text-[10px] font-serif text-[#6E7069] mt-1 line-clamp-1 italic">
                    {item.style}
                  </p>
                </div>

                <div className="mt-3 pt-2 border-t border-[#E3DFD5]/60 flex items-center justify-between">
                  <button
                    onClick={() => onSelectMonument && onSelectMonument(item.key)}
                    className="text-[10px] font-mono text-[#6E7069] hover:text-[#171816] font-medium underline underline-offset-2"
                  >
                    View Dossier
                  </button>
                  <button
                    onClick={() => onTestSample && onTestSample(item.key)}
                    className="px-2 py-1 rounded bg-[#F5F3ED] hover:bg-[#171816] text-[#171816] hover:text-white font-mono text-[9px] uppercase font-bold tracking-wider transition-colors active:scale-95"
                  >
                    Test Scan
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Recently Explored Places (Live Scans from History) */}
      {recentScans.length > 0 && (
        <section className="space-y-3 pt-2">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-serif text-lg font-semibold text-[#171816]">
                Recently Explored
              </h2>
              <p className="text-[10px] font-mono text-[#6E7069] uppercase tracking-wider">
                YOUR CURATORIAL RECOGNITION LOG
              </p>
            </div>
            <button
              onClick={() => onSelectTab('history')}
              className="flex items-center gap-1 text-xs font-mono text-[#A9472D] font-semibold"
            >
              <span>View Log</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-2">
            {recentScans.map((scan) => (
              <div
                key={scan.id}
                onClick={() => onSelectTab('history')}
                className="p-2.5 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5] flex items-center gap-3 cursor-pointer active:scale-98 transition-transform shadow-2xs"
              >
                <div className="w-14 h-14 rounded-lg overflow-hidden bg-neutral-200 flex-shrink-0">
                  <img
                    src={scan.thumbnail || '/assets/heritage/taj-mahal.jpg'}
                    alt={scan.monument_name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = '/assets/heritage/taj-mahal.jpg';
                    }}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1">
                    <h4 className="font-display font-semibold text-xs text-[#171816] truncate">
                      {scan.monument_name}
                    </h4>
                    <span className="font-mono text-[9px] px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 font-bold flex-shrink-0">
                      {scan.confidence_score ? `${scan.confidence_score.toFixed(1)}%` : 'VERIFIED'}
                    </span>
                  </div>
                  <p className="text-[11px] text-[#6E7069] truncate mt-0.5">
                    {scan.location}
                  </p>
                  <div className="flex items-center gap-1 text-[9px] font-mono text-[#6E7069]/80 mt-1">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{new Date(scan.timestamp).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* How It Works (Compact Stepper) */}
      <section className="p-4 rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-3">
        <div className="flex items-center gap-1.5 text-xs font-mono uppercase text-[#A9472D] font-bold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multimodal Pipeline</span>
        </div>
        <h3 className="font-serif text-base font-semibold text-[#171816]">
          How Heritage Recognition Works
        </h3>

        <div className="space-y-3 pt-1">
          <div className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-[#F5F3ED] border border-[#E3DFD5] text-[10px] font-mono font-bold text-[#A9472D] flex items-center justify-center flex-shrink-0">
              1
            </span>
            <div className="text-xs">
              <p className="font-medium text-[#171816]">Deposit Architectural Specimen</p>
              <p className="text-[#6E7069] text-[11px] leading-relaxed">
                Take a field photograph or upload an archival picture from your gallery.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-[#F5F3ED] border border-[#E3DFD5] text-[10px] font-mono font-bold text-[#A9472D] flex items-center justify-center flex-shrink-0">
              2
            </span>
            <div className="text-xs">
              <p className="font-medium text-[#171816]">512-D CLIP & FAISS Matching</p>
              <p className="text-[#6E7069] text-[11px] leading-relaxed">
                Matches visual features against 577 indexed monument centroids in &lt;15ms.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <span className="w-5 h-5 rounded-full bg-[#F5F3ED] border border-[#E3DFD5] text-[10px] font-mono font-bold text-[#A9472D] flex items-center justify-center flex-shrink-0">
              3
            </span>
            <div className="text-xs">
              <p className="font-medium text-[#171816]">Grounded Citations & VLM Tier 2</p>
              <p className="text-[#6E7069] text-[11px] leading-relaxed">
                Resolves complex angles and extracts authentic ASI & UNESCO epigraphical citations.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

