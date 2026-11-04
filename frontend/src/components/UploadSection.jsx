import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, Camera, Image as ImageIcon, Sparkles, FileText, CheckCircle2 } from 'lucide-react';

export default function UploadSection({ onFileSelected, isLoading, onSampleSelect }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file) => {
    if (!file.type.startsWith('image/')) {
      alert('Please upload a valid image file (JPEG, PNG, or WebP).');
      return;
    }
    onFileSelected(file);
  };

  const sampleButtons = [
    { key: 'taj_mahal', label: 'Taj Mahal' },
    { key: 'charminar', label: 'Charminar' },
    { key: 'hampi_stone_chariot', label: 'Hampi Chariot' },
    { key: 'brihadeeswarar_temple', label: 'Brihadeeswarar' },
    { key: 'non_monument', label: 'Non-Monument (Rejection Test)', isReject: true },
  ];

  return (
    <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-6 sm:p-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-archive-hairline gap-3">
        <div>
          <span className="font-mono text-xs uppercase text-archive-terracotta tracking-stamp font-bold block">
            ENTRY PORTAL // SPECIMEN INGESTION
          </span>
          <h2 className="font-serif text-2xl sm:text-3xl font-bold text-archive-charcoal mt-0.5">
            Deposit Architectural Specimen for Analysis
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] bg-archive-parchment px-2.5 py-1 border border-archive-hairline rounded text-archive-stone uppercase tracking-wider">
            JPEG / PNG / WEBP • UP TO 20MB
          </span>
        </div>
      </div>

      {/* Main Drag-and-Drop Area */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`mt-6 relative border-2 border-dashed rounded p-8 sm:p-14 text-center transition-all cursor-pointer flex flex-col items-center justify-center group ${
          isDragActive
            ? 'border-archive-terracotta bg-archive-terracottaLight/40'
            : 'border-archive-hairline hover:border-archive-borderDark bg-archive-alabaster/40 hover:bg-archive-alabaster'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          disabled={isLoading}
        />

        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          disabled={isLoading}
        />

        <motion.div
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="w-16 h-16 rounded-full bg-white border border-archive-hairline flex items-center justify-center shadow-sm text-archive-terracotta mb-4 transition-transform"
        >
          <UploadCloud className="w-8 h-8" />
        </motion.div>

        <h3 className="font-serif text-2xl font-bold text-archive-charcoal">
          Drag and drop specimen photograph here
        </h3>
        <p className="text-sm text-archive-stone mt-1 max-w-md font-sans">
          Supports field camera captures, high-resolution scans, and travel photos. EXIF GPS coordinates will be extracted automatically for geo-verification.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-6" onClick={(e) => e.stopPropagation()}>
          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.98 }}
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="px-4 py-2 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded shadow-sm transition-colors flex items-center gap-2"
          >
            <ImageIcon className="w-3.5 h-3.5 text-archive-parchment" />
            <span>Browse Local File</span>
          </motion.button>

          <motion.button
            whileHover={{ y: -1 }}
            whileTap={{ scale: 0.98 }}
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            disabled={isLoading}
            className="px-4 py-2 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline text-xs font-mono uppercase tracking-wider rounded shadow-sm transition-colors flex items-center gap-2"
          >
            <Camera className="w-3.5 h-3.5 text-archive-terracotta" />
            <span>Use Mobile Camera</span>
          </motion.button>
        </div>
      </div>

      {/* Preset Evaluation Samples */}
      <div className="mt-6 pt-5 border-t border-archive-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 font-mono text-archive-stone flex-shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-archive-gold" />
          <span className="font-semibold uppercase tracking-wider">Turnkey Evaluation Samples:</span>
        </div>

        <div className="flex flex-wrap gap-2">
          {sampleButtons.map((btn) => (
            <motion.button
              key={btn.key}
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.98 }}
              type="button"
              onClick={() => onSampleSelect(btn.key)}
              disabled={isLoading}
              className={`px-3 py-1 rounded font-mono text-[11px] transition-all shadow-sm ${
                btn.isReject
                  ? 'bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200'
                  : 'bg-white hover:bg-archive-parchment text-archive-charcoal border border-archive-hairline hover:border-archive-terracotta'
              }`}
            >
              {btn.label}
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
}
