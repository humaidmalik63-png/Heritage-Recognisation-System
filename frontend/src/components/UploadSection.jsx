import React, { useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Camera, Image as ImageIcon, BookOpen, X, RefreshCw, CheckCircle2 } from 'lucide-react';

// Must match the backend's MAX_UPLOAD_BYTES (15 MB) in backend/main.py.
const MAX_UPLOAD_BYTES = 15 * 1024 * 1024;

export default function UploadSection({ onFileSelected, isLoading, onSampleSelect }) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const stopCameraStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraActive(false);
    setCameraError(null);
  };

  useEffect(() => {
    return () => {
      stopCameraStream();
    };
  }, []);

  const startFieldCamera = async () => {
    setCameraError(null);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setCameraError(
        'Camera access is not supported by your browser or environment. Please use Select Photo to upload an image.'
      );
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setIsCameraActive(true);
      setCameraError(null);
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch((playErr) => {
            console.warn('Video stream playback warning:', playErr);
          });
        }
      }, 100);
    } catch (err) {
      console.warn('Direct camera stream failed:', err);
      stopCameraStream();
      let msg = 'Unable to access field camera. Please select a photo from your files instead.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        msg = 'Camera permission was denied. Please allow camera permissions in your browser or select a photo from your files.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        msg = 'No camera hardware detected on this device. Please select a photo from your files instead.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        msg = 'Camera is currently in use by another application. Please select a photo from your files instead.';
      } else if (err.message) {
        msg = `Camera access error: ${err.message}. Please select a photo from your files instead.`;
      }
      setCameraError(msg);
    }
  };

  const capturePhotoFromStream = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], `field_camera_${Date.now()}.jpg`, { type: 'image/jpeg' });
        stopCameraStream();
        handleFile(file);
      }
    }, 'image/jpeg', 0.95);
  };

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
    // Matches the backend's 15 MB server-side limit (413 above this size).
    if (file.size > MAX_UPLOAD_BYTES) {
      alert(
        `This image is ${(file.size / (1024 * 1024)).toFixed(1)} MB, over the 15 MB limit. ` +
          'Please use a smaller or compressed copy.'
      );
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
          onChange={(e) => {
            if (e.target.files?.[0]) {
              handleFile(e.target.files[0]);
              e.target.value = '';
            }
          }}
          disabled={isLoading}
        />

        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => {
            if (e.target.files?.[0]) {
              handleFile(e.target.files[0]);
              e.target.value = '';
            }
          }}
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

        {/* On-screen Camera Message / Fallback banner (Defect 3) */}
        {cameraError && (
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-lg mt-4 p-3.5 rounded-xl bg-amber-50 border border-amber-300 text-amber-950 text-xs flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs"
          >
            <div className="flex items-center gap-2 text-left">
              <Camera className="w-4 h-4 text-amber-700 flex-shrink-0" />
              <span>{cameraError}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                type="button"
                onClick={() => {
                  fileInputRef.current?.click();
                  setCameraError(null);
                }}
                className="px-3 py-1 bg-[#171816] text-white hover:bg-[#A9472D] rounded-lg font-mono text-[11px] uppercase tracking-wider font-semibold cursor-pointer whitespace-nowrap"
              >
                Select Photo Instead
              </button>
              <button
                type="button"
                onClick={() => setCameraError(null)}
                className="p-1 text-amber-800 hover:text-black rounded cursor-pointer"
                title="Dismiss"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons for Mobile & Desktop (FIX 9: Immediate feedback and live camera modal) */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-6 w-full sm:w-auto" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="flex-1 sm:flex-none px-4 py-2.5 bg-[#171816] hover:bg-[#A9472D] text-white text-xs font-mono uppercase tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 shadow-sm active:scale-95 cursor-pointer font-semibold disabled:opacity-50"
          >
            <ImageIcon className="w-4 h-4 text-[#B99A5B]" />
            <span>Select Photo</span>
          </button>

          <button
            type="button"
            onClick={startFieldCamera}
            disabled={isLoading}
            className="flex-1 sm:flex-none px-4 py-2.5 bg-white hover:bg-[#F5F3ED] text-[#171816] border border-[#E3DFD5] text-xs font-mono uppercase tracking-wider rounded-xl transition-all flex items-center justify-center gap-2 shadow-xs active:scale-95 cursor-pointer font-semibold disabled:opacity-50"
          >
            <Camera className="w-4 h-4 text-[#A9472D]" />
            <span>Field Camera</span>
          </button>
        </div>
      </div>

      {/* Live Field Camera Viewfinder Modal */}
      <AnimatePresence>
        {isCameraActive && (
          <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/85 p-4 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative w-full max-w-lg bg-[#171816] border border-white/20 rounded-2xl overflow-hidden shadow-2xl p-4 text-white"
            >
              <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-mono text-xs uppercase tracking-wider text-white font-semibold">
                    Live Optical Viewfinder
                  </span>
                </div>
                <button
                  type="button"
                  onClick={stopCameraStream}
                  className="p-1 rounded-lg text-white/70 hover:text-white hover:bg-white/10 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Viewfinder Frame */}
              <div className="relative aspect-video bg-black rounded-xl overflow-hidden border border-white/10">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-full object-cover"
                />
                {/* Optical Reticles */}
                <div className="absolute inset-4 pointer-events-none border border-white/20 rounded-lg">
                  <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-[#B99A5B]" />
                  <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-[#B99A5B]" />
                  <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-[#B99A5B]" />
                  <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-[#B99A5B]" />
                </div>
              </div>

              {/* Capture Control */}
              <div className="mt-4 flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={stopCameraStream}
                  className="px-4 py-2 text-xs font-mono uppercase text-white/70 hover:text-white rounded-lg border border-white/20 hover:bg-white/10"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={capturePhotoFromStream}
                  className="px-6 py-2.5 bg-[#A9472D] hover:bg-[#8A3720] text-white rounded-full font-mono text-xs uppercase tracking-wider font-semibold shadow-md active:scale-95 flex items-center gap-2"
                >
                  <Camera className="w-4 h-4 text-[#B99A5B]" />
                  <span>Capture Specimen</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

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
