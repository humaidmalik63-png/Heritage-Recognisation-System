import React, { createContext, useContext, useState, useEffect } from 'react';
import { LOCAL_HERITAGE_IMAGES } from '../constants/heritageImages';

const AuthContext = createContext(null);

const HISTORY_KEY = 'heritage_scan_history';
const CURRENT_USER_KEY = 'heritage_current_user';
const USERS_KEY = 'heritage_users';
const HISTORY_LIMIT = 50;

// Initial archival demo scans for user history visualization
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
    thumbnail: '/assets/heritage/charminar.jpg', // FIX 2: Correct Charminar photo
    coordinates: { lat: 17.3616, lng: 78.4747 },
    historical_summary: 'Charminar is a monumental mosque and landmark situated in the heart of Hyderabad, built in 1591 by Muhammad Quli Qutb Shah.',
    structural_features_detected: ['Four 56-meter-tall fluted minarets', 'Four colossal grand pointed arches', 'Stucco ornamentation'],
  },
];

async function hashPassword(plainText) {
  try {
    const enc = new TextEncoder().encode(plainText);
    const buf = await window.crypto.subtle.digest('SHA-256', enc);
    return Array.from(new Uint8Array(buf))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');
  } catch {
    return btoa(plainText);
  }
}

function loadStoredHistory() {
  const entries = [];
  const seen = new Set();

  const collect = (raw) => {
    try {
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        for (const entry of parsed) {
          if (entry && entry.id && !seen.has(entry.id)) {
            // FIX 2: Fix legacy mapping where Charminar had Qutub Minar photo
            if (entry.monument_key === 'charminar' && String(entry.thumbnail || '').includes('qutub-minar')) {
              entry.thumbnail = '/assets/heritage/charminar.jpg';
            }
            seen.add(entry.id);
            entries.push(entry);
          }
        }
      }
    } catch {
      // Ignore unparseable stored values
    }
  };

  collect(localStorage.getItem(HISTORY_KEY));

  // Also collect from legacy per-user keys if present
  for (let i = 0; i < localStorage.length; i += 1) {
    const key = localStorage.key(i);
    if (key && key.startsWith('heritage_history_')) {
      collect(localStorage.getItem(key));
    }
  }

  if (entries.length === 0) {
    return INITIAL_DEMO_SCANS;
  }

  entries.sort((a, b) => String(b.timestamp || '').localeCompare(String(a.timestamp || '')));
  return entries.slice(0, HISTORY_LIMIT);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session and scan history from localStorage
  useEffect(() => {
    try {
      const storedUser = localStorage.getItem(CURRENT_USER_KEY);
      if (storedUser) {
        setUser(JSON.parse(storedUser));
      }
      setHistory(loadStoredHistory());
    } catch (e) {
      console.error('Failed to parse auth/history state:', e);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const trimmedEmail = email.trim().toLowerCase();
    const storedUsers = JSON.parse(localStorage.getItem(USERS_KEY) || '[]');
    const passwordHash = await hashPassword(password);

    const found = storedUsers.find(
      (u) => u.email.toLowerCase() === trimmedEmail && u.passwordHash === passwordHash
    );

    if (!found) {
      throw new Error('Invalid curatorial credentials. Please check your email and password.');
    }

    const { passwordHash: _, ...userProfile } = found;
    setUser(userProfile);
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userProfile));
    return userProfile;
  };

  const signup = async (name, email, password) => {
    const trimmedEmail = email.trim().toLowerCase();
    const storedUsers = JSON.parse(localStorage.getItem(USERS_KEY) || '[]');

    if (storedUsers.some((u) => u.email.toLowerCase() === trimmedEmail)) {
      throw new Error('An archival account with this official email address already exists.');
    }

    const passwordHash = await hashPassword(password);
    const newUser = {
      id: `usr_${Date.now()}`,
      name: name.trim() || 'Curator',
      email: trimmedEmail,
      title: 'Field Research Associate',
      role: 'Curatorial Registry Associate',
      badgeNumber: `ASI-REG-${Math.floor(1000 + Math.random() * 9000)}`,
      department: 'Field Survey & Heritage Digital Register',
      passwordHash,
    };

    storedUsers.push(newUser);
    localStorage.setItem(USERS_KEY, JSON.stringify(storedUsers));

    const { passwordHash: _, ...userProfile } = newUser;
    setUser(userProfile);
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(userProfile));
    return userProfile;
  };

  // FIX 4: Logout clears user session completely so header reflects signed-out state,
  // but NEVER deletes survey log entries — history remains intact!
  const logout = () => {
    setUser(null);
    localStorage.removeItem(CURRENT_USER_KEY);
  };

  // FIX 3: Persistent specimen photo for each scan entry
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
    localStorage.removeItem(HISTORY_KEY);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        history,
        isLoading,
        login,
        signup,
        logout,
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
