import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, Camera, Image as ImageIcon, BookOpen, Sparkles } from 'lucide-react';

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
    <div className="bg-[#FFFEFA] border border-[#E3DFD5] rounded-2xl sm:rounded-3xl shadow-sm p-4 sm:p-8">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#E3DFD5] gap-3">
        <div>
          <span className="font-mono text-[10px] uppercase text-[#A9472D] tracking-wider font-bold block">
            ACCESSION INGESTION // SPECIMEN PLATE
          </span>
          <h2 className="font-serif text-2xl sm:text-3xl font-bold text-[#171816] mt-0.5">
            Deposit Architectural Specimen for Analysis
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] bg-[#F5F3ED] px-2.5 py-1 border border-[#E3DFD5] rounded-full text-[#6E7069] uppercase tracking-wider font-semibold">
            JPEG / PNG / WEBP • UP TO 15MB
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
        className={`mt-6 relative border-2 border-dashed rounded-2xl p-6 sm:p-12 text-center transition-all cursor-pointer flex flex-col items-center justify-center group ${
          isDragActive
            ? 'border-[#A9472D] bg-[#A9472D]/5'
            : 'border-[#E3DFD5] hover:border-[#171816]/40 bg-[#F5F3ED]/40 hover:bg-[#F5F3ED]/70'
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

        <div className="w-14 h-14 rounded-2xl border border-[#E3DFD5] bg-white flex items-center justify-center text-[#A9472D] mb-3.5 shadow-sm group-hover:scale-105 transition-transform">
          <Upload className="w-6 h-6 text-[#A9472D]" />
        </div>

        <h3 className="font-serif text-xl sm:text-2xl font-bold text-[#171816]">
          Deposit specimen photograph or survey scan
        </h3>
        <p className="text-xs text-[#6E7069] mt-1.5 max-w-lg font-sans leading-relaxed">
          Supports field camera captures, archival reproductions, and uncompressed photos. EXIF GPS coordinates will be parsed automatically for geodetic verification.
        </p>

        {/* Action Buttons for Mobile & Desktop */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-6 w-full sm:w-auto" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="flex-1 sm:flex-none px-4 py-2.5 bg-[#171816] hover:bg-[#A9472D] text-white text-xs font-mono uppercase tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 shadow-sm active:scale-95 cursor-pointer font-semibold"
          >
            <ImageIcon className="w-4 h-4 text-[#B99A5B]" />
            <span>Select Photo</span>
          </button>

          <button
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            disabled={isLoading}
            className="flex-1 sm:flex-none px-4 py-2.5 bg-white hover:bg-[#F5F3ED] text-[#171816] border border-[#E3DFD5] text-xs font-mono uppercase tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 shadow-xs active:scale-95 cursor-pointer font-semibold"
          >
            <Camera className="w-4 h-4 text-[#A9472D]" />
            <span>Field Camera</span>
          </button>
        </div>
      </div>

      {/* Preset Evaluation Samples */}
      <div className="mt-6 pt-5 border-t border-[#E3DFD5] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 font-mono text-[#6E7069] flex-shrink-0">
          <BookOpen className="w-3.5 h-3.5 text-[#A9472D]" />
          <span className="font-semibold uppercase tracking-wider text-[11px]">Curated Test Specimens:</span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {sampleButtons.map((btn) => (
            <button
              key={btn.key}
              type="button"
              onClick={() => onSampleSelect(btn.key)}
              disabled={isLoading}
              className={`px-3 py-1.5 rounded-lg font-mono text-[11px] transition-all cursor-pointer active:scale-95 ${
                btn.isReject
                  ? 'bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-200'
                  : 'bg-[#F5F3ED] hover:bg-[#E3DFD5] text-[#171816] border border-[#E3DFD5]'
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
