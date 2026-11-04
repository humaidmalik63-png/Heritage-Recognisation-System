import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Navigation } from 'lucide-react';

// Custom archival pin icon using Leaflet DivIcon
const archivalIcon = L.divIcon({
  className: 'custom-archival-pin',
  html: `
    <div style="
      background-color: #9E3B24;
      width: 32px;
      height: 32px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      border: 2px solid #FFFFFF;
      box-shadow: 0 4px 10px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      justify-content: center;
    ">
      <div style="
        width: 10px;
        height: 10px;
        background-color: #FDFBF7;
        border-radius: 50%;
        transform: rotate(45deg);
      "></div>
    </div>
  `,
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -30],
});

// Component to dynamically smooth fly to new coordinates
function MapFlyTo({ coords }) {
  const map = useMap();
  useEffect(() => {
    if (coords && coords.lat && coords.lng) {
      map.flyTo([coords.lat, coords.lng], 15, {
        duration: 1.8,
        easeLinearity: 0.25,
      });
    }
  }, [coords, map]);
  return null;
}

export default function MonumentMap({ coordinates, monumentName, catalogId, location }) {
  if (!coordinates || !coordinates.lat || !coordinates.lng) {
    return (
      <div className="bg-archive-alabaster border border-archive-hairline rounded h-72 flex items-center justify-center text-xs font-mono text-archive-muted">
        GEOGRAPHIC COORDINATES NOT AVAILABLE FOR THIS SPECIMEN
      </div>
    );
  }

  const center = [coordinates.lat, coordinates.lng];

  return (
    <div className="bg-archive-ivory border border-archive-hairline rounded overflow-hidden shadow-plate">
      {/* Map Card Header */}
      <div className="px-4 py-2.5 bg-archive-parchment/70 border-b border-archive-hairline flex items-center justify-between font-mono text-xs text-archive-charcoal">
        <div className="flex items-center gap-1.5 font-semibold text-archive-terracotta">
          <Navigation className="w-3.5 h-3.5" />
          <span>GEODETIC CARTOGRAPHY // OPENSTREETMAP CARTOGRAPHIC SURVEY</span>
        </div>
        <span className="text-[11px] text-archive-stone">
          {coordinates.lat.toFixed(5)}° N, {coordinates.lng.toFixed(5)}° E
        </span>
      </div>

      {/* Leaflet Map Frame */}
      <div className="h-72 w-full relative z-10">
        <MapContainer
          center={center}
          zoom={15}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={center} icon={archivalIcon}>
            <Popup className="archival-popup">
              <div className="font-sans text-xs p-1">
                <div className="font-mono text-[9px] uppercase tracking-wider text-archive-terracotta font-bold">
                  {catalogId || 'HERITAGE SITE'}
                </div>
                <div className="font-serif font-bold text-base text-archive-charcoal mt-0.5">
                  {monumentName}
                </div>
                <div className="text-[11px] text-archive-stone mt-0.5">
                  {location}
                </div>
              </div>
            </Popup>
          </Marker>
          <MapFlyTo coords={coordinates} />
        </MapContainer>
      </div>
    </div>
  );
}

