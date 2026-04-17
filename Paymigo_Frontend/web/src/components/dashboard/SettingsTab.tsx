import React from 'react';
import type { Worker } from '../../types/dashboard';

interface SettingsTabProps {
  workerData: Worker | null;
}

const NOTIFICATION_PREFS = [
  { label: 'Rainfall Alerts', desc: 'Get notified when rain is predicted in your zone' },
  { label: 'Payout Confirmations', desc: 'Instant alerts for wallet credits' },
  { label: 'Weekly Reports', desc: 'Summary of your earnings and protection' },
];

const SettingsTab = ({ workerData }: SettingsTabProps) => (
  <div className="max-w-2xl space-y-8">
    <div className="glass-card p-8">
      <h3 className="text-xl font-bold mb-8">Profile Settings</h3>
      <div className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Full Name</label>
            <input
              type="text"
              defaultValue={workerData?.name || 'Ravi Kumar'}
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 outline-none focus:border-accent"
            />
          </div>
          <div className="space-y-2">
            <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Phone Number</label>
            <input
              type="text"
              defaultValue={workerData?.phone || '+91 98765 43210'}
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 outline-none focus:border-accent"
            />
          </div>
        </div>
        <div className="space-y-2">
          <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">UPI ID</label>
          <input
            type="text"
            defaultValue="ravi.delivery@okaxis"
            className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 outline-none focus:border-accent"
          />
        </div>
        <button className="px-8 py-3 bg-accent text-background rounded-xl font-bold">Save Changes</button>
      </div>
    </div>

    <div className="glass-card p-8">
      <h3 className="text-xl font-bold mb-8">Notification Preferences</h3>
      <div className="space-y-4">
        {NOTIFICATION_PREFS.map((pref, i) => (
          <div key={i} className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
            <div>
              <div className="font-bold text-sm">{pref.label}</div>
              <div className="text-[10px] text-text-secondary">{pref.desc}</div>
            </div>
            <div className="w-10 h-5 bg-accent rounded-full relative cursor-pointer">
              <div className="absolute right-1 top-1 w-3 h-3 bg-background rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export default SettingsTab;
