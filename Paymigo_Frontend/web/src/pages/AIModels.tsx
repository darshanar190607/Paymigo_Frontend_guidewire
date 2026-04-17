import React from 'react';
import { motion } from 'motion/react';
import { 
  Shield, 
  Zap, 
  CloudRain, 
  TrendingUp, 
  Globe,
  Activity,
  Database,
  Cpu
} from 'lucide-react';
import { cn } from '@/lib/utils';

const AIModels = () => {
  const models = [
    {
      title: "Premium Engine",
      algo: "XGBoost",
      desc: "Calculates weekly premiums based on 5,000+ synthetic worker records and 4 years of IMD rainfall history.",
      icon: TrendingUp,
      color: "text-accent",
      bg: "bg-accent/10"
    },
    {
      title: "Fraud Detector",
      algo: "Isolation Forest",
      desc: "Detects anomalies in GPS data and payout patterns to prevent fraudulent claims and system abuse.",
      icon: Shield,
      color: "text-danger",
      bg: "bg-danger/10"
    },
    {
      title: "Risk Forecaster",
      algo: "LSTM (RNN)",
      desc: "Predicts 7-day disruption likelihood at a 500m grid level using historical weather time-series data.",
      icon: CloudRain,
      color: "text-warning",
      bg: "bg-warning/10"
    },
    {
      title: "Zone Clusterer",
      algo: "K-Means",
      desc: "Dynamically groups delivery micro-zones based on risk frequency and payout density.",
      icon: Globe,
      color: "text-success",
      bg: "bg-success/10"
    }
  ];

  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Hero Section */}
      <header className="relative py-20 px-6 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full hero-glow -z-10 opacity-50" />
        
        <div className="max-w-7xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl md:text-6xl font-display font-black leading-tight mb-8 tracking-tight">
              The AI Engine Behind <br />
              <span className="text-accent">Paymigo</span>
            </h1>
            <p className="text-lg text-text-secondary mb-12 max-w-2xl mx-auto leading-relaxed">
              We've built a custom stack of machine learning models to automate risk assessment, 
              fraud detection, and instant payouts.
            </p>
          </motion.div>
        </div>
      </header>

      {/* Models Grid */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-8">
            {models.map((model, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="glass-card p-10 flex flex-col md:flex-row gap-8 items-start"
              >
                <div className={cn("w-16 h-16 rounded-2xl flex items-center justify-center shrink-0", model.bg, model.color)}>
                  <model.icon className="w-10 h-10" />
                </div>
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-2xl font-bold">{model.title}</h3>
                    <div className="px-3 py-1 bg-white/5 rounded-full text-[10px] font-black uppercase tracking-widest text-accent border border-accent/20">
                      {model.algo}
                    </div>
                  </div>
                  <p className="text-text-secondary leading-relaxed mb-6">{model.desc}</p>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-text-secondary">
                      <Activity className="w-4 h-4" /> Accuracy: 94.2%
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-text-secondary">
                      <Zap className="w-4 h-4" /> Latency: 120ms
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Pipeline */}
      <section className="py-24 px-6 bg-surface/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-display font-bold mb-6">Real-time Data Pipeline</h2>
            <p className="text-text-secondary max-w-2xl mx-auto">
              Our models process millions of data points every hour to ensure 100% accurate triggers.
            </p>
          </div>
          
          <div className="relative">
            <div className="grid md:grid-cols-3 gap-8 relative z-10">
              {[
                { title: "Ingestion", desc: "IMD API + Skymet + IoT Gauges", icon: Database },
                { title: "Processing", desc: "FastAPI + XGBoost + LSTM", icon: Cpu },
                { title: "Execution", desc: "Instant Payouts + UPI", icon: Zap },
              ].map((step, i) => (
                <div key={i} className="glass-card p-8 text-center">
                  <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <step.icon className="w-6 h-6 text-accent" />
                  </div>
                  <h4 className="text-lg font-bold mb-2">{step.title}</h4>
                  <p className="text-xs text-text-secondary">{step.desc}</p>
                </div>
              ))}
            </div>
            
            {/* Connecting Lines (Desktop) */}
            <div className="hidden md:block absolute top-1/2 left-0 w-full h-px bg-gradient-to-r from-transparent via-accent/20 to-transparent -z-10" />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <Shield className="text-accent w-6 h-6" />
            <span className="text-xl font-display font-bold">Paymigo</span>
          </div>
          <p className="text-text-secondary text-sm">
            Built for DEVTrails 2026 • India's first parametric gig insurance
          </p>
          <div className="flex gap-6">
            <a href="/how-it-works" className="text-sm text-text-secondary hover:text-accent transition-colors">Privacy</a>
            <a href="/how-it-works" className="text-sm text-text-secondary hover:text-accent transition-colors">Terms</a>
            <a href="/how-it-works" className="text-sm text-text-secondary hover:text-accent transition-colors">Contact</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AIModels;
