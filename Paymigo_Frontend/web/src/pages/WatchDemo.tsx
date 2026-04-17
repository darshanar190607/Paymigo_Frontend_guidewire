import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import { Play, Pause, RotateCcw, Shield, Zap, Wallet, ArrowRight, Loader2, Key } from 'lucide-react';
import { cn } from '@/lib/utils';
import { GoogleGenAI } from '@google/genai';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DemoStep {
  title: string;
  description: string;
  icon: React.ReactNode;
  timestamp: string;
}

// ─── Static data ─────────────────────────────────────────────────────────────

const LOADING_MESSAGES: string[] = [
  'Connecting to hyper-local weather satellites...',
  'Calibrating rainfall sensors in Chennai South-4...',
  'Analyzing historical gig worker payout data...',
  'Simulating real-time threshold trigger (15mm/hr)...',
  'Executing smart contract for instant payout...',
  'Generating cinematic demo visualization...',
  'Almost there! Finalizing the protection stream...',
];

const DEMO_STEPS: DemoStep[] = [
  { title: 'Real-time Monitoring', description: 'Our AI engine monitors weather and AQI data in your specific delivery zone 24/7.', icon: <Zap className="w-6 h-6 text-accent" />, timestamp: '0:05' },
  { title: 'Automatic Trigger',   description: "When conditions hit your plan's threshold (e.g., 15mm rain), the policy activates instantly.", icon: <Shield className="w-6 h-6 text-accent" />, timestamp: '0:12' },
  { title: 'Instant Payout',      description: 'No claims, no paperwork. Funds are pushed to your Paymigo wallet in under 90 seconds.', icon: <Wallet className="w-6 h-6 text-accent" />, timestamp: '0:25' },
];

// ─── Component ────────────────────────────────────────────────────────────────

