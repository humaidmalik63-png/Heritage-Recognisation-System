import React, { useState } from 'react';
import UploadSection from '../components/UploadSection';
import ProcessingOverlay from '../components/ProcessingOverlay';
import MonographResult from '../components/MonographResult';
import { verifyMonumentImage } from '../api';
import { useAuth } from '../context/AuthContext';
import { AlertCircle, Layers } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function Dashboard({ onExceptionCreated }) {
  const { addScanToHistory } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleFileSubmission = async (file) => {
    setErrorMessage(null);
    setIsLoading(true);

    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);

    try {
      const result = await verifyMonumentImage(file);
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
      console.error('Verification failed:', err);
      setErrorMessage(err.message || 'Failed to verify monument. Please check backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSampleSelect = async (sampleKey) => {
    setErrorMessage(null);
    setIsLoading(true);

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
          if (!blob) throw new Error('Canvas conversion failed');
          const file = new File([blob], 'synthetic_sample.jpg', { type: 'image/jpeg' });
          const previewUrl = URL.createObjectURL(file);
          setImagePreview(previewUrl);
          const result = await verifyMonumentImage(file);
          setVerificationResult(result);
          if (result?.human_review_flagged && onExceptionCreated) {
            onExceptionCreated();
          }
          setIsLoading(false);
        }, 'image/jpeg');
      } else {
        // Fetch real reference sample from backend static dataset
        const sampleUrl = `${API_BASE_URL}/dataset/${sampleKey}/img_1.jpg`;
        const res = await fetch(sampleUrl);
        if (!res.ok) throw new Error(`Could not load reference image from ${sampleUrl}`);
        const blob = await res.blob();
        const file = new File([blob], `${sampleKey}_ref.jpg`, { type: 'image/jpeg' });
        const previewUrl = URL.createObjectURL(file);
        setImagePreview(previewUrl);

        const result = await verifyMonumentImage(file);
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
      console.error('Sample processing failed:', err);
      setErrorMessage(err.message || 'Sample test failed.');
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setVerificationResult(null);
    setImagePreview(null);
    setErrorMessage(null);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Processing Scanner Overlay */}
      {isLoading && <ProcessingOverlay previewUrl={imagePreview} />}

      {/* Error Alert Banner */}
      {errorMessage && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 p-4 rounded flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-xs font-mono uppercase underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* View Switcher: Upload Section or Monograph Dossier */}
      {!verificationResult ? (
        <div className="space-y-8">
          <UploadSection
            onFileSelected={handleFileSubmission}
            isLoading={isLoading}
            onSampleSelect={handleSampleSelect}
          />

          {/* Curatorial Architecture Explainer Card */}
          <div className="bg-archive-ivory border border-archive-hairline rounded shadow-plate p-6 sm:p-8">
            <div className="flex items-center gap-2 font-mono text-xs uppercase text-archive-terracotta tracking-stamp font-bold pb-2 border-b border-archive-hairline">
              <Layers className="w-4 h-4 text-archive-terracotta" />
              <span>ARCHIVAL RECOGNITION SPECIFICATION // TWO-TIER HYBRID ARCHITECTURE</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-5 text-sm text-archive-stone font-sans">
              <div className="space-y-2">
                <h4 className="font-serif font-bold text-lg text-archive-charcoal">
                  Tier 1: Local CLIP + FAISS Vector Search
                </h4>
                <p className="leading-relaxed">
                  Visual embeddings (512-D) are extracted with Hugging Face <code className="font-mono text-xs bg-archive-parchment px-1.5 py-0.5 rounded">openai/clip-vit-base-patch32</code> and queried against an L2-normalized 50-anchor <code className="font-mono text-xs bg-archive-parchment px-1.5 py-0.5 rounded">faiss.IndexFlatIP</code> index for near-instant cosine similarity matching.
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="font-serif font-bold text-lg text-archive-charcoal">
                  Tier 2: Gemini 2.5 Flash VLM Fallback
                </h4>
                <p className="leading-relaxed">
                  Photographs depicting unindexed monuments, extreme angles, or ambiguous lighting are automatically routed to multimodal <code className="font-mono text-xs bg-archive-parchment px-1.5 py-0.5 rounded">gemini-2.5-flash</code> with strict Pydantic JSON validation for comprehensive curatorial analysis.
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <MonographResult
          result={verificationResult}
          imagePreview={imagePreview}
          onReset={handleReset}
        />
      )}
    </div>
  );
}
