import React, { useState, useRef } from 'react';
import HeritageHero from '../components/HeritageHero';
import FeaturedHeritage from '../components/FeaturedHeritage';
import UploadSection from '../components/UploadSection';
import ProcessingOverlay from '../components/ProcessingOverlay';
import MonographResult from '../components/MonographResult';
import ExploreArchive from '../components/ExploreArchive';
import HowItWorks from '../components/HowItWorks';
import AboutPlatform from '../components/AboutPlatform';
import { verifyMonumentImage } from '../api';
import { useAuth } from '../context/AuthContext';
import { AlertCircle, ScanLine, ArrowDown, Sparkles } from 'lucide-react';
import { LOCAL_HERITAGE_IMAGES } from '../constants/heritageImages';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8001';

export default function Dashboard({
  onExceptionCreated,
  monuments = {},
  readyCount = 101,
  health = null,
  onOpenCatalog = () => {},
  isLoading: propIsLoading,
  setIsLoading: propSetIsLoading,
  imagePreview: propImagePreview,
  setImagePreview: propSetImagePreview,
  verificationResult: propVerificationResult,
  setVerificationResult: propSetVerificationResult,
  errorMessage: propErrorMessage,
  setErrorMessage: propSetErrorMessage,
}) {
  const { addScanToHistory } = useAuth();
  
  // Local fallback if props not provided
  const [localIsLoading, localSetIsLoading] = useState(false);
  const [localImagePreview, localSetImagePreview] = useState(null);
  const [localVerificationResult, localSetVerificationResult] = useState(null);
  const [localErrorMessage, localSetErrorMessage] = useState(null);

  const isLoading = propIsLoading !== undefined ? propIsLoading : localIsLoading;
  const setIsLoading = propSetIsLoading || localSetIsLoading;
  const imagePreview = propImagePreview !== undefined ? propImagePreview : localImagePreview;
  const setImagePreview = propSetImagePreview || localSetImagePreview;
  const verificationResult = propVerificationResult !== undefined ? propVerificationResult : localVerificationResult;
  const setVerificationResult = propSetVerificationResult || localSetVerificationResult;
  const errorMessage = propErrorMessage !== undefined ? propErrorMessage : localErrorMessage;
  const setErrorMessage = propSetErrorMessage || localSetErrorMessage;

  const abortControllerRef = useRef(null);

  const handleCancelScan = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setErrorMessage(null);
  };

  const scrollToRecognition = () => {
    const el = document.getElementById('recognition');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const scrollToDiscover = () => {
    const el = document.getElementById('discover');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleFileSubmission = async (file) => {
    setErrorMessage(null);
    setIsLoading(true);

    abortControllerRef.current = new AbortController();
    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);

    try {
      const result = await verifyMonumentImage(file, abortControllerRef.current.signal);
      setVerificationResult(result);

      // Automatically append verified monument scans to authenticated user's history
      if (result && result.is_monument && !result.is_uncertain) {
        addScanToHistory(result, previewUrl);
      }

      // If an ambiguous specimen was flagged for curator review, update exception count
      if (result?.human_review_flagged && onExceptionCreated) {
        onExceptionCreated();
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('Scan cancelled by user.');
        return;
      }
      console.error('Verification failed:', err);
      setVerificationResult(null);
      setImagePreview(null);
      setErrorMessage(err.message || 'Failed to verify monument. Please check backend connection.');
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleSampleSelect = async (sampleKey) => {
    setErrorMessage(null);
    setIsLoading(true);

    // Scroll to recognition scanner smoothly
    scrollToRecognition();
    abortControllerRef.current = new AbortController();

    try {
      if (sampleKey === 'non_monument') {
        // Generate an in-browser synthetic non-architectural graphic
        const canvas = document.createElement('canvas');
        canvas.width = 400;
        canvas.height = 400;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#E5E7EB';
        ctx.fillRect(0, 0, 400, 400);

        ctx.fillStyle = '#4B5563';
        ctx.fillRect(40, 40, 320, 50);

        ctx.fillStyle = '#9CA3AF';
        ctx.fillRect(40, 110, 260, 25);
        ctx.fillRect(40, 150, 200, 25);
        ctx.fillRect(40, 190, 290, 25);
        ctx.fillRect(40, 240, 150, 40);

        ctx.fillStyle = '#1F2937';
        ctx.font = '16px monospace';
        ctx.fillText('NON-ARCHITECTURAL RECEIPT', 50, 72);

        canvas.toBlob(async (blob) => {
          try {
            if (!blob) throw new Error('Canvas conversion failed');
            const file = new File([blob], 'synthetic_sample.jpg', { type: 'image/jpeg' });
            const previewUrl = URL.createObjectURL(file);
            setImagePreview(previewUrl);
            const result = await verifyMonumentImage(file, abortControllerRef.current?.signal);
            setVerificationResult(result);
            if (result?.human_review_flagged && onExceptionCreated) {
              onExceptionCreated();
            }
          } catch (err) {
            if (err.name === 'AbortError') return;
            console.error('Sample processing failed:', err);
            setVerificationResult(null);
            setImagePreview(null);
            setErrorMessage(err.message || 'Sample test failed.');
          } finally {
            setIsLoading(false);
          }
        }, 'image/jpeg');
      } else {
        // 1. Resolve to bundled photo directly from LOCAL_HERITAGE_IMAGES (guaranteed on Vercel CDN)
        const sampleUrl = LOCAL_HERITAGE_IMAGES[sampleKey];
        if (!sampleUrl) {
          throw new Error('Sample photo not available for this monument. Please upload an image directly.');
        }

        const res = await fetch(sampleUrl);
        if (!res.ok) {
          throw new Error('Sample photo not available for this monument. Please upload an image directly.');
        }

        const blob = await res.blob();

        // Defensive guard: verify blob is a real image (>10 KB AND first bytes FF D8 FF for JPEG)
        if (!blob || blob.size < 10240) {
          throw new Error('Sample photo not available for this monument. Please upload an image directly.');
        }

        const headerBuffer = await blob.slice(0, 3).arrayBuffer();
        const headerBytes = new Uint8Array(headerBuffer);
        const isJpeg = headerBytes[0] === 0xff && headerBytes[1] === 0xd8 && headerBytes[2] === 0xff;
        if (!isJpeg) {
          throw new Error('Sample photo not available for this monument. Please upload an image directly.');
        }
        const file = new File([blob], `${sampleKey}_ref.jpg`, { type: 'image/jpeg' });
        const previewUrl = URL.createObjectURL(file);
        setImagePreview(previewUrl);

        const result = await verifyMonumentImage(file, abortControllerRef.current?.signal);
        setVerificationResult(result);

        // Sync to user history
        if (result && result.is_monument && !result.is_uncertain) {
          addScanToHistory(result, previewUrl);
        }

        if (result?.human_review_flagged && onExceptionCreated) {
          onExceptionCreated();
        }

        setIsLoading(false);
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error('Sample processing failed:', err);
      setVerificationResult(null);
      setImagePreview(null);
      setErrorMessage(err.message || 'Sample test failed.');
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setVerificationResult(null);
    setImagePreview(null);
    setErrorMessage(null);
    scrollToRecognition();
  };

  return (
    <div className="w-full">
      {/* 1. Kinetic Architectural Editorial Hero */}
      <HeritageHero
        onRecognizeClick={scrollToRecognition}
        onExploreClick={scrollToDiscover}
        readyCount={readyCount}
      />

      {/* 2. Curated Highlights (#discover) */}
      <FeaturedHeritage onTestSample={handleSampleSelect} />

      {/* 3. Core Recognition Portal (#recognition) */}
      <section id="recognition" className="py-20 lg:py-28 border-t border-[#E3DFD5] bg-[#F5F3ED]/30">
        <div className="max-w-[1360px] mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
            <div>
              <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[#A9472D] font-bold mb-3">
                <ScanLine className="w-3.5 h-3.5 text-[#A9472D]" />
                <span>ACCESSION PORTAL // REAL-TIME VECTOR SCANNER</span>
              </div>
              <h2 className="font-display font-semibold text-3xl sm:text-4xl lg:text-5xl text-[#171816] tracking-tight leading-[1.08]">
                Identify An Architectural Specimen.
              </h2>
            </div>
            <p className="max-w-md text-sm sm:text-base text-[#6E7069] leading-relaxed font-sans">
              Deposit a photograph of any monument, temple, fort, or architectural fragment. Our hybrid pipeline matches 512-D visual vectors against the indexed cultural landmarks.
            </p>
          </div>

          {/* Processing Scanner Overlay with cancel button & Escape listener (A4) */}
          {isLoading && <ProcessingOverlay previewUrl={imagePreview} onCancel={handleCancelScan} />}

          {/* Error Alert Banner */}
          {errorMessage && (
            <div className="mb-6 bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded-2xl flex items-center justify-between text-sm shadow-sm">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
              <button
                onClick={() => setErrorMessage(null)}
                className="text-xs font-mono uppercase underline hover:no-underline cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* View Switcher: Upload Section or Monograph Dossier */}
          {!verificationResult ? (
            <UploadSection
              onFileSelected={handleFileSubmission}
              isLoading={isLoading}
              onSampleSelect={handleSampleSelect}
            />
          ) : (
            <MonographResult
              result={verificationResult}
              imagePreview={imagePreview}
              onReset={handleReset}
            />
          )}
        </div>
      </section>

      {/* 4. Complete Indexed Corpus Explorer (#archive) */}
      <ExploreArchive
        monuments={monuments}
        readyCount={readyCount}
        onTestSample={handleSampleSelect}
        onOpenCatalogDrawer={onOpenCatalog}
      />

      {/* 5. 4-Stage Methodology & Architecture (#how-it-works) */}
      <HowItWorks readyCount={readyCount} />

      {/* 6. Institutional Charter & Live Telemetry (#about) */}
      <AboutPlatform
        health={health}
        monumentsCount={readyCount}
      />
    </div>
  );
}
