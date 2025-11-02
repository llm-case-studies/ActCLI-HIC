import { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useAppState, type CategoryId } from '../state/appState';
import { palette } from '../styles/theme';
import {
  useHosts,
  useDiscovery,
  useImportDiscovery,
  useHostMetrics,
  useCreateJob,
  useJob,
} from '../api/hooks';

const CATEGORY_OPTIONS: { id: CategoryId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'memory', label: 'Memory' },
  { id: 'storage', label: 'Storage' },
  { id: 'cpu', label: 'CPU' },
  { id: 'gpu', label: 'GPU' },
  { id: 'software', label: 'Software' },
];

const formatDateTime = (iso?: string | null) => {
  if (!iso) return 'unknown';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return 'unknown';
  return date.toLocaleString();
};

const formatNumber = (value?: number | null, fractionDigits = 1) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 'Unknown';
  }
  return value.toFixed(fractionDigits);
};

export function ExploreView() {
  const { selectedHost, activeTheme, selectHost } = useAppState();
  const queryClient = useQueryClient();

  const { data: hosts = [], isLoading, isError } = useHosts();
  const { data: discovery = [], isLoading: loadingDiscovery } = useDiscovery();
  const importDiscoveryMutation = useImportDiscovery();
  const createJobMutation = useCreateJob();

  const [activeJobId, setActiveJobId] = useState<number | null>(null);
  const jobQuery = useJob(activeJobId);

  const activeHost = useMemo(
    () => hosts.find((h) => String(h.id) === selectedHost) ?? hosts[0],
    [hosts, selectedHost]
  );

  useEffect(() => {
    if (!selectedHost && hosts.length) {
      selectHost(String(hosts[0].id));
    }
  }, [hosts, selectHost, selectedHost]);

  const selectedHostId = activeHost?.id ?? null;
  const metricsQuery = useHostMetrics(selectedHostId);

  useEffect(() => {
    const status = jobQuery.data?.status;
    if (!status || !activeJobId) {
      return;
    }
    if (status === 'completed') {
      queryClient.invalidateQueries({ queryKey: ['metrics', selectedHostId] });
      queryClient.invalidateQueries({ queryKey: ['hosts'] });
      queryClient.invalidateQueries({ queryKey: ['comparison'] });
      setActiveJobId(null);
    } else if (status === 'error') {
      setActiveJobId(null);
    }
  }, [jobQuery.data?.status, activeJobId, queryClient, selectedHostId]);

  const handleRunAssessment = () => {
    if (!activeHost) {
      return;
    }
    createJobMutation.mutate(activeHost.id, {
      onSuccess: (job) => {
        setActiveJobId(job.id);
      },
    });
  };

  const theme = palette[activeTheme];

  const metricsData = (metricsQuery.data?.metrics ?? {}) as Record<string, any>;
  const ratingsData = (metricsQuery.data?.ratings ?? {}) as Record<string, any>;
  const tips: string[] = metricsQuery.data?.tips ?? [];
  const storageHint: string | undefined = metricsQuery.data?.storage_hint as string | undefined;
  const systemData = (metricsQuery.data?.system ?? {}) as Record<string, any>;

  const workstationRating = (ratingsData['Developer workstation'] as Record<string, any> | undefined)?.summary;
  const overviewSummary = metricsQuery.isLoading
    ? 'Collecting metrics…'
    : metricsQuery.data
      ? workstationRating ?? 'Assessment captured successfully.'
      : 'Run an assessment to populate metrics.';

  const renderCategoryBody = (category: CategoryId) => {
    switch (category) {
      case 'overview': {
        const virtualization = metricsData.virtualization ?? 'Unknown';
        return (
          <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
            <li>Manufacturer: {systemData.manufacturer ?? 'Unknown'}</li>
            <li>Product: {systemData.product_name ?? 'Unknown'}</li>
            <li>BIOS: {systemData.bios_version ?? 'Unknown'}</li>
            <li>Virtualization: {virtualization}</li>
          </ul>
        );
      }
      case 'memory': {
        const ramTotal = typeof metricsData.ram_total_gb === 'number' ? metricsData.ram_total_gb : null;
        const ramMax = typeof metricsData.ram_max_capacity_gb === 'number' ? metricsData.ram_max_capacity_gb : null;
        const ramEmpty = typeof metricsData.ram_empty === 'number' ? metricsData.ram_empty : null;
        const configuredSpeed = metricsData.ram_configured_speed_mts;
        return (
          <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
            <li>Total: {ramTotal !== null ? `${formatNumber(ramTotal)} GB` : 'Unknown'}</li>
            <li>Max: {ramMax !== null ? `${formatNumber(ramMax, 0)} GB` : 'Unknown'}</li>
            <li>Empty slots: {ramEmpty !== null ? ramEmpty : 'Unknown'}</li>
            <li>Configured speed: {configuredSpeed ?? 'Unknown'} MT/s</li>
          </ul>
        );
      }
      case 'storage': {
        const storageTotal = metricsData.storage_total;
        const storageNvme = metricsData.storage_nvme;
        return (
          <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
            <li>Total devices: {storageTotal ?? 'Unknown'}</li>
            <li>NVMe devices: {storageNvme ?? 'Unknown'}</li>
            {storageHint && <li>{storageHint}</li>}
          </ul>
        );
      }
      case 'cpu': {
        const cpuModel = metricsData.cpu_model ?? 'Unknown';
        const cores = metricsData.cores;
        const threads = metricsData.threads;
        const cpuMax = typeof metricsData.cpu_max_ghz === 'number' ? metricsData.cpu_max_ghz : null;
        const cpuMin = typeof metricsData.cpu_min_ghz === 'number' ? metricsData.cpu_min_ghz : null;
        const cpuCur = typeof metricsData.cpu_cur_ghz === 'number' ? metricsData.cpu_cur_ghz : null;
        return (
          <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
            <li>Model: {cpuModel}</li>
            <li>Cores / Threads: {cores ?? '?'} / {threads ?? '?'}</li>
            <li>Frequency: min {cpuMin ? `${cpuMin.toFixed(2)} GHz` : '?'} · current {cpuCur ? `${cpuCur.toFixed(2)} GHz` : '?'} · max {cpuMax ? `${cpuMax.toFixed(2)} GHz` : '?'}</li>
          </ul>
        );
      }
      case 'gpu': {
        const hasGpu = metricsData.has_dedicated_gpu;
        const gpuVram = typeof metricsData.gpu_vram_gb === 'number' ? metricsData.gpu_vram_gb : null;
        return (
          <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
            <li>Discrete GPU: {hasGpu ? 'Yes' : 'No'}</li>
            <li>
              VRAM: {gpuVram !== null ? `${gpuVram.toFixed(1)} GB` : hasGpu ? 'Unknown' : 'n/a'}
            </li>
          </ul>
        );
      }
      case 'software':
      default:
        return <p style={{ margin: 0, color: palette[activeTheme].hint }}>Software inventory capture planned for a later sprint.</p>;
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', minHeight: '100%' }}>
      <div
        style={{
          borderRight: '1px solid rgba(255,255,255,0.08)',
          padding: '1.25rem',
          background: theme.surface,
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: '1rem', color: theme.brand }}>Host Explorer</h2>
        <p style={{ color: theme.hint, fontSize: '0.85rem' }}>
          Import discovered nodes and trigger assessments to populate metrics.
        </p>
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {isLoading && <span style={{ color: theme.hint }}>Loading hosts…</span>}
          {isError && <span style={{ color: theme.hint }}>Unable to load hosts.</span>}
          {hosts.map((host) => {
            const hostId = String(host.id);
            const active = hostId === selectedHost;
            return (
              <button
                key={host.id}
                type="button"
                onClick={() => selectHost(hostId)}
                style={{
                  textAlign: 'left',
                  padding: '0.6rem 0.75rem',
                  borderRadius: '0.5rem',
                  border: '1px solid rgba(255,255,255,0.15)',
                  background: active ? 'rgba(255,255,255,0.12)' : 'transparent',
                  color: theme.text,
                  cursor: 'pointer',
                }}
              >
                <strong>{host.hostname}</strong>
                <span style={{ display: 'block', fontSize: '0.75rem', color: theme.hint }}>
                  last seen · {formatDateTime(host.lastSeenAt)}
                </span>
              </button>
            );
          })}
          {!isLoading && !isError && hosts.length === 0 && <span style={{ color: theme.hint }}>No hosts registered.</span>}
        </div>

        <section style={{ marginTop: '1.5rem' }}>
          <h3 style={{ margin: 0, fontSize: '0.85rem', color: theme.hint, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Discoveries
          </h3>
          {loadingDiscovery && <p style={{ color: theme.hint }}>Scanning…</p>}
          {!loadingDiscovery && discovery.length === 0 && <p style={{ color: theme.hint }}>Nothing discovered yet.</p>}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
            {discovery.map((item) => {
              const alreadyImported = Boolean(item.known_host_id);
              return (
                <button
                  key={item.hostname}
                  type="button"
                  onClick={() => importDiscoveryMutation.mutate([item.hostname])}
                  disabled={alreadyImported || importDiscoveryMutation.isLoading}
                  style={{
                    textAlign: 'left',
                    padding: '0.5rem 0.75rem',
                    borderRadius: '0.5rem',
                    border: '1px dashed rgba(255,255,255,0.25)',
                    background: alreadyImported ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.08)',
                    color: theme.text,
                    cursor: alreadyImported ? 'default' : 'pointer',
                  }}
                >
                  <strong>{item.hostname}</strong>
                  <span style={{ display: 'block', fontSize: '0.75rem', color: theme.hint }}>
                    {item.addresses[0] ?? 'unknown address'}
                  </span>
                </button>
              );
            })}
          </div>
          {importDiscoveryMutation.isError && (
            <p style={{ color: '#F05A28', fontSize: '0.8rem', marginTop: '0.5rem' }}>Import failed. Check logs.</p>
          )}
        </section>
      </div>

      <section style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {activeHost ? (
          <>
            <header>
              <h2 style={{ margin: 0, fontSize: '1.4rem' }}>{activeHost.hostname}</h2>
              <p style={{ color: theme.hint }}>{overviewSummary}</p>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem', alignItems: 'center' }}>
                <button
                  type="button"
                  onClick={handleRunAssessment}
                  disabled={createJobMutation.isLoading || Boolean(activeJobId)}
                  style={{
                    padding: '0.55rem 1rem',
                    borderRadius: '0.5rem',
                    border: 'none',
                    fontWeight: 600,
                    background: theme.accent,
                    color: '#0b0b0b',
                    cursor: 'pointer',
                  }}
                >
                  {createJobMutation.isLoading ? 'Queuing…' : 'Run assessment'}
                </button>
                {jobQuery.data?.status === 'running' && <span style={{ color: theme.hint }}>Assessment running…</span>}
                {jobQuery.data?.status === 'error' && (
                  <span style={{ color: '#F05A28' }}>Assessment failed — check backend logs.</span>
                )}
              </div>
            </header>

            <article style={{ background: theme.surface, borderRadius: '1rem', padding: '1.5rem' }}>
              <h3 style={{ marginTop: 0, fontSize: '1rem', color: theme.brand }}>Upgrade Tips</h3>
              {metricsQuery.isLoading ? (
                <p style={{ color: theme.hint }}>Collecting tips…</p>
              ) : tips.length ? (
                <ul style={{ paddingLeft: '1.1rem', margin: 0 }}>
                  {tips.map((tip) => (
                    <li key={tip}>{tip}</li>
                  ))}
                </ul>
              ) : (
                <p style={{ color: theme.hint }}>Run an assessment to surface upgrade suggestions.</p>
              )}
            </article>

            <section style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
              {CATEGORY_OPTIONS.map((category) => (
                <div
                  key={category.id}
                  style={{
                    padding: '1rem',
                    borderRadius: '0.75rem',
                    background: theme.surface,
                    border: '1px solid rgba(255,255,255,0.08)',
                  }}
                >
                  <h4 style={{ marginTop: 0 }}>{category.label}</h4>
                  {metricsQuery.isFetching && !metricsQuery.data ? (
                    <p style={{ color: theme.hint }}>Loading…</p>
                  ) : metricsQuery.isError || !metricsQuery.data ? (
                    <p style={{ color: theme.hint }}>No data yet. Run an assessment.</p>
                  ) : (
                    renderCategoryBody(category.id)
                  )}
                </div>
              ))}
            </section>
          </>
        ) : (
          <p style={{ color: theme.hint }}>No hosts selected.</p>
        )}
      </section>
    </div>
  );
}
