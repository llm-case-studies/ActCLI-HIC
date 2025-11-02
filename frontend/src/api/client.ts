export interface HostSummary {
  id: number;
  hostname: string;
  tags: string[];
  lastSeenAt?: string;
  allowPrivileged?: boolean;
}

export interface ComparisonMetric {
  host_id: number;
  category: string;
  label: string;
  value: string | number | null;
  hint?: string;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export async function fetchHosts(): Promise<HostSummary[]> {
  const response = await fetch(`${API_BASE}/hosts`);
  if (!response.ok) {
    throw new Error(`Failed to fetch hosts (${response.status})`);
  }
  return response.json();
}

export async function fetchDiscovery(): Promise<unknown> {
  const response = await fetch(`${API_BASE}/discover/hosts`);
  if (!response.ok) {
    throw new Error(`Failed to fetch discovery (${response.status})`);
  }
  return response.json();
}

export async function fetchComparison(
  hosts: string[],
  categories: string[]
): Promise<ComparisonMetric[]> {
  if (!hosts.length) return [];
  const params = new URLSearchParams();
  hosts.forEach((h) => params.append('hosts', h));
  categories.forEach((c) => params.append('categories', c));
  const response = await fetch(`${API_BASE}/comparisons?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch comparison (${response.status})`);
  }
  return response.json();
}
