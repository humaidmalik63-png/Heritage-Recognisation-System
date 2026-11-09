import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, Camera, Image as ImageIcon, BookOpen } from 'lucide-react';

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
      alert('Please deposit a valid photographic image (JPEG, PNG, or WebP).');
      return;
    }
    onFileSelected(file);
  };

  const sampleButtons = [
    { key: 'taj_mahal', label: 'Taj Mahal (Mughal)' },
    { key: 'charminar', label: 'Charminar (Qutb Shahi)' },
    { key: 'hampi_stone_chariot', label: 'Hampi Chariot (Vijayanagara)' },
    { key: 'brihadeeswarar_temple', label: 'Brihadeeswarar (Chola)' },
    { key: 'non_monument', label: 'Non-Architectural Specimen (Rejection Test)', isReject: true },
  ];

  return (
    <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-6 sm:p-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-archive-hairline gap-3">
        <div>
          <span className="font-mono text-[10px] uppercase text-archive-terracotta tracking-stamp font-bold block">
            ACCESSION INGESTION // SPECIMEN PLATE
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

      {/* Main Drag-and-Drop Area as Architectural Mounting Plate */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`mt-6 relative border border-dashed rounded p-8 sm:p-12 text-center transition-all cursor-pointer flex flex-col items-center justify-center group ${
          isDragActive
            ? 'border-archive-terracotta bg-archive-terracottaLight/50'
            : 'border-archive-hairline hover:border-archive-borderDark bg-archive-alabaster/30 hover:bg-archive-alabaster/60'
        }`}
      >
        {/* Subtle Architectural Corner Ticks */}
        <div className="absolute top-2 left-2 w-2 h-2 border-t border-l border-archive-hairline"></div>
        <div className="absolute top-2 right-2 w-2 h-2 border-t border-r border-archive-hairline"></div>
        <div className="absolute bottom-2 left-2 w-2 h-2 border-b border-l border-archive-hairline"></div>
        <div className="absolute bottom-2 right-2 w-2 h-2 border-b border-r border-archive-hairline"></div>

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

        <div className="w-12 h-12 rounded border border-archive-hairline bg-white flex items-center justify-center text-archive-terracotta mb-3 shadow-xs">
          <Upload className="w-5 h-5" />
        </div>

        <h3 className="font-serif text-xl sm:text-2xl font-bold text-archive-charcoal">
          Deposit specimen photograph or survey scan
        </h3>
        <p className="text-xs text-archive-stone mt-1.5 max-w-lg font-sans leading-relaxed">
          Supports field camera captures, archival reproductions, and uncompressed scans. EXIF GPS coordinates will be parsed automatically for geodetic verification.
        </p>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 mt-5" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="px-3.5 py-1.5 bg-archive-charcoal hover:bg-black text-white text-xs font-mono uppercase tracking-wider rounded transition-colors flex items-center gap-2 shadow-xs"
          >
            <ImageIcon className="w-3.5 h-3.5 text-archive-parchment" />
            <span>Select Local Image</span>
          </button>

          <button
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            disabled={isLoading}
            className="px-3.5 py-1.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline text-xs font-mono uppercase tracking-wider rounded transition-colors flex items-center gap-2 shadow-xs"
          >
            <Camera className="w-3.5 h-3.5 text-archive-terracotta" />
            <span>Field Camera</span>
          </button>
        </div>
      </div>

      {/* Preset Evaluation Samples */}
      <div className="mt-6 pt-5 border-t border-archive-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 font-mono text-archive-stone flex-shrink-0">
          <BookOpen className="w-3.5 h-3.5 text-archive-terracotta" />
          <span className="font-semibold uppercase tracking-wider text-[11px]">Curated Reference Specimens:</span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {sampleButtons.map((btn) => (
            <button
              key={btn.key}
              type="button"
              onClick={() => onSampleSelect(btn.key)}
              disabled={isLoading}
              className={`px-2.5 py-1 rounded font-mono text-[11px] transition-all ${
                btn.isReject
                  ? 'bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200'
                  : 'bg-white hover:bg-archive-parchment text-archive-charcoal border border-archive-hairline hover:border-archive-borderDark'
              }`}
            >
              {btn.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