const WatchDemo: React.FC = () => {
  const navigate = useNavigate();
  const [isPlaying, setIsPlaying]         = useState(false);
  const [currentStep, setCurrentStep]     = useState(0);
  const [showOverlay, setShowOverlay]     = useState(true);
  const [isGenerating, setIsGenerating]   = useState(false);
  const [videoUrl, setVideoUrl]           = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [hasKey, setHasKey]               = useState(true); // API key is auto-accepted
  const videoRef = useRef<HTMLVideoElement>(null);

  const generateDemoVideo = async (): Promise<void> => {
    setIsGenerating(true);
    let messageIndex = 0;
    const iv = setInterval(() => {
      setLoadingMessage(LOADING_MESSAGES[messageIndex % LOADING_MESSAGES.length]);
      messageIndex++;
    }, 3000);

    try {
      // Simulated AI model inference delay — maps to cinematic stock footage
      await new Promise(resolve => setTimeout(resolve, 12000));
      setVideoUrl('https://videos.pexels.com/video-files/3045163/3045163-hd_1920_1080_30fps.mp4');
      setShowOverlay(false);
      setIsPlaying(true);
    } catch (error) {
      console.error('Video generation failed:', error);
    } finally {
      clearInterval(iv);
      setIsGenerating(false);
    }
  };

  const togglePlayback = (): void => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
    } else {
      videoRef.current.pause();
    }
  };

  const restartVideo = (): void => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = 0;
    videoRef.current.play();
  };

  return (
    <div className="min-h-screen bg-background py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-block px-4 py-1.5 bg-accent/10 rounded-full text-accent text-[10px] font-black uppercase tracking-[0.2em] mb-6"
          >
            Interactive Experience
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-7xl font-display font-black mb-6 tracking-tighter"
          >
            See How <span className="gradient-text">Paymigo</span> Works
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-text-secondary text-lg max-w-2xl mx-auto font-medium"
          >
            Experience the future of gig worker protection. Watch our AI-generated demo of a real-world weather event.
          </motion.p>
        </div>

        <div className="grid lg:grid-cols-3 gap-12 items-start">
          {/* Video Player */}
          <div className="lg:col-span-2 space-y-8">
            <div className="relative aspect-video glass-card overflow-hidden border-accent/20 group">
              <div className="absolute inset-0 bg-surface flex items-center justify-center">
                {videoUrl ? (
                  <video
                    ref={videoRef}
                    src={videoUrl}
                    className="w-full h-full object-cover"
                    autoPlay
                    loop
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                  />
                ) : (
                  <div className="text-center space-y-6">
                    <div className="relative">
                      <div className="absolute inset-0 bg-accent blur-3xl opacity-20 animate-pulse" />
                      <Shield className="w-24 h-24 text-accent relative z-10 mx-auto opacity-20" />
                    </div>
                    <p className="text-text-secondary font-mono text-sm tracking-widest uppercase">
                      {isGenerating ? 'Generating Live Demo...' : 'Demo Video Stream'}
                    </p>
                  </div>
                )}
              </div>

              <AnimatePresence>
                {showOverlay && !isGenerating && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-20 p-8 text-center"
                  >
                    {!hasKey ? (
                      <div className="space-y-6 max-w-md">
                        <div className="w-20 h-20 bg-accent/20 rounded-full flex items-center justify-center mx-auto mb-4">
                          <Key className="w-10 h-10 text-accent" />
                        </div>
                        <h3 className="text-2xl font-bold text-white tracking-tight">AI Demo Access</h3>
                        <p className="text-white/60 text-sm leading-relaxed">
                          To generate your personalized AI demo video, please connect your AI Studio API key.
                        </p>
                        <button
                          onClick={() => setHasKey(true)}
                          className="px-8 py-4 bg-accent text-white rounded-2xl font-bold hover:glow-accent transition-all flex items-center justify-center gap-3 mx-auto"
                        >
                          Connect API Key <ArrowRight className="w-5 h-5" />
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-6">
                        <button
                          onClick={generateDemoVideo}
                          className="w-24 h-24 bg-accent text-white rounded-full flex items-center justify-center hover:scale-110 transition-transform shadow-2xl shadow-accent/40 group/btn"
                        >
                          <Play className="w-10 h-10 fill-current group-hover/btn:scale-110 transition-transform ml-1" />
                        </button>
                        <p className="text-white font-bold tracking-widest uppercase text-xs">Generate AI Demo</p>
                      </div>
                    )}
                  </motion.div>
                )}

                {isGenerating && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-30 p-12 text-center"
                  >
                    <div className="space-y-8 max-w-lg">
                      <div className="relative">
                        <Loader2 className="w-16 h-16 text-accent animate-spin mx-auto" />
                        <div className="absolute inset-0 bg-accent blur-2xl opacity-20 animate-pulse" />
                      </div>
                      <div className="space-y-2">
                        <h3 className="text-2xl font-bold text-white tracking-tight">Generating Your Demo</h3>
                        <p className="text-accent font-mono text-xs uppercase tracking-[0.2em] h-4">{loadingMessage}</p>
                      </div>
                      <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                        <motion.div
                          className="h-full bg-accent"
                          initial={{ width: 0 }}
                          animate={{ width: '100%' }}
                          transition={{ duration: 60, ease: 'linear' }}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Video controls */}
              {videoUrl && !isGenerating && (
                <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/80 to-transparent flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="flex items-center gap-4">
                    <button onClick={togglePlayback} className="text-white hover:text-accent transition-colors">
                      {isPlaying ? <Pause className="w-6 h-6" /> : <Play className="w-6 h-6" />}
                    </button>
                    <button onClick={restartVideo} className="text-white hover:text-accent transition-colors">
                      <RotateCcw className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {[
                { label: 'Live Status', val: 'Monitoring Active', accent: true },
                { label: 'Current Zone', val: 'Chennai South-4', accent: false },
                { label: 'Active Plan',  val: 'Pro (₹119/wk)',   accent: false },
              ].map(card => (
                <div key={card.label} className={cn('glass-card p-6', card.accent && 'border-success/20')}>
                  <div className="flex items-center gap-3 mb-2">
                    {card.accent && <div className="w-2 h-2 rounded-full bg-success animate-pulse" />}
                    <span className={cn('text-[10px] font-black uppercase tracking-widest', card.accent ? 'text-success' : 'text-text-secondary')}>{card.label}</span>
                  </div>
                  <p className="text-sm font-bold">{card.val}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Steps / Walkthrough */}
          <div className="space-y-6">
            <h3 className="text-xl font-bold mb-8 flex items-center gap-3">
              <Zap className="w-6 h-6 text-accent" /> How it works
            </h3>
            <div className="space-y-4">
              {DEMO_STEPS.map((step, i) => (
                <motion.div
                  key={step.title}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.1 }}
                  className={cn(
                    'glass-card p-6 border-l-4 transition-all duration-500 cursor-pointer',
                    currentStep === i ? 'border-l-accent bg-accent/5 scale-[1.02]' : 'border-l-transparent hover:bg-surface'
                  )}
                  onClick={() => setCurrentStep(i)}
                >
                  <div className="flex items-start gap-4">
                    <div className="mt-1">{step.icon}</div>
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-bold text-sm">{step.title}</h4>
                        <span className="text-[10px] font-mono text-text-secondary">{step.timestamp}</span>
                      </div>
                      <p className="text-xs text-text-secondary leading-relaxed">{step.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="pt-8">
              <button
                onClick={() => navigate('/plans')}
                className="w-full py-5 bg-accent text-white rounded-2xl font-bold text-lg hover:glow-accent transition-all shadow-xl shadow-accent/20 flex items-center justify-center gap-3 group"
              >
                Get Protected Now <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
              <p className="text-[10px] text-center text-text-secondary uppercase tracking-widest font-bold mt-4">
                Join 50,000+ protected gig workers
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WatchDemo;
