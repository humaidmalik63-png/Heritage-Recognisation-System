import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Compass, ScanLine, ArrowUpRight, CheckCircle2, BookOpen, Layers } from 'lucide-react';

const CURATED_MONUMENTS = [
  {
    key: 'taj_mahal',
    name: 'Taj Mahal',
    indigenousName: 'ताज महल',
    location: 'Agra, Uttar Pradesh, India',
    period: '1632–1653 CE',
    dynasty: 'Mughal Empire',
    style: 'Indo-Islamic Archival Marble',
    image: '/assets/heritage/taj-mahal.jpg',
    color: '#B99A5B',
    summary: 'Commissioned by Mughal Emperor Shah Jahan as an ivory-white marble mausoleum for Mumtaz Mahal, featuring symmetry, calligraphy, and pietra dura inlay.',
    stats: { height: '73 m', status: 'UNESCO World Heritage', coordinates: '27.1751° N, 78.0421° E' },
  },
  {
    key: 'petra',
    name: 'Al-Khazneh, Petra',
    indigenousName: 'الخزنة',
    location: "Ma'an Governorate, Jordan",
    period: '1st Century CE',
    dynasty: 'Nabataean Kingdom',
    style: 'Hellenistic-Nabataean Rock-Cut',
    image: '/assets/heritage/petra.jpg',
    color: '#A9472D',
    summary: 'Carved directly into vibrant rose-red sandstone cliffs, Al-Khazneh (The Treasury) served as an elaborate royal mausoleum in the ancient trading hub.',
    stats: { height: '39.6 m', status: 'UNESCO World Heritage', coordinates: '30.3222° N, 35.4516° E' },
  },
  {
    key: 'colosseum',
    name: 'The Colosseum',
    indigenousName: 'Amphitheatrum Flavium',
    location: 'Rome, Lazio, Italy',
    period: '70–80 CE',
    dynasty: 'Flavian Dynasty',
    style: 'Imperial Roman Concrete & Travertine',
    image: '/assets/heritage/colosseum.jpg',
    color: '#6E7069',
    summary: 'The largest amphitheatre built in antiquity, utilizing elliptical tiered travertine seating and an intricate subterranean hypogeum network.',
    stats: { capacity: '50,000–80,000', status: 'UNESCO World Heritage', coordinates: '41.8902° N, 12.4922° E' },
  },
  {
    key: 'angkor_wat',
    name: 'Angkor Wat',
    indigenousName: 'អង្គរវត្ត',
    location: 'Siem Reap, Cambodia',
    period: '12th Century CE',
    dynasty: 'Khmer Empire',
    style: 'Classic Khmer Quincunx Towers',
    image: '/assets/heritage/angkor-wat.jpg',
    color: '#536B57',
    summary: 'Built by King Suryavarman II as the state temple and royal mausoleum, oriented westward toward Vishnu with 1,200 m² of bas-relief carvings.',
    stats: { area: '162.6 ha', status: 'UNESCO World Heritage', coordinates: '13.4125° N, 103.8670° E' },
  },
  {
    key: 'great_wall_of_china',
    name: 'Great Wall of China',
    indigenousName: '万里长城',
    location: 'Beijing & Northern Provinces, China',
    period: '7th c. BCE – 17th c. CE',
    dynasty: 'Ming Dynasty (Current sections)',
    style: 'Rammed Earth & Masonry Fortification',
    image: '/assets/heritage/great-wall.jpg',
    color: '#8A5D3B',
    summary: 'A 21,196 km frontier fortification system featuring watchtowers, garrison fortresses, and beacon towers engineered over two millennia.',
    stats: { totalLength: '21,196 km', status: 'UNESCO World Heritage', coordinates: '40.4319° N, 116.5704° E' },
  },
  {
    key: 'qutub_minar',
    name: 'Qutub Minar',
    indigenousName: 'क़ुतुब मीनार',
    location: 'Mehrauli, New Delhi, India',
    period: '1199–1220 CE',
    dynasty: 'Delhi Sultanate (Mamluk)',
    style: 'Indo-Islamic Fluted Red Sandstone',
    image: '/assets/heritage/qutub-minar.jpg',
    color: '#A9472D',
    summary: 'A 72.5-meter tapering victory minaret composed of alternating fluted red sandstone balconies and Arabic epigraphical friezes.',
    stats: { height: '72.5 m', status: 'UNESCO World Heritage', coordinates: '28.5244° N, 77.1855° E' },
  },
  {
    key: 'hawa_mahal',
    name: 'Hawa Mahal',
    indigenousName: 'हवा महल',
    location: 'Jaipur, Rajasthan, India',
    period: '1799 CE',
    dynasty: 'Kachhwaha Rajput Dynasty',
    style: 'Rajput & Mughal Screen Architecture',
    image: '/assets/heritage/hawa-mahal.jpg',
    color: '#C46D4E',
    summary: 'Known as the Palace of Winds, featuring 953 jharokha honeycomb windows that vent cool mountain air while allowing royal women unobserved street views.',
    stats: { windows: '953 Jharokhas', status: 'ASI State Monument', coordinates: '26.9239° N, 75.8267° E' },
  },
  {
    key: 'machu_picchu',
    name: 'Machu Picchu',
    indigenousName: 'Machu Pikchu',
    location: 'Cusco Region, Peru',
    period: 'c. 1450 CE',
    dynasty: 'Inca Empire (Pachacuti)',
    style: 'Polished Dry-Stone Ashlar Masonry',
    image: '/assets/heritage/machu-picchu.jpg',
    color: '#536B57',
    summary: 'Perched on an 2,430-meter Andean ridge, featuring seismic-resistant mortarless granite stonework, agricultural terraces, and astronomical alignment.',
    stats: { elevation: '2,430 m', status: 'UNESCO World Heritage', coordinates: '13.1631° S, 72.5450° W' },
  },
];

