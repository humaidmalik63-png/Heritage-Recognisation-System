import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { ScanLine, Compass, ArrowRight, ShieldCheck, Cpu, Database, Sparkles, Layers } from 'lucide-react';

// Heritage photo mosaic tiles configuration
const COLUMN_1 = [
  { type: 'photo', src: '/assets/heritage/taj-mahal.jpg', label: 'Taj Mahal', location: 'Agra, India', aspect: 'tall' },
  { type: 'color', bg: '#A9472D', label: 'Mughal Brick & Terracotta' },
  { type: 'photo', src: '/assets/heritage/colosseum.jpg', label: 'The Colosseum', location: 'Rome, Italy', aspect: 'standard' },
  { type: 'color', bg: '#AAB9A4', label: 'Living Earth Pigment' },
  { type: 'photo', src: '/assets/heritage/red-fort.jpg', label: 'Red Fort', location: 'Delhi, India', aspect: 'standard' },
];

const COLUMN_2 = [
  { type: 'color', bg: '#B99A5B', label: 'Gilded Epigraphical Script' },
  { type: 'photo', src: '/assets/heritage/petra.jpg', label: 'Al-Khazneh, Petra', location: "Ma'an, Jordan", aspect: 'tall' },
  { type: 'color', bg: '#151514', label: 'Basalt & Obsidian Shading' },
  { type: 'photo', src: '/assets/heritage/qutub-minar.jpg', label: 'Qutub Minar', location: 'Delhi, India', aspect: 'standard' },
  { type: 'color', bg: '#A9C8D4', label: 'Celestial Cerulean Mineral' },
];

const COLUMN_3 = [
  { type: 'color', bg: '#A9C8D4', label: 'Sky-well Reflectance' },
  { type: 'photo', src: '/assets/heritage/great-wall.jpg', label: 'Great Wall of China', location: 'Beijing, China', aspect: 'tall' },
  { type: 'color', bg: '#FFFEFA', border: true, label: 'Alabaster Plinth' },
  { type: 'photo', src: '/assets/heritage/angkor-wat.jpg', label: 'Angkor Wat', location: 'Siem Reap, Cambodia', aspect: 'standard' },
  { type: 'photo', src: '/assets/heritage/hawa-mahal.jpg', label: 'Hawa Mahal', location: 'Jaipur, India', aspect: 'standard' },
];

