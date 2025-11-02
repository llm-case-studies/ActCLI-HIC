import { useMemo } from 'react';
import { useAppState } from '../state/appState';
import { palette } from '../styles/theme';
import { useHosts, useDiscovery, useImportDiscovery } from '../api/hooks';

const CATEGORY_OPTIONS = [
  { id: 'overview', label: 'Overview' },
  { id: 'memory', label: 'Memory' },
  { id: 'storage', label: 'Storage' },
  { id: 'cpu', label: 'CPU' },
  { id: 'gpu', label: 'GPU' },
  { id: 'software', label: 'Software' }
];

export function ExploreView() {
  const { selectedHost, activeTheme, selectHost } = useAppState();
  const { data: hosts = [], isLoading, isError } = useHosts();
  const { data: discovery = [], isLoading: loadingDiscovery } = useDiscovery();
  const importDiscoveryMutation = useImportDiscovery();
  const theme = palette[activeTheme];

  const activeHost = hosts.find((h) => String(h.id) === selectedHost) ?? hosts[0];
  const info = useMemo(
    () => ({
      host: activeHost,
      summary: 'Assessment pending implementation.',
      categories: CATEGORY_OPTIONS
    }),
    [activeHost]
  );

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', minHeight: '100%' }}>
      <div
        style={{
          borderRight: '1px solid rgba(255,255,255,0.08)',
          padding: '1.25rem',
          background: theme.surface
        }}
      >
        <h2 style={{ marginTop: 0, fontSize: '1rem', color: theme.brand }}>Host Explorer</h2>
        <p style={{ color: theme.hint, fontSize: '0.85rem' }}>
          Browse hosts discovered via the API. Selecting a host will show category panels backed by future assessments.
        </p>
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {isLoading && <span style={{ color: theme.hint }}>Loading hosts…</span>}
          {isError && <span style={{ color: theme.hint }}>Unable to load hosts.</span>}
          {!isLoading && !isError && !hosts.length && <span style={{ color: theme.hint }}>No hosts registered.</span>}
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
                  cursor: 'pointer'
                }}
              >
                <strong>{host.hostname}</strong>
                <span style={{ display: 'block', fontSize: '0.75rem', color: theme.hint }}>
                  last seen · {host.lastSeenAt ?? 'unknown'}
                </span>
              </button>
            );
          })}
          {!isLoading && !isError && !hosts.length && (
            <div style={{ marginTop: '1rem' }}>
              <p style={{ color: theme.hint, fontSize: '0.85rem' }}>Promote discovered hosts:</p>
              {loadingDiscovery && <span style={{ color: theme.hint }}>Scanning…</span>}
              {!loadingDiscovery && discovery.length === 0 && (
                <span style={{ color: theme.hint }}>No discovery results.</span>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {discovery.map((item) => (
                  <button
                    key={item.hostname}
                    type="button"
                    onClick={() => importDiscoveryMutation.mutate([item.hostname])}
                    disabled={importDiscoveryMutation.isLoading}
                    style={{
                      textAlign: 'left',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '0.5rem',
                      border: '1px dashed rgba(255,255,255,0.2)',
                      background: 'rgba(255,255,255,0.05)',
                      color: theme.text,
                      cursor: 'pointer'
                    }}
                  >
                    {item.hostname}
                    <span style={{ display: 'block', fontSize: '0.75rem', color: theme.hint }}>
                      {item.addresses[0] ?? 'unknown address'}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      <section style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {activeHost ? (
          <>
            <header>
              <h2 style={{ margin: 0, fontSize: '1.4rem' }}>{activeHost.hostname}</h2>
              <p style={{ color: theme.hint }}>
                Explore host metrics. Assessment integrations will replace the placeholder content below.
              </p>
            </header>
            <article style={{ background: theme.surface, borderRadius: '1rem', padding: '1.5rem' }}>
              <h3 style={{ marginTop: 0, fontSize: '1rem', color: theme.brand }}>Summary</h3>
              <p style={{ lineHeight: 1.6 }}>{info.summary}</p>
            </article>
            <section style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
              {info.categories.map((category) => (
                <div
                  key={category.id}
                  style={{
                    padding: '1rem',
                    borderRadius: '0.75rem',
                    background: theme.surface,
                    border: '1px solid rgba(255,255,255,0.08)'
                  }}
                >
                  <h4 style={{ marginTop: 0 }}>{category.label}</h4>
                  <p style={{ fontSize: '0.85rem', color: theme.hint }}>
                    Data cards will appear here (memory slots, NVMe drives, etc.).
                  </p>
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
