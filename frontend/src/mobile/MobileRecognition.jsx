import React, { useRef } from 'react';
import { Camera, Image as ImageIcon, RefreshCw, X, AlertCircle, Sparkles, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';

export default function MobileRecognition({
  imagePreview,
  isLoading,
  errorMessage,
  onImageSelected,
  onReset,
  onDismissError,
}) {
  const cameraInputRef = useRef(null);
  const galleryInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageSelected(file);
    }
  };

  return (
    <div className="space-y-4 pb-6">
      {/* Editorial Header */}
      <div className="pt-2 border-b border-[#E3DFD5]/60 pb-3">
        <span className="text-[10px] font-mono text-[#A9472D] uppercase font-bold tracking-wider">
          REAL-TIME 512-D VECTOR SCANNER
        </span>
        <h1 className="font-serif text-2xl font-bold text-[#171816] mt-0.5">
          Recognise a Monument
        </h1>
        <p className="text-xs text-[#6E7069] mt-0.5">
          Deposit a field photograph or survey scan. Matches 512-D visual vectors against 100 indexed cultural landmarks.
        </p>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-900 text-xs flex items-start justify-between gap-2 shadow-2xs">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="font-sans leading-relaxed">{errorMessage}</p>
          </div>
          {onDismissError && (
            <button onClick={onDismissError} className="text-red-600 hover:text-red-800 font-bold p-1">
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      )}

      {/* Upload & Specimen Viewport */}
      {!imagePreview ? (
        <div className="p-6 rounded-2xl bg-[#FFFEFA] border-2 border-dashed border-[#E3DFD5] text-center space-y-4">
          {/* Hidden inputs */}
          <input
            ref={cameraInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={handleFileChange}
          />
          <input
            ref={galleryInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFileChange}
          />

          <div className="w-14 h-14 mx-auto rounded-full bg-[#F5F3ED] border border-[#E3DFD5] flex items-center justify-center text-[#A9472D]">
            <Camera className="w-7 h-7" />
          </div>

          <div className="space-y-1">
            <h3 className="font-serif text-lg font-semibold text-[#171816]">
              Deposit Specimen Photo
            </h3>
            <p className="text-xs text-[#6E7069] max-w-xs mx-auto leading-relaxed">
              Supports live field camera capture, architectural scans, and uncompressed photos up to 15MB.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-2 gap-2.5 pt-2">
            <button
              onClick={() => cameraInputRef.current?.click()}
              className="py-3 px-3 rounded-xl bg-[#A9472D] hover:bg-[#8F3720] text-white font-mono text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-xs active:scale-97 cursor-pointer"
            >
              <Camera className="w-4 h-4" />
              <span>Camera</span>
            </button>

            <button
              onClick={() => galleryInputRef.current?.click()}
              className="py-3 px-3 rounded-xl bg-[#F5F3ED] hover:bg-[#ECE8DD] text-[#171816] border border-[#E3DFD5] font-mono text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-1.5 shadow-2xs active:scale-97 cursor-pointer"
            >
              <ImageIcon className="w-4 h-4 text-[#B99A5B]" />
              <span>Gallery</span>
            </button>
          </div>

          <p className="text-[10px] font-mono text-[#6E7069]/70 pt-1">
            EXIF GPS coordinates parsed automatically for geodetic verification.
          </p>
        </div>
      ) : (
        /* Image Preview Plate */
        <div className="rounded-2xl overflow-hidden bg-[#FFFEFA] border border-[#E3DFD5] shadow-xs space-y-3 p-3">
          <div className="relative aspect-4/3 w-full rounded-xl overflow-hidden bg-black">
            <img
              src={imagePreview}
              alt="Uploaded specimen preview"
              className="w-full h-full object-contain"
            />

            {/* Corner archival ticks */}
            <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-[#B99A5B]" />
            <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-[#B99A5B]" />
            <div className="absolute bottom-2 left-2 w-3 h-2 border-b-2 border-l-2 border-[#B99A5B]" />
            <div className="absolute bottom-2 right-2 w-3 h-2 border-b-2 border-r-2 border-[#B99A5B]" />

            {/* In-Flight Processing Spinner Overlay */}
            {isLoading && (
              <div className="absolute inset-0 bg-black/75 backdrop-blur-xs flex flex-col items-center justify-center text-white p-4 text-center space-y-3">
                <div className="w-10 h-10 border-3 border-white/20 border-t-[#B99A5B] rounded-full animate-spin" />
                <div className="space-y-1">
                  <p className="font-mono text-xs uppercase tracking-wider font-bold text-[#F5F3ED]">
                    Analyzing Vector Embeddings
                  </p>
                  <p className="text-[11px] text-white/70">
                    Extracting 512-D CLIP features & querying 577 centroids...
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Controls while previewing */}
          {!isLoading && (
            <div className="flex items-center justify-between gap-2 pt-1">
              <button
                onClick={() => galleryInputRef.current?.click()}
                className="flex-1 py-2.5 px-3 rounded-xl border border-[#E3DFD5] bg-[#F5F3ED] hover:bg-[#ECE8DD] text-[#171816] font-mono text-[11px] uppercase font-semibold flex items-center justify-center gap-1.5 active:scale-97"
              >
                <RefreshCw className="w-3.5 h-3.5 text-[#B99A5B]" />
                <span>Replace</span>
              </button>

              <button
                onClick={onReset}
                className="py-2.5 px-4 rounded-xl border border-red-200 bg-red-50 hover:bg-red-100 text-red-700 font-mono text-[11px] uppercase font-semibold flex items-center justify-center gap-1.5 active:scale-97"
              >
                <X className="w-3.5 h-3.5" />
                <span>Clear</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

