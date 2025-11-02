import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  fetchHosts,
  fetchComparison,
  fetchDiscovery,
  importDiscovery,
  createJob,
  fetchJob,
  fetchHostMetrics,
  type HostSummary,
  type ComparisonMetric,
  type DiscoveryHost,
  type JobSummary,
  type HostMetricsResponse,
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

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation<JobSummary, Error, number>({
    mutationFn: createJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    }
  });
}

export function useJob(jobId: number | null) {
  return useQuery<JobSummary, Error>({
    queryKey: ['job', jobId],
    queryFn: () => fetchJob(jobId as number),
    enabled: jobId != null,
    refetchInterval: (data) => {
      if (!data) {
        return 2000;
      }
      return data.status in ['completed', 'error'] ? false : 2000;
    },
    refetchOnWindowFocus: false,
  });
}

export function useHostMetrics(hostId: number | null) {
  return useQuery<HostMetricsResponse, Error>({
    queryKey: ['metrics', hostId],
    queryFn: () => fetchHostMetrics(hostId as number),
    enabled: hostId != null,
    staleTime: 15 * 1000,
    refetchOnWindowFocus: false,
  });
}
