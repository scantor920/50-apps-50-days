export type ISODate = string; // "2026-04-30"
export type Quarter = `Q${1 | 2 | 3 | 4} ${number}`; // "Q1 2026"

export interface GlAccount {
  id: string;
  name: string;
  parentId: string | null;
  level: number;
}

export interface PnlNode {
  id: string;
  name: string;
  parentId: string | null;
  actual: number;
  prior: number;
  budget: number;
  forecast?: number;
  children?: PnlNode[];
}

export interface CostCenter {
  id: string;
  name: string;
  lead: string;
  headcount: number;
  actual: number;
  prior: number;
  budget: number;
}

export interface Vendor {
  id: string;
  name: string;
  category: string;
  primaryGlId: string;
  primaryCcId: string;
  contractType: string;
  renewalDate: ISODate | null;
  actual: number;
  prior: number;
  budget: number;
}

export interface Transaction {
  id: string;
  date: ISODate;
  vendorId: string;
  vendorName: string;
  glId: string;
  ccId: string;
  memo: string;
  amount: number;
  status: 'Posted' | 'Pending' | 'Reclassed' | 'Voided';
  invoiceNumber: string;
}

export interface TrendPoint {
  period: Quarter;
  actual: number;
  budget: number;
}

export interface PeriodFilter {
  period: Quarter | 'YTD' | 'TTM';
  comparePeriod?: Quarter | null;
}

export interface DrillFilter {
  glId: string | null;
  ccId: string | null;
  vendorId: string | null;
}
