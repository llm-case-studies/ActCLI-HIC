import { useMemo } from 'react';
import { useAppState, type CategoryId } from '../state/appState';
import { palette } from '../styles/theme';
import { useHosts, useComparison } from '../api/hooks';

const CATEGORY_OPTIONS: { id: CategoryId; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'memory', label: 'Memory' },
  { id: 'storage', label: 'Storage' },
  { id: 'cpu', label: 'CPU' },
  { id: 'gpu', label: 'GPU' },
  { id: 'software', label: 'Software' }
];

export function CompareView() {
  const { activeTheme, compareHosts, toggleCompareHost, compareCategories, setCompareCategories } = useAppState();
  const theme = palette[activeTheme];
  const { data: hosts = [] } = useHosts();
  const { data: comparison = [], isLoading: loadingComparison, isError: comparisonError } = useComparison(
    compareHosts,
    compareCategories
  );

  const hostLookup = useMemo(() => {
    const lookup = new Map<string, string>();
    hosts.forEach((host) => lookup.set(String(host.id), host.hostname));
    return lookup;
  }, [hosts]);

  const table = useMemo(() => {
    if (!compareHosts.length) {
      return [];
    }
    const grouped = new Map<string, Record<CategoryId, string>>();
    comparison.forEach((metric) => {
      const hostId = String(metric.host_id);
      const bucket = grouped.get(hostId) ?? ({} as Record<CategoryId, string>);
      const text = metric.label ? `${metric.label}: ${metric.value ?? 'n/a'}` : String(metric.value ?? 'n/a');
      const category = metric.category as CategoryId;
      bucket[category] = bucket[category] ? `${bucket[category]} • ${text}` : text;
      grouped.set(hostId, bucket);
    });
    return compareHosts.map((hostId) => ({
      hostId,
      hostName: hostLookup.get(hostId) ?? hostId,
      metrics: grouped.get(hostId) ?? ({} as Record<CategoryId, string>)
    }));
  }, [compareHosts, comparison, hostLookup]);

  return (
    <div style={{ padding: '1.5rem', display: 'grid', gap: '1.5rem' }}>
      <header>
        <h2 style={{ margin: 0 }}>Comparison Workspace</h2>
        <p style={{ color: theme.hint }}>
          Select hosts and categories to compare. Export menu will wire into CSV/PDF flows described in docs.
        </p>
      </header>
      <section style={{ display: 'grid', gap: '1rem', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))' }}>
        <div style={{ background: theme.surface, borderRadius: '1rem', padding: '1.25rem' }}>
          <h3 style={{ marginTop: 0 }}>Hosts</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {hosts.length === 0 && <span style={{ color: theme.hint }}>No hosts available.</span>}
            {hosts.map((host) => {
              const hostId = String(host.id);
              const active = compareHosts.includes(hostId);
              return (
                <label key={host.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <input type="checkbox" checked={active} onChange={() => toggleCompareHost(hostId)} />
                  <span>{host.hostname}</span>
                </label>
              );
            })}
          </div>
        </div>
        <div style={{ background: theme.surface, borderRadius: '1rem', padding: '1.25rem' }}>
          <h3 style={{ marginTop: 0 }}>Categories</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {CATEGORY_OPTIONS.map((category) => {
              const active = compareCategories.includes(category.id);
              return (
                <label key={category.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={() => {
                      const next: CategoryId[] = active
                        ? compareCategories.filter((id) => id !== category.id)
                        : [...compareCategories, category.id];
                      setCompareCategories(next);
                    }}
                  />
                  <span>{category.label}</span>
                </label>
              );
            })}
          </div>
        </div>
        <div style={{ background: theme.surface, borderRadius: '1rem', padding: '1.25rem' }}>
          <h3 style={{ marginTop: 0 }}>Exports</h3>
          <p style={{ color: theme.hint, fontSize: '0.9rem' }}>
            Buttons below will call client-side CSV/PDF exports. API endpoints documented in backlog for automation.
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button style={exportButton(theme)} type="button">
              CSV (client)
            </button>
            <button style={exportButton(theme)} type="button">
              PDF (client)
            </button>
            <button style={exportGhostButton(theme)} type="button">
              PDF via API
            </button>
          </div>
        </div>
      </section>
      <section style={{ background: theme.surface, borderRadius: '1rem', padding: '1.5rem' }}>
        <h3 style={{ marginTop: 0 }}>Comparison Table</h3>
        {loadingComparison && <p style={{ color: theme.hint }}>Loading metrics…</p>}
        {comparisonError && <p style={{ color: theme.hint }}>Unable to load comparison metrics.</p>}
        {!loadingComparison && !comparisonError && !compareHosts.length && (
          <p style={{ color: theme.hint }}>Select at least one host to populate metrics.</p>
        )}
        {!loadingComparison && !comparisonError && compareHosts.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ background: 'rgba(255,255,255,0.05)' }}>
                <tr>
                  <th style={thStyle}>Host</th>
                  {compareCategories.map((category) => (
                    <th key={category} style={thStyle}>
                      {CATEGORY_OPTIONS.find((opt) => opt.id === category)?.label ?? category}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.map((row) => (
                  <tr key={row.hostId}>
                    <td style={tdStyle}>{row.hostName}</td>
                    {compareCategories.map((category) => (
                      <td key={category} style={tdStyle}>
                        {row.metrics[category] ?? '—'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function exportButton(theme: typeof palette[keyof typeof palette]): React.CSSProperties {
  return {
    background: theme.accent,
    border: 'none',
    color: '#0b0b0b',
    padding: '0.6rem 1rem',
    borderRadius: '0.75rem',
    cursor: 'pointer',
    fontWeight: 600
  };
}

function exportGhostButton(theme: typeof palette[keyof typeof palette]): React.CSSProperties {
  return {
    background: 'transparent',
    border: `1px solid ${theme.accent}`,
    color: theme.accent,
    padding: '0.6rem 1rem',
    borderRadius: '0.75rem',
    cursor: 'pointer',
    fontWeight: 600
  };
}

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '0.75rem',
  fontWeight: 600,
  borderBottom: '1px solid rgba(255,255,255,0.1)'
};

const tdStyle: React.CSSProperties = {
  padding: '0.75rem',
  borderBottom: '1px solid rgba(255,255,255,0.05)',
  fontSize: '0.95rem'
};
