import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | string) {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(num);
}

// ─── Admin guard ──────────────────────────────────────────────────────────────
// Single source-of-truth for admin email list.
// To add/remove admins, change only this array — no need to touch any component.
const ADMIN_EMAILS: readonly string[] = [
  'admin@gmail.com',
  'vennila498@gmail.com',
];

export const isAdminUser = (email: string | null | undefined): boolean =>
  ADMIN_EMAILS.includes(email ?? '');