export default function FeaturedHeritage({ onTestSample }) {
  const [activeModal, setActiveModal] = useState(null);

  const handleTestInScanner = (monumentKey) => {
    if (onTestSample) {
      onTestSample(monumentKey);
      const el = document.getElementById('recognition');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  return (
    <section id="discover" className="py-20 lg:py-28 border-t border-[#E3DFD5] bg-[#F5F3ED]/40">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 sm:mb-16 gap-6">
          <div>
            <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[#A9472D] font-bold mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-[#A9472D]"></span>
              <span>CURATORIAL HIGHLIGHTS // GLOBAL REGISTER</span>
            </div>
            <h2 className="font-display font-semibold text-3xl sm:text-4xl lg:text-5xl text-[#171816] tracking-tight leading-[1.08]">
              Recognised Landmarks of Antiquity.
            </h2>
          </div>
          <p className="max-w-md text-sm sm:text-base text-[#6E7069] leading-relaxed font-sans">
            A curated cross-section from our 100-site multi-epoch archive. Each site is fully indexed with 512-dimensional CLIP embeddings and verified against historical ASI and UNESCO charters.
          </p>
        </div>

        {/* 8 Monument Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {CURATED_MONUMENTS.map((monument, idx) => (
            <motion.div
              key={monument.key}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.5, delay: idx * 0.06 }}
              className="group bg-[#FFFEFA] border border-[#E3DFD5] rounded-2xl overflow-hidden flex flex-col justify-between transition-all duration-300 hover:border-[#171816]/30 hover:shadow-lg"
            >
              {/* Photo Header */}
              <div className="relative aspect-[4/3] overflow-hidden bg-[#EAE6DC]">
                <img
                  src={monument.image}
                  alt={monument.name}
                  className="w-full h-full object-cover transition-transform duration-700 ease-out group-hover:scale-105"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

                {/* Badge top-left */}
                <div className="absolute top-3 left-3">
                  <span className="inline-flex items-center gap-1 font-mono text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded bg-[#171816]/75 text-[#F5F3ED] backdrop-blur-sm">
                    {monument.period}
                  </span>
                </div>

                {/* Badge top-right */}
                <div className="absolute top-3 right-3">
                  <span
                    className="w-2.5 h-2.5 rounded-full inline-block shadow-sm"
                    style={{ backgroundColor: monument.color }}
                    title={monument.style}
                  />
                </div>

                {/* Title overlay at photo bottom */}
                <div className="absolute bottom-3 left-3 right-3 text-white">
                  <h3 className="font-display font-semibold text-lg leading-tight drop-shadow-sm">
                    {monument.name}
                  </h3>
                  <div className="flex items-center gap-1.5 text-xs text-white/85 font-sans mt-0.5">
                    <MapPin className="w-3 h-3 text-[#B99A5B] flex-shrink-0" />
                    <span className="truncate">{monument.location}</span>
                  </div>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-mono text-[#6E7069] pb-2 mb-2.5 border-b border-[#E3DFD5]/70">
                    <span className="uppercase tracking-wider font-semibold">{monument.dynasty}</span>
                    <span className="text-[10px] text-[#A9472D] font-bold">512-D VECTOR</span>
                  </div>
                  <p className="font-sans text-xs text-[#6E7069] leading-relaxed line-clamp-3">
                    {monument.summary}
                  </p>
                </div>

                {/* Action Footer */}
                <div className="pt-4 mt-4 border-t border-[#E3DFD5]/70 flex items-center gap-2">
                  <button
                    onClick={() => handleTestInScanner(monument.key)}
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-[#171816] hover:bg-[#A9472D] text-[#F5F3ED] text-xs font-mono uppercase tracking-wider font-semibold transition-colors duration-200 cursor-pointer shadow-sm"
                  >
                    <ScanLine className="w-3.5 h-3.5 text-[#B99A5B]" />
                    <span>Test Scanner</span>
                  </button>

                  <button
                    onClick={() => setActiveModal(monument)}
                    className="p-2 rounded-xl border border-[#E3DFD5] text-[#171816] hover:bg-[#F5F3ED] transition-colors duration-200 cursor-pointer"
                    title="View Architectural Dossier"
                    aria-label={`View dossier for ${monument.name}`}
                  >
                    <ArrowUpRight className="w-4 h-4 text-[#6E7069]" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Monument Dossier Modal */}
      {activeModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-[#FFFEFA] border border-[#E3DFD5] rounded-3xl max-w-xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="relative aspect-[16/9] overflow-hidden">
              <img
                src={activeModal.image}
                alt={activeModal.name}
                className="w-full h-full object-cover"
              />
              <button
                onClick={() => setActiveModal(null)}
                className="absolute top-4 right-4 w-9 h-9 rounded-full bg-black/60 text-white flex items-center justify-center hover:bg-black transition-colors cursor-pointer text-sm font-bold"
              >
                ✕
              </button>
              <div className="absolute bottom-4 left-4 right-4 text-white">
                <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-[#A9472D] font-bold">
                  {activeModal.dynasty}
                </span>
                <h3 className="font-display font-semibold text-2xl mt-1 leading-tight">
                  {activeModal.name}
                </h3>
                <p className="text-xs text-white/80 font-sans mt-0.5">{activeModal.location}</p>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <h4 className="font-mono text-xs uppercase tracking-wider text-[#A9472D] font-bold">
                  ARCHITECTURAL MONOGRAPH & STYLE
                </h4>
                <p className="font-serif text-base text-[#171816] mt-1 font-semibold">
                  {activeModal.style}
                </p>
                <p className="font-sans text-sm text-[#6E7069] leading-relaxed mt-2">
                  {activeModal.summary}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-3 border-t border-[#E3DFD5] text-xs font-mono">
                {Object.entries(activeModal.stats).map(([k, v]) => (
                  <div key={k} className="p-2.5 rounded-xl bg-[#F5F3ED] border border-[#E3DFD5]">
                    <span className="text-[#6E7069] uppercase block text-[10px]">{k}</span>
                    <span className="font-bold text-[#171816] mt-0.5 block">{v}</span>
                  </div>
                ))}
              </div>

              <div className="pt-4 flex items-center justify-end gap-3">
                <button
                  onClick={() => {
                    handleTestInScanner(activeModal.key);
                    setActiveModal(null);
                  }}
                  className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-[#171816] hover:bg-[#A9472D] text-[#F5F3ED] text-xs font-mono uppercase tracking-wider font-semibold transition-colors duration-200 cursor-pointer shadow-md"
                >
                  <ScanLine className="w-4 h-4 text-[#B99A5B]" />
                  <span>Run Live Verification In Scanner</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
