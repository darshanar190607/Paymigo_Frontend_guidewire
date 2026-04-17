import React from 'react';
import { Zap, CheckCircle2, FileText, Download } from 'lucide-react';
import type { Worker } from '../../types/dashboard';

interface PolicyTabProps {
  workerData: Worker | null;
}

const PolicyTab = ({ workerData }: PolicyTabProps) => {
  const getRenewalDate = () => {
    if (!workerData?.createdAt) return 'N/A';
    const created = new Date(workerData.createdAt?.toDate?.() || workerData.createdAt);
    const nextRenewal = new Date(created.getTime() + 7 * 24 * 60 * 60 * 1000);
    return nextRenewal.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const getBenefits = (plan: string): string[] => {
    const common = ['Instant 90s Payout', 'Parametric Rain Trigger', 'GigWallet Integration'];
    switch (plan) {
      case 'Premium': return [...common, 'All Weather Extremes Coverage', 'Priority Support', 'Zero Deductible'];
      case 'Pro': return [...common, 'Monsoon Stay-at-Home Benefit', 'Weekly Risk Reports'];
      default: return [...common, 'Essential Rain Protection', 'Basic Support'];
    }
  };

  const benefits = getBenefits(workerData?.plan || 'Pro');

  const handleDocDownload = async (docName: string, filePath: string) => {
    try {
      const response = await fetch(filePath);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${docName}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download file:', err);
    }
  };

  return (
    <div className="space-y-8">
      <div className="glass-card p-8">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h2 className="text-3xl font-display font-bold mb-2">{workerData?.plan || 'Pro'} Shield</h2>
            <p className="text-text-secondary">Policy ID: PK-{workerData?.id?.slice(0, 4).toUpperCase() || '9928'}-X</p>
          </div>
          <div className="px-4 py-2 bg-success/10 border border-success/20 text-success rounded-full text-xs font-bold uppercase">
            {workerData?.status || 'Active'}
          </div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'Weekly Premium', val: `₹${workerData?.weeklyPremium || 119}`, className: 'text-accent' },
            { label: 'Max Coverage', val: '₹1,500 / day', className: '' },
            { label: 'Trigger', val: '15mm / hr', className: '' },
            { label: 'Next Renewal', val: getRenewalDate(), className: 'text-warning' },
          ].map((item, i) => (
            <div key={i} className="p-6 bg-white/5 rounded-2xl border border-white/5">
              <div className="text-[10px] text-text-secondary font-black uppercase tracking-widest mb-2">{item.label}</div>
              <div className={`text-xl font-bold ${item.className}`}>{item.val}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        <div className="glass-card p-8">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-accent" /> Key Benefits
          </h3>
          <div className="space-y-4">
            {benefits.map((benefit, i) => (
              <div key={i} className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/5">
                <CheckCircle2 className="w-5 h-5 text-success shrink-0" />
                <span className="text-sm font-medium">{benefit}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-8">
          <h3 className="text-xl font-bold mb-6">Policy Documents</h3>
          <div className="space-y-4">
            {[
              { name: 'Policy Schedule', size: '1.2 MB', file: '/docs/policy-schedule.pdf' },
              { name: 'Terms & Conditions', size: '0.8 MB', file: '/docs/terms-and-conditions.pdf' },
              { name: 'Trigger Mechanism Guide', size: '2.1 MB', file: '/docs/trigger-mechanism-guide.pdf' },
            ].map((doc, i) => (
              <div
                key={i}
                onClick={() => handleDocDownload(doc.name, doc.file)}
                className="flex justify-between items-center p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-text-secondary group-hover:text-accent" />
                  <div>
                    <div className="text-sm font-bold">{doc.name}</div>
                    <div className="text-[10px] text-text-secondary uppercase">{doc.size} • PDF</div>
                  </div>
                </div>
                <Download className="w-4 h-4 text-text-secondary group-hover:text-accent" />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="glass-card p-8">
        <h3 className="text-xl font-bold mb-6">Coverage Zones</h3>
        <div className="space-y-4">
          <div className="flex justify-between items-center p-4 bg-accent/10 border border-accent/20 rounded-xl">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-accent rounded-full" />
              <span className="font-bold">{workerData?.zone || 'Chennai Zone 4'} (Primary)</span>
            </div>
            <span className="text-[10px] font-bold text-accent uppercase tracking-widest">Active</span>
          </div>
        </div>
        <button className="w-full mt-6 py-4 border border-white/10 rounded-xl text-sm font-bold hover:bg-white/5 transition-all">
          Add Secondary Zone
        </button>
      </div>
    </div>
  );
};

export default PolicyTab;
