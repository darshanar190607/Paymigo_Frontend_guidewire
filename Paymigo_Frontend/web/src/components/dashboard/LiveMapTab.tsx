import React from 'react';
import { Navigation, AlertTriangle, ShieldAlert } from 'lucide-react';
import type { Worker } from '../../types/dashboard';

interface LiveMapTabProps {
  workerData: Worker | null;
}

const LiveMapTab = ({ workerData }: LiveMapTabProps) => {
  const isAdmin = false; // Admin check is handled by the parent via workerData role

  return (
    <div className="space-y-6 animate-in fade-in duration-500 h-[80vh] flex flex-col">
      {/* Status Bar */}
      <div className="flex justify-between items-center bg-black/40 p-4 border border-white/10 rounded-2xl backdrop-blur-md shrink-0">
        <div className="flex items-center gap-3">
          <Navigation className="w-5 h-5 text-accent animate-pulse" />
          <div>
            <h2 className="font-bold">Live Journey Tracking</h2>
            <p className="text-xs text-text-secondary">GPS verified. Anomalies detection: Active.</p>
          </div>
        </div>
        <div className="flex gap-2">
          <div className="px-3 py-1 bg-success/20 text-success text-[10px] font-black uppercase tracking-widest rounded flex items-center gap-2 border border-success/30">
            <span className="w-2 h-2 bg-success rounded-full animate-ping" /> Connection Stable
          </div>
        </div>
      </div>

      <div className="flex-grow grid lg:grid-cols-4 gap-6 min-h-0">
        {/* Map */}
        <div className="lg:col-span-3 glass-card relative overflow-hidden bg-[#111115] border-accent/20 flex flex-col p-1">
          <div className="flex-grow relative rounded-2xl overflow-hidden bg-black">
            <iframe
              src="https://www.openstreetmap.org/export/embed.html?bbox=79.95,12.90,80.35,13.15&layer=mapnik"
              className="absolute inset-0 w-full h-full opacity-80"
              style={{ filter: 'invert(100%) hue-rotate(200deg) brightness(85%) contrast(140%) grayscale(40%)' }}
              title="Live Zone Map"
            />
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10 pointer-events-none" />
            <div className="absolute inset-0 shadow-[inset_0_0_100px_rgba(0,0,0,1)] pointer-events-none" />

            <div className="absolute top-4 right-4 px-4 py-1.5 bg-black/80 border border-accent/50 backdrop-blur-md rounded-full text-[10px] font-black tracking-widest uppercase text-accent flex items-center gap-2 shadow-[0_0_20px_rgba(255,87,34,0.3)]">
              <span className="w-2 h-2 bg-accent rounded-full animate-ping" /> Live Telemetry Active
            </div>

            {/* User location dot */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-accent rounded-full glow-accent flex items-center justify-center shadow-[0_0_30px_#ff5722]">
              <div className="w-16 h-16 border-2 border-accent/40 rounded-full animate-ping absolute" />
              <div className="w-32 h-32 border border-accent/10 rounded-full animate-pulse absolute" />
            </div>
          </div>
        </div>

        {/* Intelligence Panel */}
        <div className="lg:col-span-1 space-y-4 overflow-y-auto pr-2">
          <h3 className="font-bold flex items-center gap-2 mb-4">
            <ShieldAlert className="w-5 h-5 text-warning" /> Intelligence Panel
          </h3>
          <div className="space-y-4">
            <div className="p-4 bg-danger/10 border border-danger/30 rounded-xl relative overflow-hidden">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-danger" />
              <h4 className="font-bold text-sm text-danger mb-1 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> Storm Warning
              </h4>
              <p className="text-[10px] text-text-primary leading-relaxed">Incoming thunderstorm approaching Zone 4. High likelihood of waterlogging.</p>
              <div className="mt-3 text-[10px] font-mono text-danger font-bold bg-black/20 px-2 py-1 rounded inline-block">Risk Multiplier: 2.5x</div>
            </div>

            <div className="p-4 bg-warning/10 border border-warning/30 rounded-xl relative overflow-hidden">
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-warning" />
              <h4 className="font-bold text-sm text-warning mb-1 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> Traffic Anomaly
              </h4>
              <p className="text-[10px] text-text-primary leading-relaxed">Major accident on Ring Road. Congestion detected via sensor fusion.</p>
              <div className="mt-3 text-[10px] font-mono text-warning font-bold bg-black/20 px-2 py-1 rounded inline-block">Impact: High</div>
            </div>

            <div className="p-4 bg-white/5 border border-white/10 rounded-xl">
              <h4 className="font-bold text-sm mb-3">AI Verification Stream</h4>
              <div className="space-y-2">
                {[
                  { label: 'GPS Validity', val: '100% Genuine' },
                  { label: 'Speed Signature', val: 'Verified Vehicle' },
                  { label: 'Anti-Spoofing', val: 'Active Monitoring' },
                ].map((item, i) => (
                  <div key={i} className="flex justify-between items-center text-[10px]">
                    <span className="text-text-secondary">{item.label}</span>
                    <span className="text-success font-bold font-mono">{item.val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMapTab;
