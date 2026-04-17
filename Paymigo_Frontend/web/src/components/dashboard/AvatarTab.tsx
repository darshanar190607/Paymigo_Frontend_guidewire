import React, { useState } from 'react';
import { motion } from 'motion/react';
import { User, Trophy } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Worker } from '../../types/dashboard';
import type { User as FirebaseUser } from 'firebase/auth';

interface AvatarTabProps {
  workerData: Worker | null;
  user: FirebaseUser | null;
}

const PREMIUM_AVATARS = [
  { id: 'custom_glb', url: 'https://darshanar190607.github.io/GLB/', thumb: 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=500&q=80', label: 'Darshan GLB', is3D: true },
  { id: 'ghost_rider', url: 'https://sketchfab.com/models/cd743669a6c54e0c97b7b63b4cf2d420/embed?autostart=1&ui_theme=dark&dnt=1&transparent=1', thumb: 'https://media.sketchfab.com/models/cd743669a6c54e0c97b7b63b4cf2d420/thumbnails/6c65bdab291244bb97beccc1f534f3c0/1024x768.jpeg', label: 'Ghost Rider', is3D: true },
  { id: 'cyber', url: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=500&q=80', thumb: 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=500&q=80', label: 'Neon Cyber', is3D: false },
  { id: 'scout', url: 'https://images.unsplash.com/photo-1618336753974-aae8e04506aa?w=500&q=80', thumb: 'https://images.unsplash.com/photo-1618336753974-aae8e04506aa?w=500&q=80', label: 'Recon Scout', is3D: false },
  { id: 'stealth', url: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500&q=80', thumb: 'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=500&q=80', label: 'Night Rider', is3D: false },
  { id: 'merc', url: 'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=500&q=80', thumb: 'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=500&q=80', label: 'Tactical', is3D: false },
  { id: 'pilot', url: 'https://images.unsplash.com/photo-1552820728-8b83bb6b773f?w=500&q=80', thumb: 'https://images.unsplash.com/photo-1552820728-8b83bb6b773f?w=500&q=80', label: 'Mech Pilot', is3D: false },
];

const LEADERBOARD = [
  { rank: 1, name: 'Arjun K.', score: 9850, isMe: false },
  { rank: 2, name: '__YOU__', score: 9240, isMe: true },
  { rank: 3, name: 'Priya M.', score: 8900, isMe: false },
  { rank: 4, name: 'Suresh D.', score: 8430, isMe: false },
  { rank: 5, name: 'Manoj P.', score: 8100, isMe: false },
];

const AvatarTab = ({ workerData, user }: AvatarTabProps) => {
  const [selectedAvatar, setSelectedAvatar] = useState(PREMIUM_AVATARS[0].url);
  const [isConfirmed, setIsConfirmed] = useState(false);

  const currentAvatarInfo = PREMIUM_AVATARS.find(a => a.url === selectedAvatar);
  const displayName = workerData?.name || user?.displayName || 'Worker Identity';

  const leaderboard = LEADERBOARD.map(entry =>
    entry.isMe ? { ...entry, name: workerData?.name || user?.displayName || 'You' } : entry
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="grid lg:grid-cols-3 gap-8">
        {/* Avatar Editor Canvas */}
        <div className="lg:col-span-2 glass-card p-8 flex flex-col items-center justify-center relative overflow-hidden min-h-[600px]">
          <div className="absolute inset-0 bg-gradient-to-t from-background via-accent/5 to-transparent pointer-events-none" />

          {/* Header */}
          <div className="absolute top-8 w-full px-8 flex justify-between items-center z-30 pointer-events-none">
            <div>
              <h2 className="text-2xl font-display font-bold text-accent drop-shadow-lg pointer-events-auto">{displayName}</h2>
              <p className="text-[10px] uppercase tracking-widest text-[#aaabb0] pointer-events-auto">Tactical Command Center</p>
            </div>
            {!isConfirmed ? (
              <button
                onClick={() => setIsConfirmed(true)}
                className="pointer-events-auto px-6 py-2 bg-gradient-to-br from-accent to-[#00d4ec] text-background hover:glow-accent rounded-xl text-sm font-bold transition-all border border-accent/50 shadow-xl relative overflow-hidden group"
              >
                <span className="relative z-10">Confirm Profile</span>
                <div className="absolute inset-0 bg-white/20 -translate-x-full group-hover:translate-x-0 transition-transform duration-500 skew-x-12" />
              </button>
            ) : (
              <button
                onClick={() => setIsConfirmed(false)}
                className="pointer-events-auto px-6 py-2 bg-[#171a1f] hover:bg-[#23262c] text-[#aaabb0] hover:text-white rounded-xl text-xs font-bold transition-all border border-[#46484d] shadow-md"
              >
                Modify Identity
              </button>
            )}
          </div>

          {/* Avatar Display */}
          <div className={cn(
            'relative border-[1px] border-accent/30 rounded-2xl flex flex-col items-center justify-center shadow-[0_0_80px_rgba(0,229,255,0.15)] bg-gradient-to-br from-[#0c1f2e] via-[#050b14] to-[#0a192f] overflow-hidden group transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]',
            isConfirmed ? 'w-80 h-[28rem] mt-6 scale-110 shadow-[0_0_100px_rgba(0,229,255,0.35)] border-accent' : 'w-56 h-72 mb-8 hover:border-accent z-20'
          )}>
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-40 pointer-events-none z-10 mix-blend-overlay" />

            {currentAvatarInfo?.is3D ? (
              <iframe
                src={selectedAvatar}
                frameBorder="0"
                allow="autoplay; fullscreen; xr-spatial-tracking"
                className="w-full h-full relative z-0 pointer-events-auto mix-blend-screen scale-[1.3] mt-4 filter contrast-125 brightness-110"
              />
            ) : (
              <img
                src={selectedAvatar}
                alt="Player Character Blueprint"
                className={cn(
                  'w-full h-full object-cover transition-transform duration-1000 ease-out relative z-0 origin-center filter contrast-125 saturate-150 pointer-events-auto',
                  isConfirmed ? 'scale-100' : 'scale-[1.05] group-hover:scale-[1.1]'
                )}
              />
            )}

            <div className="absolute inset-0 bg-gradient-to-t from-[#050b14] via-transparent to-transparent z-10 opacity-90 pointer-events-none" />

            <div className={cn(
              'absolute left-0 w-full text-center z-20 flex flex-col items-center justify-center transition-all duration-700 pointer-events-none',
              isConfirmed ? 'bottom-8' : 'bottom-4'
            )}>
              <div className={cn('bg-accent rounded-full mb-1 transition-all', isConfirmed ? 'w-24 h-1.5 shadow-[0_0_15px_#00E5FF] mb-3' : 'w-16 h-1 shadow-[0_0_10px_#00E5FF]')} />
              {isConfirmed ? (
                <>
                  <span className="text-lg font-black tracking-widest uppercase text-white drop-shadow-[0_0_10px_rgba(0,229,255,0.8)]">{currentAvatarInfo?.label}</span>
                  <span className="text-[9px] font-mono tracking-[0.4em] uppercase text-accent mt-1">Confirmed Operator</span>
                </>
              ) : (
                <span className="text-[8px] font-mono tracking-[0.3em] uppercase text-accent">Active Loadout</span>
              )}
            </div>
          </div>

          {/* Avatar Selector */}
          {!isConfirmed && (
            <div className="relative z-30 w-full max-w-xl bg-[#111318]/90 border border-[#46484d]/50 backdrop-blur-2xl rounded-2xl p-6 shadow-[0_32px_64px_rgba(0,0,0,0.8)] animate-in slide-in-from-bottom-4 duration-500 fade-in pointer-events-auto">
              <div className="flex justify-between items-center mb-4">
                <span className="text-[10px] font-black uppercase tracking-widest text-[#aaabb0] flex items-center gap-2">
                  <User className="w-3 h-3 text-accent" /> Select Class Architecture
                </span>
              </div>
              <div className="flex gap-4 overflow-x-auto pb-4 pt-2 px-1">
                {PREMIUM_AVATARS.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => setSelectedAvatar(preset.url)}
                    className={cn(
                      'shrink-0 w-24 h-32 rounded-xl transition-all p-1 bg-[#171a1f] relative group overflow-hidden flex flex-col',
                      selectedAvatar === preset.url
                        ? 'border border-accent shadow-[0_0_20px_rgba(0,229,255,0.3)]'
                        : 'border border-[#46484d]/30 hover:border-[#aaabb0]/50'
                    )}
                  >
                    <div className="h-20 w-full rounded-lg overflow-hidden relative">
                      <img src={preset.thumb} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500 filter contrast-125 saturate-150" alt={preset.label} />
                      <div className="absolute inset-0 bg-black/20 group-hover:bg-transparent transition-colors" />
                    </div>
                    <span className={cn(
                      'mt-2 text-[9px] font-bold uppercase tracking-wider text-center w-full block',
                      selectedAvatar === preset.url ? 'text-accent drop-shadow-[0_0_5px_#00e5ff]' : 'text-[#aaabb0] group-hover:text-white'
                    )}>{preset.label}</span>
                    {selectedAvatar === preset.url && <div className="absolute top-0 left-0 w-1 h-full bg-accent animate-pulse" />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {!isConfirmed && (
            <>
              <div className="w-48 h-[3px] bg-[#1d2025] rounded-full overflow-hidden relative mt-8 z-20">
                <motion.div initial={{ width: 0 }} animate={{ width: '85%' }} className="absolute top-0 left-0 h-full bg-accent shadow-[0_0_10px_#00e5ff]" />
              </div>
              <p className="mt-2 text-[10px] font-mono uppercase tracking-[0.2em] text-[#aaabb0] relative z-20">System Integrity: 85%</p>
            </>
          )}
        </div>

        {/* Leaderboard */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-card p-6 h-full flex flex-col relative overflow-hidden">
            <div className="flex items-center gap-3 mb-6">
              <Trophy className="w-6 h-6 text-warning" />
              <h3 className="text-xl font-bold">Zone Leaderboard</h3>
            </div>
            <div className="space-y-4 flex-grow">
              {leaderboard.map(usr => (
                <div key={usr.rank} className={cn(
                  'flex items-center justify-between p-3 rounded-xl border transition-all',
                  usr.isMe ? 'bg-accent/10 border-accent/30' : 'bg-white/5 border-white/5 hover:border-white/10'
                )}>
                  <div className="flex items-center gap-4">
                    <div className={cn(
                      'font-black text-lg',
                      usr.rank === 1 ? 'text-warning' : usr.rank === 2 ? 'text-gray-300' : usr.rank === 3 ? 'text-amber-600' : 'text-text-secondary'
                    )}>#{usr.rank}</div>
                    <div>
                      <div className="font-bold text-sm">{usr.name}</div>
                      <div className="text-[10px] text-text-secondary">Safety Factor: 99%</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-mono font-bold text-accent">{usr.score}</div>
                    <div className="text-[8px] uppercase tracking-widest text-text-secondary">Points</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AvatarTab;
