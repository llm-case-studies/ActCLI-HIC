import { create } from 'zustand';
import type { ThemeName } from '../styles/theme';

type HostId = string;
type CategoryId =
  | 'overview'
  | 'memory'
  | 'storage'
  | 'cpu'
  | 'gpu'
  | 'software-services'
  | 'software-packages'
  | 'users';

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
      const exists = state.compareHosts.includes(host);
      return {
        compareHosts: exists
          ? state.compareHosts.filter((h) => h !== host)
          : [...state.compareHosts, host],
        mode: 'compare'
      };
    }),
  setCompareCategories: (compareCategories) => set({ compareCategories, mode: 'compare' })
}));

export type { HostId, CategoryId, Mode };
