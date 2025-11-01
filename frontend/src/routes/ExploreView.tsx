import { useMemo } from 'react';
import { useAppState } from '../state/appState';
import { palette } from '../styles/theme';

const sampleCategories = [
  { id: 'overview', label: 'Overview' },
  { id: 'memory', label: 'Memory' },
  { id: 'storage', label: 'Storage' },
  { id: 'cpu', label: 'CPU' },
  { id: 'gpu', label: 'GPU' },
  { id: 'software-services', label: 'Services' },
  { id: 'software-packages', label: 'Packages' }
];

export function ExploreView() {
  const { selectedHost, activeTheme, selectHost } = useAppState();
  const host = selectedHost ?? 'acer-hl';
  const theme = palette[activeTheme];
  const info = useMemo(
    () => ({
      host,
      summary: 'Assessment pending implementation.',
      categories: sampleCategories
    }),
    [host]
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
          This is a placeholder tree. API wiring will populate hosts & categories.
        </p>
        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {['acer-hl', 'omv-elbo', 'runpod-edge'].map((h) => (
            <button
              key={h}
              type="button"
              onClick={() => selectHost(h)}
              style={{
                textAlign: 'left',
                padding: '0.6rem 0.75rem',
                borderRadius: '0.5rem',
                border: '1px solid rgba(255,255,255,0.15)',
                background: h === host ? 'rgba(255,255,255,0.12)' : 'transparent',
                color: theme.text,
                cursor: 'pointer'
              }}
            >
              <strong>{h}</strong>
              <span style={{ display: 'block', fontSize: '0.75rem', color: theme.hint }}>Last seen · pending</span>
            </button>
          ))}
        </div>
      </div>
      <section style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <header>
          <h2 style={{ margin: 0, fontSize: '1.4rem' }}>{info.host}</h2>
          <p style={{ color: theme.hint }}>Exploratory view prototype — wiring to FastAPI coming soon.</p>
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
      </section>
    </div>
  );
}
