import { useMemo } from 'react';
import { useAppState } from '../state/appState';
import { palette } from '../styles/theme';

const mockHosts = ['acer-hl', 'omv-elbo', 'ionos-2c4g'];
const mockCategories = [
  { id: 'memory', label: 'Memory' },
  { id: 'storage', label: 'Storage' },
  { id: 'cpu', label: 'CPU' }
];

export function CompareView() {
  const { activeTheme, compareHosts, toggleCompareHost, compareCategories, setCompareCategories } = useAppState();
  const theme = palette[activeTheme];

  const table = useMemo(() => {
    if (!compareHosts.length) return [];
    return compareHosts.map((host) => ({
      host,
      memory: '32 GB / 64 GB max',
      storage: '2 × NVMe (1 free)',
      cpu: '16c / 32t'
    }));
  }, [compareHosts]);

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
            {mockHosts.map((host) => {
              const active = compareHosts.includes(host);
              return (
                <label key={host} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <input type="checkbox" checked={active} onChange={() => toggleCompareHost(host)} />
                  <span>{host}</span>
                </label>
              );
            })}
          </div>
        </div>
        <div style={{ background: theme.surface, borderRadius: '1rem', padding: '1.25rem' }}>
          <h3 style={{ marginTop: 0 }}>Categories</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {mockCategories.map((category) => {
              const active = compareCategories.includes(category.id as never);
              return (
                <label key={category.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <input
                    type="checkbox"
                    checked={active}
                    onChange={() => {
                      const next = active
                        ? compareCategories.filter((id) => id !== (category.id as never))
                        : [...compareCategories, category.id as never];
                      setCompareCategories(next as never);
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
        {!table.length ? (
          <p style={{ color: theme.hint }}>Select at least one host to populate metrics.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead style={{ background: 'rgba(255,255,255,0.05)' }}>
                <tr>
                  <th style={thStyle}>Host</th>
                  <th style={thStyle}>Memory</th>
                  <th style={thStyle}>Storage</th>
                  <th style={thStyle}>CPU</th>
                </tr>
              </thead>
              <tbody>
                {table.map((row) => (
                  <tr key={row.host}>
                    <td style={tdStyle}>{row.host}</td>
                    <td style={tdStyle}>{row.memory}</td>
                    <td style={tdStyle}>{row.storage}</td>
                    <td style={tdStyle}>{row.cpu}</td>
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