export default function HeritageHero({ onRecognizeClick, onExploreClick }) {
  const shouldReduceMotion = useReducedMotion();

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1,
      },
    },
  };

  const fadeUpVariants = {
    hidden: { y: 22, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.75,
        ease: [0.16, 1, 0.3, 1],
      },
    },
  };

  const renderColumn = (items, direction = 'down', speed = 26) => {
    // Duplicate items to ensure seamless loop
    const duplicated = [...items, ...items];

    return (
      <div className="relative w-full overflow-hidden h-[500px] sm:h-[580px] lg:h-[640px] rounded-[24px]">
        <motion.div
          className="flex flex-col gap-3.5"
          animate={
            shouldReduceMotion
              ? {}
              : {
                  y: direction === 'down' ? [0, -960] : [-960, 0],
                }
          }
          transition={
            shouldReduceMotion
              ? {}
              : {
                  repeat: Infinity,
                  repeatType: 'loop',
                  duration: speed,
                  ease: 'linear',
                }
          }
        >
          {duplicated.map((tile, idx) => (
            <div
              key={idx}
              className={`relative overflow-hidden rounded-[20px] flex-shrink-0 transition-transform duration-300 hover:scale-[1.02] shadow-sm ${
                tile.aspect === 'tall' ? 'h-[240px]' : 'h-[180px]'
              }`}
              style={{
                backgroundColor: tile.type === 'color' ? tile.bg : '#EAE6DC',
                border: tile.border ? '1px solid #E3DFD5' : '1px solid rgba(23, 24, 22, 0.06)',
              }}
            >
              {tile.type === 'photo' ? (
                <>
                  <img
                    src={tile.src}
                    alt={tile.label}
                    className="w-full h-full object-cover object-center"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-black/10 to-transparent" />
                  <div className="absolute bottom-3 left-3.5 right-3.5 text-white">
                    <p className="font-serif text-sm font-semibold leading-tight drop-shadow-sm">
                      {tile.label}
                    </p>
                    <p className="font-sans text-[10px] text-white/80 tracking-wide font-medium mt-0.5">
                      {tile.location}
                    </p>
                  </div>
                </>
              ) : (
                <div className="w-full h-full p-4 flex flex-col justify-between relative overflow-hidden">
                  <div
                    className="absolute inset-0 opacity-15 pointer-events-none"
                    style={{
                      backgroundImage: 'url(/assets/grain.svg)',
                      backgroundSize: 'cover',
                    }}
                  />
                  <span className="w-2 h-2 rounded-full bg-black/20 self-end" />
                  <p
                    className="text-[10px] font-mono tracking-wider uppercase font-semibold relative z-10"
                    style={{
                      color: tile.bg === '#151514' ? '#A9C8D4' : '#171816',
                      opacity: 0.85,
                    }}
                  >
                    {tile.label}
                  </p>
                </div>
              )}
            </div>
          ))}
        </motion.div>
      </div>
    );
  };

  return (
    <section className="relative w-full pt-4 pb-14 sm:pt-8 sm:pb-20 overflow-hidden bg-[#F5F3ED]/40">
      <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-14 items-center">
          
          {/* Left Column: High-End Architectural Editorial Headline & Actions */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="lg:col-span-6 flex flex-col justify-center space-y-6 sm:space-y-8"
          >
            {/* Luminous Classification Badge */}
            <motion.div variants={fadeUpVariants} className="flex items-center gap-2">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#FFFEFA] border border-[#E3DFD5] shadow-sm">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#A9472D] opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#A9472D]" />
                </span>
                <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-[#171816] font-semibold">
                  ASI & UNESCO REGISTER // 100 CANONICAL SITES
                </span>
              </div>
            </motion.div>

            {/* Giant Editorial Heading (Modernist Geometric + Heritage Serif Italic) */}
            <motion.h1
              variants={fadeUpVariants}
              className="text-5xl sm:text-7xl lg:text-[78px] font-bold tracking-tight leading-[0.92] text-[#171816]"
            >
              <span className="block font-display tracking-tight">
                Every place
              </span>
              <span className="block font-serif italic font-semibold text-[#A9472D] tracking-normal mt-1 sm:mt-2">
                holds a story.
              </span>
            </motion.h1>

            {/* Grounded Historical Copy */}
            <motion.p
              variants={fadeUpVariants}
              className="text-base sm:text-lg text-[#6E7069] font-sans leading-relaxed max-w-xl"
            >
              An intelligent two-tier recognition framework pairing 512-dimensional visual embeddings with verified dynasties, UNESCO charters, and grounded architectural monographs across 100 canonical world heritage sites.
            </motion.p>

            {/* Interactive Dual Action Suite */}
            <motion.div
              variants={fadeUpVariants}
              className="flex flex-wrap items-center gap-3.5 sm:gap-4 pt-1"
            >
              {/* Primary CTA: Recognise a Monument */}
              <motion.button
                whileHover={{ y: -2, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onRecognizeClick}
                className="inline-flex items-center gap-2.5 px-6 py-3.5 sm:px-7 sm:py-4 bg-gradient-to-r from-[#A9472D] via-[#B84E34] to-[#993E26] text-white rounded-full text-sm sm:text-base font-sans font-semibold tracking-wide shadow-[0_4px_20px_rgba(169,71,45,0.35),inset_0_1px_1px_rgba(255,255,255,0.25)] transition-all cursor-pointer group whitespace-nowrap"
              >
                <ScanLine className="w-4 h-4 sm:w-5 sm:h-5 text-[#B99A5B] transition-transform group-hover:scale-110" />
                <span>Recognise a Monument</span>
                <ArrowRight className="w-3.5 h-3.5 text-white/80 transition-transform group-hover:translate-x-1" />
              </motion.button>

              {/* Secondary CTA: Explore the Archive */}
              <motion.button
                whileHover={{ y: -2, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={onExploreClick}
                className="inline-flex items-center gap-2 px-6 py-3.5 sm:px-7 sm:py-4 bg-[#FFFEFA] hover:bg-white text-[#171816] border border-[#E3DFD5] hover:border-[#171816]/30 rounded-full text-sm sm:text-base font-sans font-semibold tracking-wide shadow-sm hover:shadow transition-all cursor-pointer group whitespace-nowrap"
              >
                <Compass className="w-4 h-4 sm:w-5 sm:h-5 text-[#B99A5B] transition-transform group-hover:rotate-45 duration-300" />
                <span>Explore the Archive</span>
                <span className="font-mono text-[10px] text-[#A9472D] bg-[#A9472D]/10 px-2 py-0.5 rounded-full font-bold ml-0.5">
                  100 Sites
                </span>
              </motion.button>
            </motion.div>

            {/* Architecture Telemetry Micro-Pills Ribbon */}
            <motion.div
              variants={fadeUpVariants}
              className="pt-4 border-t border-[#E3DFD5] flex flex-wrap items-center gap-2.5 text-xs font-mono"
            >
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#FFFEFA] border border-[#E3DFD5] text-[#171816] shadow-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="font-semibold">OpenAI CLIP ViT-B/32</span>
                <span className="text-[#6E7069]">(512-D)</span>
              </div>

              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#FFFEFA] border border-[#E3DFD5] text-[#171816] shadow-xs">
                <Database className="w-3 h-3 text-[#B99A5B]" />
                <span className="font-semibold">577 FAISS Anchors</span>
              </div>

              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#FFFEFA] border border-[#E3DFD5] text-[#171816] shadow-xs">
                <ShieldCheck className="w-3 h-3 text-[#A9472D]" />
                <span className="font-semibold">Gemini 3.1 Fallback</span>
              </div>
            </motion.div>

            {/* Micro Benchmark Stats Line */}
            <motion.div
              variants={fadeUpVariants}
              className="grid grid-cols-3 gap-3 pt-2 text-[#171816]"
            >
              <div className="p-2.5 rounded-xl bg-[#FFFEFA]/80 border border-[#E3DFD5]/80">
                <span className="font-display font-bold text-lg leading-none block">100</span>
                <span className="font-mono text-[10px] uppercase text-[#6E7069] tracking-wider mt-0.5 block">
                  Canonical Sites
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-[#FFFEFA]/80 border border-[#E3DFD5]/80">
                <span className="font-display font-bold text-lg leading-none block">&lt; 15ms</span>
                <span className="font-mono text-[10px] uppercase text-[#6E7069] tracking-wider mt-0.5 block">
                  Vector Retrieval
                </span>
              </div>

              <div className="p-2.5 rounded-xl bg-[#FFFEFA]/80 border border-[#E3DFD5]/80">
                <span className="font-display font-bold text-lg leading-none text-[#A9472D] block">100%</span>
                <span className="font-mono text-[10px] uppercase text-[#6E7069] tracking-wider mt-0.5 block">
                  Grounded Citations
                </span>
              </div>
            </motion.div>
          </motion.div>

          {/* Right Column: 3-Column Kinetic Heritage Mosaic */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.9, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="lg:col-span-6 relative w-full"
          >
            {/* The 3-Column Mosaic Container */}
            <div className="grid grid-cols-3 gap-3 sm:gap-4 relative w-full overflow-hidden rounded-[28px] p-2 bg-[#FFFEFA]/60 border border-[#E3DFD5] shadow-lg">
              {/* Column 1: Moves Down */}
              <div className="w-full">{renderColumn(COLUMN_1, 'down', 24)}</div>

              {/* Column 2: Moves Up */}
              <div className="w-full">{renderColumn(COLUMN_2, 'up', 26)}</div>

              {/* Column 3: Moves Down */}
              <div className="w-full">{renderColumn(COLUMN_3, 'down', 28)}</div>
            </div>

            {/* Subtle Gradient Fade at Top & Bottom of Mosaic */}
            <div className="absolute top-0 left-0 right-0 h-10 bg-gradient-to-b from-[#F5F3ED] to-transparent pointer-events-none rounded-t-[28px]" />
            <div className="absolute bottom-0 left-0 right-0 h-10 bg-gradient-to-t from-[#F5F3ED] to-transparent pointer-events-none rounded-b-[28px]" />
          </motion.div>
        </div>
      </div>
    </section>
  );
}