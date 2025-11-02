import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  fetchHosts,
  fetchComparison,
  fetchDiscovery,
  importDiscovery,
  type HostSummary,
  type ComparisonMetric,
  type DiscoveryHost,
} from './client';

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

export function useDiscovery() {
  return useQuery<DiscoveryHost[], Error>({
    queryKey: ['discovery'],
    queryFn: fetchDiscovery,
    staleTime: 60 * 1000
  });
}

export function useImportDiscovery() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: importDiscovery,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hosts'] });
      queryClient.invalidateQueries({ queryKey: ['discovery'] });
    }
  });
}
