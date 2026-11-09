import React, { useState } from 'react';
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

const LOCAL_SAMPLE_IMAGES = {
  taj_mahal: '/assets/heritage/taj-mahal.jpg',
  petra: '/assets/heritage/petra.jpg',
  colosseum: '/assets/heritage/colosseum.jpg',
  angkor_wat: '/assets/heritage/angkor-wat.jpg',
  great_wall_of_china: '/assets/heritage/great-wall.jpg',
  qutub_minar: '/assets/heritage/qutub-minar.jpg',
  hawa_mahal: '/assets/heritage/hawa-mahal.jpg',
  machu_picchu: '/assets/heritage/machu-picchu.jpg',
  ajanta_caves: '/assets/heritage/ajanta-caves.jpg',
  ellora_caves: '/assets/heritage/ellora-caves.jpg',
  golden_temple: '/assets/heritage/golden-temple.jpg',
  humayuns_tomb: '/assets/heritage/humayuns-tomb.jpg',
  konark_sun_temple: '/assets/heritage/konark-sun-temple.jpg',
  mysore_palace: '/assets/heritage/mysore-palace.jpg',
  parthenon: '/assets/heritage/parthenon.jpg',
  great_pyramid_of_giza: '/assets/heritage/pyramids-giza.jpg',
  red_fort: '/assets/heritage/red-fort.jpg',
  eiffel_tower: '/assets/heritage/eiffel-tower.jpg',
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export default function MobileApp({
  health,
  monuments = {},
  onOpenCatalog,
  onOpenExceptions,
  pendingExceptionsCount = 0,
}) {
  const { user, history, addScanToHistory } = useAuth();
  const [activeTab, setActiveTab] = useState('discover');

  // Recognition state
  const [isLoading, setIsLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Selected monument for bottom sheet detail dossier
  const [selectedMonumentKey, setSelectedMonumentKey] = useState(null);

  // Handle direct file upload from camera or gallery
  const handleImageSelected = async (file) => {
    if (!file) return;
    setErrorMessage(null);
    setVerificationResult(null);
    setIsLoading(true);

    const previewUrl = URL.createObjectURL(file);
    setImagePreview(previewUrl);

    try {
      const result = await verifyMonumentImage(file);
      setVerificationResult(result);

      if (result && result.is_monument && !result.is_uncertain) {
        addScanToHistory(result, previewUrl);
      }
    } catch (err) {
      console.error('Mobile verification failed:', err);
      setErrorMessage(err.message || 'Recognition scan failed. Please check network connection.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle sample testing from carousel or archive
  const handleTestSample = async (sampleKey) => {
    setActiveTab('recognise');
    setErrorMessage(null);
    setVerificationResult(null);
    setIsLoading(true);

    try {
      // 1. Try local asset first
      let sampleUrl = LOCAL_SAMPLE_IMAGES[sampleKey];
      let res = null;

      if (sampleUrl) {
        try {
          const check = await fetch(sampleUrl);
          if (check.ok) res = check;
        } catch {
          res = null;
        }
      }

      // 2. Try backend static dataset img_1.jpg
      if (!res) {
        sampleUrl = `${API_BASE_URL}/dataset/${sampleKey}/img_1.jpg`;
        try {
          const check = await fetch(sampleUrl);
          if (check.ok) res = check;
        } catch {
          res = null;
        }
      }

      // 3. Fallback to ref_01.jpg
      if (!res) {
        sampleUrl = `${API_BASE_URL}/dataset/${sampleKey}/ref_01.jpg`;
        try {
          const check = await fetch(sampleUrl);
          if (check.ok) res = check;
        } catch {
          res = null;
        }
      }

      if (!res || !res.ok) {
        throw new Error(`Sample photo for "${sampleKey.replace(/_/g, ' ')}" could not be loaded. Please upload a photo directly.`);
      }

      const blob = await res.blob();
      const file = new File([blob], `${sampleKey}_ref.jpg`, { type: 'image/jpeg' });
      const previewUrl = URL.createObjectURL(file);
      setImagePreview(previewUrl);

      const result = await verifyMonumentImage(file);
      setVerificationResult(result);

      if (result && result.is_monument && !result.is_uncertain) {
        addScanToHistory(result, previewUrl);
      }
    } catch (err) {
      console.error('Sample processing failed:', err);
      setErrorMessage(err.message || 'Sample test failed.');
    } finally {
      setIsLoading(false);
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
      monumentsCount={Object.keys(monuments).length}
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
              <span className="px-2.5 py-1 rounded-full bg-[#171816] text-[#FFFEFA] font-mono text-xs font-bold">
                {history?.length || 0} Scans
              </span>
            </div>

            {(!history || history.length === 0) ? (
              <div className="p-8 text-center rounded-2xl bg-[#FFFEFA] border border-[#E3DFD5] space-y-3">
                <BookOpen className="w-10 h-10 text-[#6E7069]/40 mx-auto" />
                <div className="space-y-1">
                  <h3 className="font-serif text-base font-semibold text-[#171816]">
                    No Monograph Scans Recorded
                  </h3>
                  <p className="text-xs text-[#6E7069] leading-relaxed">
                    Deposited specimens and verified monuments will be indexed here with their official ASI catalog stamps and geodetic coordinates.
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
                        src={scan.thumbnail || '/assets/heritage/taj-mahal.jpg'}
                        alt={scan.monument_name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = '/assets/heritage/taj-mahal.jpg';
                        }}
                      />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <span className="font-mono text-[9px] font-bold text-[#A9472D] uppercase">
                          {scan.catalog_id || 'ASI-RECORD'}
                        </span>
                        <span className="font-mono text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700">
                          {scan.confidence_score ? `${scan.confidence_score.toFixed(1)}%` : 'VERIFIED'}
                        </span>
                      </div>

                      <h3 className="font-display font-semibold text-xs text-[#171816] truncate mt-0.5">
                        {scan.monument_name}
                      </h3>

                      <div className="flex items-center gap-1 text-[11px] text-[#6E7069] truncate mt-0.5">
                        <MapPin className="w-2.5 h-2.5 text-[#A9472D] flex-shrink-0" />
                        <span className="truncate">{scan.location}</span>
                      </div>

                      <p className="text-[9px] font-mono text-[#6E7069]/70 mt-1">
                        {new Date(scan.timestamp).toLocaleString()}
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
                <p className="text-[#6E7069] text-[10px]">577 pre-computed monument centroid vectors</p>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-[#ECE8DD] border border-[#E3DFD5] space-y-2 text-xs">
              <span className="font-mono text-[9px] uppercase tracking-wider text-[#A9472D] font-bold">
                CURATORIAL CREDENTIALS
              </span>
              <p className="font-medium text-[#171816]">
                Authenticated User: {user?.name || 'Dr. Eleanor Vance'}
              </p>
              <p className="text-[11px] text-[#6E7069]">
                Role: {user?.role || 'Senior Archaeologist & Curator'} • {user?.badgeNumber || 'ASI-FELLOW-2026-88'}
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

