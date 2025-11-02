import { create } from 'zustand';
import type { ThemeName } from '../styles/theme';

type HostId = string;
type CategoryId = 'overview' | 'memory' | 'storage' | 'cpu' | 'gpu' | 'software';

type Mode = 'explore' | 'compare';

interface AppState {
  mode: Mode;
  activeTheme: ThemeName;
  selectedHost: HostId | null;
  compareHosts: HostId[];
  compareCategories: CategoryId[];
  setMode: (mode: Mode) => void;
  setTheme: (theme: ThemeName) => void;
  selectHost: (host: HostId | null) => void;
  toggleCompareHost: (host: HostId) => void;
  setCompareCategories: (categories: CategoryId[]) => void;
}

export const useAppState = create<AppState>((set) => ({
  mode: 'explore',
  activeTheme: 'ledger',
  selectedHost: null,
  compareHosts: [],
  compareCategories: ['overview', 'memory', 'storage'],
  setMode: (mode) => set({ mode }),
  setTheme: (activeTheme) => set({ activeTheme }),
  selectHost: (selectedHost) => set({ selectedHost, mode: 'explore' }),
  toggleCompareHost: (host) =>
    set((state) => {
      const hostId = String(host);
      const exists = state.compareHosts.includes(hostId);
      return {
        compareHosts: exists
          ? state.compareHosts.filter((h) => h !== hostId)
          : [...state.compareHosts, hostId],
        mode: 'compare'
      };
    }),
  setCompareCategories: (compareCategories) => set({ compareCategories, mode: 'compare' })
}));

export type { HostId, CategoryId, Mode };
