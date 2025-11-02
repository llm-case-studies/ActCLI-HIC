export interface HostSummary {
  id: number;
  hostname: string;
  address?: string | null;
  tags: string[];
  source?: string | null;
  notes?: string | null;
  is_active?: boolean;
  allow_privileged?: boolean;
  ssh_target?: string | null;
  last_seen_at?: string | null;
}

export interface ComparisonMetric {
  host_id: number;
  category: string;
  label: string;
  value: string | number | null;
  hint?: string;
}

export interface DiscoveryHost {
  hostname: string;
  addresses: string[];
  sources: string[];
  tags: string[];
  ssh_aliases: string[];
  known_host_id?: number | null;
  is_active?: boolean | null;
  allow_privileged?: boolean | null;
  warnings: string[];
}

export interface JobSummary {
  id: number;
  host_id: number;
  status: string;
  requested_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string | null;
}

export interface HostMetricsResponse {
  host_id: number;
  collected_at: string;
  markdown: string;
  metrics: Record<string, unknown>;
  ratings: Record<string, unknown>;
  tips: string[];
  storage_hint?: string | null;
  system: Record<string, unknown>;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export async function fetchHosts(): Promise<HostSummary[]> {
  const response = await fetch(`${API_BASE}/hosts`);
  if (!response.ok) {
    throw new Error(`Failed to fetch hosts (${response.status})`);
  }
  return response.json();
}

export async function fetchDiscovery(): Promise<DiscoveryHost[]> {
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

export async function importDiscovery(hostnames: string[]): Promise<HostSummary[]> {
  const response = await fetch(`${API_BASE}/discover/hosts/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hostnames })
  });
  if (!response.ok) {
    throw new Error(`Failed to import discovery (${response.status})`);
  }
  return response.json();
}

export async function createJob(hostId: number): Promise<JobSummary> {
  const response = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ host_id: hostId })
  });
  if (!response.ok) {
    throw new Error(`Failed to queue assessment (${response.status})`);
  }
  return response.json();
}

export async function fetchJob(jobId: number): Promise<JobSummary> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch job (${response.status})`);
  }
  return response.json();
}

export async function fetchHostMetrics(hostId: number): Promise<HostMetricsResponse> {
  const response = await fetch(`${API_BASE}/hosts/${hostId}/metrics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch host metrics (${response.status})`);
  }
  return response.json();
}
