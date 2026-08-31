import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatIncome(amount: number): string {
  if (amount >= 10_000_000) return `₹${(amount / 10_000_000).toFixed(1)} Cr`;
  if (amount >= 100_000) return `₹${(amount / 100_000).toFixed(1)} Lakh`;
  return `₹${amount.toLocaleString("en-IN")}`;
}

export function statusLabel(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function statusColor(status: string): string {
  switch (status) {
    case "likely_eligible":
      return "bg-green-100 text-green-800 border-green-200";
    case "possibly_eligible":
      return "bg-amber-100 text-amber-800 border-amber-200";
    case "insufficient_info":
      return "bg-blue-100 text-blue-800 border-blue-200";
    default:
      return "bg-gray-100 text-gray-800 border-gray-200";
  }
}
