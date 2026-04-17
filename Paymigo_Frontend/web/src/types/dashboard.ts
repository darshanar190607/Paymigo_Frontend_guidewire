import { Timestamp } from 'firebase/firestore';

export interface Worker {
  id: string;
  name: string;
  phone: string;
  city: string;
  zone: string;
  plan: 'Basic' | 'Pro' | 'Premium';
  weeklyPremium: number;
  status: 'ACTIVE' | 'INACTIVE';
  isMonsoon: boolean;
  createdAt: Timestamp;
}

export interface WalletData {
  workerId: string;
  availableBalance: number;
  loyaltyPoolBalance: number;
  premiumReserve: number;
  fuelCashbackEarned?: number;
  totalEarned: number;
  totalWithdrawn: number;
}

export interface Claim {
  id: string;
  workerId: string;
  workerName: string;
  workerCity: string;
  workerZone: string;
  type: string;
  description: string;
  statement: string;
  amount: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  adminComment?: string;
  createdAt: Timestamp;
}

export interface AppNotification {
  id: string;
  workerId: string;
  title: string;
  message: string;
  read: boolean;
  createdAt: Timestamp;
  /** Pre-formatted at setState time — avoids new Date() on every render */
  formattedDate: string;
}
