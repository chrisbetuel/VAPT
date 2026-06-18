import type { VulnerabilitySeverity } from "@/types";

export const severityColors: Record<VulnerabilitySeverity, string> = {
  critical: "bg-red-600 text-white",
  high: "bg-orange-600 text-white",
  medium: "bg-yellow-600 text-white",
  low: "bg-blue-600 text-white",
  info: "bg-gray-500 text-white",
};

export const severityBadge: Record<VulnerabilitySeverity, string> = {
  critical: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  high: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200",
  medium: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
  low: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  info: "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200",
};

export const severityOrder: Record<VulnerabilitySeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export function sortBySeverity(
  a: VulnerabilitySeverity,
  b: VulnerabilitySeverity,
): number {
  return (severityOrder[a] ?? 99) - (severityOrder[b] ?? 99);
}

export function getCvssLabel(score?: number): string {
  if (score == null) return "N/A";
  if (score >= 9.0) return "Critical";
  if (score >= 7.0) return "High";
  if (score >= 4.0) return "Medium";
  if (score >= 0.1) return "Low";
  return "Info";
}
