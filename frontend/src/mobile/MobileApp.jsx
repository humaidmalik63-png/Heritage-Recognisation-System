import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import MobileLayout from './MobileLayout';
import MobileDiscover from './MobileDiscover';
import MobileArchive from './MobileArchive';
import MobileRecognition from './MobileRecognition';
import MobileResults from './MobileResults';
import MobileMonumentDetails from './MobileMonumentDetails';
import { useAuth } from '../context/AuthContext';
import { verifyMonumentImage } from '../api';
import { BookOpen, ShieldCheck, Cpu, Database, Info, Trash2, MapPin } from 'lucide-react';
import { LOCAL_HERITAGE_IMAGES } from '../constants/heritageImages';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export default function MobileApp({
  health,
  monuments = {},
  readyCount = 101,
  onOpenCatalog,
  onOpenExceptions,
  pendingExceptionsCount = 0,
  isLoading: propIsLoading,
  setIsLoading: propSetIsLoading,
  imagePreview: propImagePreview,
  setImagePreview: propSetImagePreview,
  verificationResult: propVerificationResult,
  setVerificationResult: propSetVerificationResult,
  errorMessage: propErrorMessage,
  setErrorMessage: propSetErrorMessage,
}) {
  const { history, addScanToHistory, clearHistory } = useAuth();
  const [activeTab, setActiveTab] = useState('discover');

  // Local fallback if not passed as lifted props
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

  // Selected monument for bottom sheet detail dossier
  const [selectedMonumentKey, setSelectedMonumentKey] = useState(null);

  const handleCancelScan = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setErrorMessage(null);
  };

  // Handle direct file upload from camera or gallery
  const handleImageSelected = async (file) => {
    if (!file) return;
    setErrorMessage(null);
    setVerificationResult(null);
    setIsLoading(true);

    abortControllerRef.current = new AbortController();
    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);

    try {
      const result = await verifyMonumentImage(file, abortControllerRef.current.signal);
      setVerificationResult(result);

      if (result && result.is_monument && !result.is_uncertain) {
        addScanToHistory(result, previewUrl);
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error('Mobile verification failed:', err);
      setErrorMessage(err.message || 'Recognition scan failed. Please check network connection.');
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  // Handle sample testing from carousel or archive
  const handleTestSample = async (sampleKey) => {
    setActiveTab('recognise');
    setErrorMessage(null);
    setVerificationResult(null);
    setIsLoading(true);

    abortControllerRef.current = new AbortController();

    try {
      // 1. Resolve to bundled photo directly from LOCAL_HERITAGE_IMAGES
      const sampleUrl = LOCAL_HERITAGE_IMAGES[sampleKey];
      if (!sampleUrl) {
        throw new Error('Sample photo not available for this monument. Please upload an image directly.');
      }

      const res = await fetch(sampleUrl);
      if (!res.ok) {
        throw new Error('Sample photo not available for this monument. Please upload an image directly.');
      }

      const blob = await res.blob();
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

      if (result && result.is_monument && !result.is_uncertain) {
        addScanToHistory(result, previewUrl);
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.error('Sample processing failed:', err);
      setErrorMessage(err.message || 'Sample test failed.');
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleResetRecognition = () => {
    setImagePreview(null);
    setVerificationResult(null);
    setErrorMessage(null);
  };

  return (
    <MobileLayout
      health={health}
      onOpenCatalog={onOpenCatalog}
      monumentsCount={readyCount || 101}
      onOpenExceptions={onOpenExceptions}
      pendingExceptionsCount={pendingExceptionsCount}
      activeTab={activeTab}
      onSelectTab={(tab) => {
        setActiveTab(tab);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }}
    >
      <AnimatePresence mode="wait">
        {/* Tab 1: Discover */}
        {activeTab === 'discover' && (
          <motion.div
            key="discover"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <MobileDiscover
              onSelectTab={setActiveTab}
              onTestSample={handleTestSample}
              onSelectMonument={(key) => setSelectedMonumentKey(key)}
              readyCount={readyCount}
            />
          </motion.div>
        )}

        {/* Tab 2: Archive */}
        {activeTab === 'archive' && (
          <motion.div
            key="archive"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <MobileArchive
              monuments={monuments}
              readyCount={readyCount}
              onTestSample={handleTestSample}
              onSelectMonument={(key) => setSelectedMonumentKey(key)}
            />
          </motion.div>
        )}

        {/* Tab 3: Recognise */}
        {activeTab === 'recognise' && (
          <motion.div
            key="recognise"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-4"
          >
            <MobileRecognition
              imagePreview={imagePreview}
              isLoading={isLoading}
              errorMessage={errorMessage}
              onImageSelected={handleImageSelected}
              onReset={handleResetRecognition}
              onCancel={handleCancelScan}
              onDismissError={() => setErrorMessage(null)}
            />

            {/* Results Section */}
            {verificationResult && (
              <MobileResults
                result={verificationResult}
                onNewScan={handleResetRecognition}
              />
            )}
          </motion.div>
        )}

        {/* Tab 4: History / Log */}
        {activeTab === 'history' && (
          <motion.div
            key="history"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-4 pb-6"
          >
            <div className="pt-2 border-b border-[#E3DFD5]/60 pb-3 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono text-[#A9472D] uppercase font-bold tracking-wider">
                  CURATORIAL ACCESSION LOG
                </span>
                <h1 className="font-serif text-2xl font-bold text-[#171816] mt-0.5">
                  Recognition History
                </h1>
              </div>
              <div className="flex items-center gap-2">
                {history?.length > 0 && (
                  <button
                    onClick={() => {
                      if (window.confirm('Clear all scans from your local scan register?')) {
                        clearHistory();
                      }
                    }}
                    className="p-1.5 rounded-lg border border-red-200 bg-red-50 text-red-700 font-mono text-[11px] uppercase flex items-center gap-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Clear</span>
                  </button>
                )}
                <span className="px-2.5 py-1 rounded-full bg-[#171816] text-[#FFFEFA] font-mono text-xs font-bold">
                  {history?.length || 0} Scans
                </span>
              </div>
            </div>

            {(!history || history.length === 0) ? (
              <div className="p-8 text-center rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-3">
                <BookOpen className="w-10 h-10 text-[#6E7069]/40 mx-auto" />
                <div className="space-y-1">
                  <h3 className="font-serif text-base font-semibold text-[#171816]">
                    No Monograph Scans Recorded
                  </h3>
                  <p className="text-xs text-[#6E7069] leading-relaxed">
                    Deposited specimens and verified monuments will be indexed here with their official catalog stamps and geodetic coordinates.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab('recognise')}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#A9472D] text-white font-mono text-xs uppercase font-bold"
                >
                  Deposit First Specimen
                </button>
              </div>
            ) : (
              <div className="space-y-2.5">
                {history.map((scan) => (
                  <div
                    key={scan.id}
                    className="p-3 rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] shadow-xs flex items-center gap-3"
                  >
                    <div className="w-16 h-16 rounded-xl overflow-hidden bg-neutral-200 flex-shrink-0">
                      <img
                        src={
                          scan.thumbnail ||
                          scan.preview_data_url ||
                          (scan.monument_key && LOCAL_HERITAGE_IMAGES[scan.monument_key]) ||
                          '/assets/heritage/taj-mahal.jpg'
                        }
                        alt={scan.monument_name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[9px] uppercase tracking-wider text-[#A9472D] font-bold">
                          {scan.catalog_id || 'CATALOG'}
                        </span>
                        <span className="font-mono text-[9px] text-[#6E7069]">
                          {scan.confidence_score ? `${scan.confidence_score}%` : 'VERIFIED'}
                        </span>
                      </div>
                      <h4 className="font-serif text-sm font-semibold text-[#171816] truncate mt-0.5">
                        {scan.monument_name}
                      </h4>
                      <p className="text-[11px] text-[#6E7069] truncate flex items-center gap-1 mt-0.5">
                        <MapPin className="w-2.5 h-2.5 text-[#B99A5B] flex-shrink-0" />
                        <span>{scan.location || 'Location Recorded'}</span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* Tab 5: About */}
        {activeTab === 'about' && (
          <motion.div
            key="about"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            className="space-y-4 pb-6"
          >
            <div className="pt-2 border-b border-[#E3DFD5]/60 pb-3">
              <span className="text-[10px] font-mono text-[#A9472D] uppercase font-bold tracking-wider">
                INSTITUTIONAL DOSSIER
              </span>
              <h1 className="font-serif text-2xl font-bold text-[#171816] mt-0.5">
                About the Platform
              </h1>
              <p className="text-xs text-[#6E7069] mt-0.5">
                Visual Heritage Recognition and Grounded Cultural Discovery Platform.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-3 text-xs leading-relaxed">
              <h3 className="font-serif text-base font-semibold text-[#171816]">
                Mission & Curatorial Charter
              </h3>
              <p className="text-[#6E7069]">
                HERITAGE is a modern computational archive uniting computer vision with authoritative archaeological records from the Archaeological Survey of India (ASI) and UNESCO World Heritage Centre.
              </p>
              <p className="text-[#6E7069]">
                Every visual match is grounded against physical epigraphical memoirs, legal protections under the AMASR Act 1958, and district gazetteers to completely eliminate AI hallucinations.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-3 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-1">
                <Cpu className="w-4 h-4 text-[#A9472D]" />
                <p className="font-bold text-[#171816] text-[11px]">Two-Tier AI Engine</p>
                <p className="text-[#6E7069] text-[10px]">OpenAI CLIP ViT-B/32 + Gemini 3.1 Flash-Lite VLM</p>
              </div>

              <div className="p-3 rounded-xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-1">
                <Database className="w-4 h-4 text-[#B99A5B]" />
                <p className="font-bold text-[#171816] text-[11px]">FAISS Vector Index</p>
                <p className="text-[#6E7069] text-[10px]">595 pre-computed monument centroid vectors</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[#ECE8DD] border border-[#E3DFD5] space-y-2 text-xs">
              <span className="font-mono text-[9px] uppercase tracking-wider text-[#A9472D] font-bold">
                LOCAL SESSION
              </span>
              <p className="font-medium text-[#171816]">
                No sign-in. Scans stay in this browser only.
              </p>
              <p className="text-[11px] text-[#6E7069]">
                Scan history is stored locally on this device and is not synced or shared.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Selected Monument Details Bottom Sheet */}
      {selectedMonumentKey && monuments[selectedMonumentKey] && (
        <MobileMonumentDetails
          monumentKey={selectedMonumentKey}
          monumentData={monuments[selectedMonumentKey]}
          onClose={() => setSelectedMonumentKey(null)}
          onTestSample={handleTestSample}
        />
      )}
    </MobileLayout>
  );
}
