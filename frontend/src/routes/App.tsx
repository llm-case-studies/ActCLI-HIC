import { useEffect, useMemo } from 'react';
import { Routes, Route, Navigate, useLocation, Link } from 'react-router-dom';
import { useAppState } from '../state/appState';
import { palette, themeVars, type ThemeName } from '../styles/theme';
import { ExploreView } from './ExploreView';
import { CompareView } from './CompareView';
import { useHosts } from '../api/hooks';

const themeOptions: ThemeName[] = ['ledger', 'analyst', 'seminar'];

export default function App() {
  const location = useLocation();
  const { activeTheme, setMode, mode, setTheme, selectHost, selectedHost } = useAppState();
  const { data: hosts = [], isLoading } = useHosts();

  useEffect(() => {
    const vars = themeVars(activeTheme);
    Object.entries(vars).forEach(([key, value]) => {
      document.documentElement.style.setProperty(key, value);
    });
  }, [activeTheme]);

  useEffect(() => {
    if (location.pathname.startsWith('/compare') && mode !== 'compare') {
      setMode('compare');
    }
    if (location.pathname.startsWith('/explore') && mode !== 'explore') {
      setMode('explore');
    }
  }, [location.pathname, mode, setMode]);

  useEffect(() => {
    if (!selectedHost && hosts.length) {
      selectHost(String(hosts[0].id));
    }
  }, [hosts, selectHost, selectedHost]);

  const sidebarHosts = useMemo(() => hosts.slice(0, 5), [hosts]);

  return (
    <div className="app-shell" style={{ display: 'grid', gridTemplateColumns: '280px 1fr', minHeight: '100vh' }}>
      <aside
        style={{
          background: palette[activeTheme].sidebar,
          borderRight: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          flexDirection: 'column',
          padding: '1.5rem 1rem',
          gap: '1rem'
        }}
      >
        <div>
          <Link to="/explore">
            <h1 style={{ margin: 0, color: palette[activeTheme].brand, fontSize: '1.1rem', letterSpacing: '0.04em' }}>
              Hardware Insight Console
            </h1>
          </Link>
          <p style={{ color: palette[activeTheme].hint, marginTop: '0.25rem' }}>ActCLI ecosystem · SPA foundation</p>
        </div>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <Link to="/explore" style={linkStyle(location.pathname.startsWith('/explore'))}>
            Explore
          </Link>
          <Link to="/compare" style={linkStyle(location.pathname.startsWith('/compare'))}>
            Compare & Export
          </Link>
        </nav>
        <section>
          <p style={{ fontSize: '0.75rem', color: palette[activeTheme].hint, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Hosts
          </p>
          {isLoading ? (
            <p style={{ color: palette[activeTheme].hint }}>Loading…</p>
          ) : sidebarHosts.length ? (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
              {sidebarHosts.map((host) => (
                <li key={host.id} style={{ color: palette[activeTheme].text, opacity: 0.75 }}>
                  {host.hostname}
                </li>
              ))}
            </ul>
          ) : (
            <p style={{ color: palette[activeTheme].hint }}>No hosts yet</p>
          )}
        </section>
        <section>
          <label
            htmlFor="theme-select"
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              fontSize: '0.85rem',
              color: palette[activeTheme].hint
            }}
          >
            Theme
            <select
              id="theme-select"
              value={activeTheme}
              onChange={(event) => setTheme(event.target.value as ThemeName)}
              style={{
                appearance: 'none',
                background: 'rgba(0,0,0,0.25)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '0.5rem',
                padding: '0.55rem 0.75rem',
                color: palette[activeTheme].text,
                fontSize: '0.9rem'
              }}
            >
              {themeOptions.map((theme) => (
                <option key={theme} value={theme}>
                  {theme.charAt(0).toUpperCase() + theme.slice(1)}
                </option>
              ))}
            </select>
          </label>
        </section>
        <footer style={{ marginTop: 'auto', fontSize: '0.75rem', color: palette[activeTheme].hint }}>
          Theme tokens sourced from docs/actcli-theme-reference.md
        </footer>
      </aside>
      <main>
        <Routes>
          <Route path="/" element={<Navigate to="/explore" replace />} />
          <Route path="/explore" element={<ExploreView />} />
          <Route path="/compare" element={<CompareView />} />
          <Route path="*" element={<Navigate to="/explore" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function linkStyle(active: boolean): React.CSSProperties {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.6rem 0.75rem',
    borderRadius: '0.5rem',
    fontWeight: active ? 600 : 400,
    background: active ? 'rgba(255,255,255,0.08)' : 'transparent',
    border: active ? '1px solid rgba(255,255,255,0.25)' : '1px solid transparent',
    color: 'inherit'
  };
}
