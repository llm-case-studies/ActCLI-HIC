export const palette = {
  ledger: {
    background: '#1E2A3A',
    header: '#0D639C',
    sidebar: '#213245',
    surface: '#1B2736',
    brand: '#66C2FF',
    hint: '#9FB7C8',
    text: '#E0E0E0',
    accent: '#F05A28',
    accentHover: '#FFD166'
  },
  analyst: {
    background: '#282C34',
    header: '#00A6A6',
    sidebar: '#22303A',
    surface: '#1F242B',
    brand: '#00D1D1',
    hint: '#C0C8CF',
    text: '#F8F8F2',
    accent: '#F05A28',
    accentHover: '#FFD166'
  },
  seminar: {
    background: '#3C3C3C',
    header: '#6A829B',
    sidebar: '#323232',
    surface: '#2C2C2C',
    brand: '#D4AC87',
    hint: '#D0D0D0',
    text: '#F3F3F3',
    accent: '#F05A28',
    accentHover: '#FFD166'
  }
} as const;

export type ThemeName = keyof typeof palette;

export const defaultTheme: ThemeName = 'ledger';

export const themeVars = (name: ThemeName = defaultTheme) => {
  const scheme = palette[name];
  return {
    '--hic-bg': scheme.background,
    '--hic-header': scheme.header,
    '--hic-sidebar': scheme.sidebar,
    '--hic-surface': scheme.surface,
    '--hic-brand': scheme.brand,
    '--hic-text': scheme.text,
    '--hic-hint': scheme.hint,
    '--hic-accent': scheme.accent,
    '--hic-accent-hover': scheme.accentHover
  } as Record<string, string>;
};
