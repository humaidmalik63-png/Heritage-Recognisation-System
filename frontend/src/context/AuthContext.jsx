import React, { createContext, useContext, useState, useEffect } from 'react';
import { LOCAL_HERITAGE_IMAGES } from '../constants/heritageImages';

const AuthContext = createContext(null);

const HISTORY_KEY = 'heritage_scan_history';
const HISTORY_LIMIT = 50;

// Initial archival demo scans for user history visualization on initial first visit
const INITIAL_DEMO_SCANS = [
  {
    id: 'scan_init_01',
    timestamp: '2026-11-04T18:42:00.000Z',
    monument_name: 'Taj Mahal',
    monument_key: 'taj_mahal',
    catalog_id: 'ASI-ARCH-TAJ-01',
    verification_tier: 'TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX',
    confidence_score: 99.8,
    location: 'Agra, Uttar Pradesh',
    architectural_style: 'Mughal Architecture',
    built_by_or_era: 'Mughal Emperor Shah Jahan (c. 1631–1653)',
    thumbnail: '/assets/heritage/taj-mahal.jpg',
    coordinates: { lat: 27.1751, lng: 78.0421 },
    historical_summary: 'Taj Mahal is an ivory-white marble mausoleum on the right bank of the river Yamuna in Agra, Uttar Pradesh.',
    structural_features_detected: ['Central onion dome', 'Four flanking minarets', 'Iwan arches', 'Pietra dura inlay'],
  },
  {
    id: 'scan_init_02',
    timestamp: '2026-11-04T15:15:00.000Z',
    monument_name: 'Charminar',
    monument_key: 'charminar',
    catalog_id: 'ASI-ARCH-CHA-06',
    verification_tier: 'TIER 1 // LOCAL CLIP + FAISS VECTOR INDEX',
    confidence_score: 99.8,
    location: 'Hyderabad, Telangana',
    architectural_style: 'Indo-Islamic / Qutb Shahi Architecture',
    built_by_or_era: 'Muhammad Quli Qutb Shah (c. 1591)',
    thumbnail: '/assets/heritage/charminar.jpg',
    coordinates: { lat: 17.3616, lng: 78.4747 },
    historical_summary: 'Charminar is a monumental mosque and landmark situated in the heart of Hyderabad, built in 1591 by Muhammad Quli Qutb Shah.',
    structural_features_detected: ['Four 56-meter-tall fluted minarets', 'Four colossal grand pointed arches', 'Stucco ornamentation'],
  },
];

function loadStoredHistory() {
  const stored = localStorage.getItem(HISTORY_KEY);
  if (stored !== null) {
    try {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        // Fix any legacy Charminar thumbnail mapping if present
        for (const entry of parsed) {
          if (entry && entry.monument_key === 'charminar' && String(entry.thumbnail || '').includes('qutub-minar')) {
            entry.thumbnail = '/assets/heritage/charminar.jpg';
          }
        }
        return parsed.slice(0, HISTORY_LIMIT);
      }
    } catch {
      // If parsing fails, fall through to demo scans
    }
  }

  // Only return initial demo scans if HISTORY_KEY was never initialized (new visitor)
  return INITIAL_DEMO_SCANS;
}

export function AuthProvider({ children }) {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize scan history and perform one-time cleanup of legacy localStorage identity keys
  useEffect(() => {
    try {
      // One-time cleanup of legacy identity keys
      localStorage.removeItem('heritage_users');
      localStorage.removeItem('heritage_current_user');
      
      setHistory(loadStoredHistory());
    } catch (e) {
      console.error('Failed to parse history state:', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const addScanToHistory = (scanResult, thumbnailSrc) => {
    const key = scanResult.monument_key;
    const persistentThumbnail =
      scanResult.preview_data_url ||
      (thumbnailSrc && thumbnailSrc.startsWith('data:') ? thumbnailSrc : null) ||
      (key && LOCAL_HERITAGE_IMAGES[key]) ||
      thumbnailSrc ||
      '/assets/heritage/taj-mahal.jpg';

    const newScanEntry = {
      id: `scan_${Date.now()}`,
      timestamp: new Date().toISOString(),
      monument_name: scanResult.monument_name || 'Unidentified Heritage Landmark',
      monument_key: key,
      catalog_id: scanResult.catalog_id || 'ASI-ARCH-NEW-00',
      verification_tier: scanResult.verification_tier,
      confidence_score: scanResult.confidence_score,
      location: scanResult.location || 'Location Recorded',
      architectural_style: scanResult.architectural_style || 'Historic Heritage',
      built_by_or_era: scanResult.built_by_or_era || 'Historical Era',
      thumbnail: persistentThumbnail,
      coordinates: scanResult.coordinates,
      historical_summary: scanResult.historical_summary,
      structural_features_detected: scanResult.structural_features_detected || [],
      pipeline_telemetry: scanResult.pipeline_telemetry,
      uncertainty: scanResult.uncertainty,
      grounded_citations: scanResult.grounded_citations,
      preservation_status: scanResult.preservation_status,
      preview_data_url: scanResult.preview_data_url,
    };

    setHistory((prev) => {
      const updated = [newScanEntry, ...prev.filter((item) => item.id !== newScanEntry.id)].slice(
        0,
        HISTORY_LIMIT
      );
      try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
      } catch (err) {
        console.warn('Storage quota alert, saving without heavy thumbnails:', err);
      }
      return updated;
    });
  };

  const clearHistory = () => {
    setHistory([]);
    // Persist empty array so cleared state survives page reload
    localStorage.setItem(HISTORY_KEY, JSON.stringify([]));
    
    // Also remove any legacy per-user history keys
    try {
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i += 1) {
        const k = localStorage.key(i);
        if (k && k.startsWith('heritage_history_')) {
          keysToRemove.push(k);
        }
      }
      for (const k of keysToRemove) {
        localStorage.removeItem(k);
      }
    } catch {
      // Ignore errors in legacy cleanup
    }
  };

  return (
    <AuthContext.Provider
      value={{
        history,
        isLoading,
        addScanToHistory,
        clearHistory,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
