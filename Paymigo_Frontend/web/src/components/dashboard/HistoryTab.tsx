import React from 'react';
import { cn } from '@/lib/utils';
import type { Claim } from '../../types/dashboard';

interface HistoryTabProps {
  claims: Claim[];
}

const HistoryTab = ({ claims }: HistoryTabProps) => (
  <div className="glass-card p-8">
    <div className="flex justify-between items-center mb-8">
      <h3 className="text-xl font-bold">Full Activity History</h3>
    </div>
    {claims.length === 0 ? (
      <p className="text-text-secondary text-sm">No activity history yet.</p>
    ) : (
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="text-xs text-text-secondary uppercase tracking-widest border-b border-white/5">
              <th className="pb-4 font-bold">Date</th>
              <th className="pb-4 font-bold">Event</th>
              <th className="pb-4 font-bold">Amount</th>
              <th className="pb-4 font-bold">Status</th>
              <th className="pb-4 font-bold">Ref ID</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {claims.map((claim) => (
              <tr key={claim.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                <td className="py-4 text-text-secondary">
                  {new Date(claim.createdAt?.toDate?.() || claim.createdAt).toLocaleDateString()}
                </td>
                <td className="py-4 font-bold">{claim.type}</td>
                <td className={cn('py-4 font-mono font-bold', claim.status === 'APPROVED' ? 'text-success' : 'text-accent')}>
                   {claim.status === 'APPROVED' ? '+' : ''}₹{claim.amount}
                </td>
                <td className="py-4">
                  <span className={cn(
                    'px-2 py-0.5 rounded text-[10px] font-bold',
                    claim.status === 'APPROVED' ? 'bg-success/20 text-success' : 
                    claim.status === 'REJECTED' ? 'bg-red-500/20 text-red-500' : 'bg-warning/20 text-warning'
                  )}>
                    {claim.status}
                  </span>
                </td>
                <td className="py-4 text-text-secondary font-mono">{claim.id.slice(0, 8)}...</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </div>
);

export default HistoryTab;
