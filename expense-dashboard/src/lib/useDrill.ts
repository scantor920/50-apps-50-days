import { create } from 'zustand';
import type { DrillFilter, PeriodFilter } from '../data/types';

interface DrillStore {
  period: PeriodFilter;
  filter: DrillFilter;
  setPeriod: (p: PeriodFilter) => void;
  setFilter: (next: Partial<DrillFilter>) => void;
  clearFilters: () => void;
}

export const useDrill = create<DrillStore>((set) => ({
  period: { period: 'Q1 2026' },
  filter: { glId: null, ccId: null, vendorId: null },
  setPeriod: (period) => set({ period }),
  setFilter: (next) => set((s) => ({ filter: { ...s.filter, ...next } })),
  clearFilters: () => set({ filter: { glId: null, ccId: null, vendorId: null } }),
}));
