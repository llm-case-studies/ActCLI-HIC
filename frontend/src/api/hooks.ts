import { useQuery } from '@tanstack/react-query';
import { fetchHosts, fetchComparison, type HostSummary, type ComparisonMetric } from './client';

export function useHosts() {
  return useQuery<HostSummary[], Error>({
    queryKey: ['hosts'],
    queryFn: fetchHosts,
    staleTime: 5 * 60 * 1000
  });
}

export function useComparison(hosts: string[], categories: string[]) {
  return useQuery<ComparisonMetric[], Error>({
    queryKey: ['comparison', hosts, categories],
    queryFn: () => fetchComparison(hosts, categories),
    enabled: hosts.length > 0
  });
}
