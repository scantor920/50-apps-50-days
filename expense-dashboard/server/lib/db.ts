import fs from 'fs';
import path from 'path';

export interface DrillFilter {
  glId?: string;
  ccId?: string;
  vendorId?: string;
}

export interface DateRange {
  startDate: string;
  endDate: string;
  priorStartDate: string;
  priorEndDate: string;
}

interface GlAccountRow {
  id: string;
  name: string;
  parentId: string | null;
  level: number;
}

interface CostCenterRow {
  id: string;
  name: string;
  lead: string;
  headcount: number;
}

interface VendorRow {
  id: string;
  name: string;
  category: string;
  primaryGlId: string;
  primaryCcId: string;
  contractType: string;
  renewalDate: string | null;
}

interface TransactionRow {
  id: string;
  date: string;
  vendorId: string;
  vendorName: string;
  glId: string;
  ccId: string;
  memo: string;
  amount: number;
  status: 'Posted' | 'Pending' | 'Reclassed' | 'Voided';
  invoiceNumber: string;
}

interface BudgetRow {
  period: string;
  glId: string;
  ccId: string;
  vendorId: string;
  amount: number;
}

interface CsvDataset {
  glAccounts: GlAccountRow[];
  costCenters: CostCenterRow[];
  vendors: VendorRow[];
  transactions: TransactionRow[];
  budgets: BudgetRow[];
}

let cachedDataset: CsvDataset | null = null;
let cachedSignature = '';

function dataRoot(): string {
  return process.env.CSV_DATA_DIR
    ? path.resolve(process.env.CSV_DATA_DIR)
    : path.resolve(process.cwd(), 'server', 'data');
}

function fileSignature(fileName: string): string {
  const fullPath = path.join(dataRoot(), fileName);
  const stats = fs.statSync(fullPath);
  return `${fileName}:${stats.mtimeMs}:${stats.size}`;
}

function datasetSignature(): string {
  const files = [
    'gl_accounts.csv',
    'cost_centers.csv',
    'vendors.csv',
    'transactions.csv',
    'budgets.csv',
  ];
  return files.map(fileSignature).join('|');
}

function parseCsvLine(line: string): string[] {
  const out: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (ch === ',' && !inQuotes) {
      out.push(current);
      current = '';
      continue;
    }
    current += ch;
  }
  out.push(current);
  return out.map((v) => v.trim());
}

function readCsv(fileName: string): Record<string, string>[] {
  const fullPath = path.join(dataRoot(), fileName);
  const content = fs.readFileSync(fullPath, 'utf8').replace(/^\uFEFF/, '');
  const lines = content
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length === 0) {
    return [];
  }

  const header = parseCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line);
    const row: Record<string, string> = {};
    header.forEach((key, idx) => {
      row[key] = values[idx] ?? '';
    });
    return row;
  });
}

function asNumber(value: string): number {
  const cleaned = value.replace(/[$,]/g, '');
  const num = Number(cleaned);
  return Number.isFinite(num) ? num : 0;
}

function loadDataset(): CsvDataset {
  const signature = datasetSignature();
  if (cachedDataset && cachedSignature === signature) {
    return cachedDataset;
  }

  const glAccounts: GlAccountRow[] = readCsv('gl_accounts.csv').map((r) => ({
    id: r.id,
    name: r.name,
    parentId: r.parentId || null,
    level: Math.trunc(asNumber(r.level)),
  }));

  const costCenters: CostCenterRow[] = readCsv('cost_centers.csv').map((r) => ({
    id: r.id,
    name: r.name,
    lead: r.lead,
    headcount: Math.trunc(asNumber(r.headcount)),
  }));

  const vendors: VendorRow[] = readCsv('vendors.csv').map((r) => ({
    id: r.id,
    name: r.name,
    category: r.category,
    primaryGlId: r.primaryGlId,
    primaryCcId: r.primaryCcId,
    contractType: r.contractType,
    renewalDate: r.renewalDate || null,
  }));

  const transactions: TransactionRow[] = readCsv('transactions.csv').map((r) => ({
    id: r.id,
    date: r.date,
    vendorId: r.vendorId,
    vendorName: r.vendorName,
    glId: r.glId,
    ccId: r.ccId,
    memo: r.memo,
    amount: asNumber(r.amount),
    status: (['Posted', 'Pending', 'Reclassed', 'Voided'].includes(r.status)
      ? r.status
      : 'Pending') as TransactionRow['status'],
    invoiceNumber: r.invoiceNumber,
  }));

  const budgets: BudgetRow[] = readCsv('budgets.csv').map((r) => ({
    period: r.period,
    glId: r.glId,
    ccId: r.ccId,
    vendorId: r.vendorId,
    amount: asNumber(r.amount),
  }));

  cachedDataset = { glAccounts, costCenters, vendors, transactions, budgets };
  cachedSignature = signature;
  return cachedDataset;
}

function inRange(date: string, start: string, end: string): boolean {
  return date >= start && date <= end;
}

function matchesFilter(txn: { glId: string; ccId: string; vendorId: string }, filter: DrillFilter): boolean {
  if (filter.glId && txn.glId !== filter.glId) return false;
  if (filter.ccId && txn.ccId !== filter.ccId) return false;
  if (filter.vendorId && txn.vendorId !== filter.vendorId) return false;
  return true;
}

function sumBudgetK(
  budgets: BudgetRow[],
  period: string,
  filter: DrillFilter,
  scope?: { glId?: string; ccId?: string; vendorId?: string },
): number {
  return budgets
    .filter((b) => b.period === period)
    .filter((b) => (!scope?.glId || b.glId === scope.glId))
    .filter((b) => (!scope?.ccId || b.ccId === scope.ccId))
    .filter((b) => (!scope?.vendorId || b.vendorId === scope.vendorId))
    .filter((b) => (!filter.glId || b.glId === filter.glId))
    .filter((b) => (!filter.ccId || b.ccId === filter.ccId))
    .filter((b) => (!filter.vendorId || b.vendorId === filter.vendorId))
    .reduce((sum, b) => sum + b.amount / 1000, 0);
}

function quarterLabelFromDate(date: string): string {
  const d = new Date(date);
  const quarter = Math.ceil((d.getUTCMonth() + 1) / 3);
  return `Q${quarter} ${d.getUTCFullYear()}`;
}

function currentQuarterLabel(): string {
  const now = new Date();
  const q = Math.ceil((now.getUTCMonth() + 1) / 3);
  return `Q${q} ${now.getUTCFullYear()}`;
}

function shiftQuarter(label: string, delta: number): string {
  const match = /^Q([1-4])\s(\d{4})$/.exec(label);
  if (!match) return label;
  let q = Number(match[1]);
  let y = Number(match[2]);
  q += delta;
  while (q > 4) {
    q -= 4;
    y += 1;
  }
  while (q < 1) {
    q += 4;
    y -= 1;
  }
  return `Q${q} ${y}`;
}

export async function testConnection(): Promise<{ ok: boolean; detail: string }> {
  try {
    loadDataset();
    return { ok: true, detail: `CSV data loaded from ${dataRoot()}` };
  } catch (error) {
    const detail = error instanceof Error ? error.message : 'Unknown CSV loading error';
    return { ok: false, detail };
  }
}

export async function getPnlRows(period: string, filter: DrillFilter, range: DateRange) {
  const data = loadDataset();
  const rowsById = new Map(
    data.glAccounts.map((gl) => [
      gl.id,
      {
        id: gl.id,
        name: gl.name,
        parentId: gl.parentId,
        actual: 0,
        prior: 0,
        budget: 0,
      },
    ]),
  );

  for (const tx of data.transactions) {
    if (!matchesFilter(tx, filter)) continue;
    const row = rowsById.get(tx.glId);
    if (!row) continue;
    if (inRange(tx.date, range.startDate, range.endDate)) row.actual += tx.amount / 1000;
    if (inRange(tx.date, range.priorStartDate, range.priorEndDate)) row.prior += tx.amount / 1000;
  }

  for (const row of rowsById.values()) {
    row.budget = sumBudgetK(data.budgets, period, filter, { glId: row.id });
  }

  return [...rowsById.values()]
    .filter((row) => !filter.glId || row.id === filter.glId)
    .sort((a, b) => a.id.localeCompare(b.id));
}

export async function getCostCenterRows(period: string, filter: DrillFilter, range: DateRange) {
  const data = loadDataset();
  const rowsById = new Map(
    data.costCenters.map((cc) => [
      cc.id,
      {
        id: cc.id,
        name: cc.name,
        lead: cc.lead,
        headcount: cc.headcount,
        actual: 0,
        prior: 0,
        budget: 0,
      },
    ]),
  );

  for (const tx of data.transactions) {
    if (!matchesFilter(tx, filter)) continue;
    const row = rowsById.get(tx.ccId);
    if (!row) continue;
    if (inRange(tx.date, range.startDate, range.endDate)) row.actual += tx.amount / 1000;
    if (inRange(tx.date, range.priorStartDate, range.priorEndDate)) row.prior += tx.amount / 1000;
  }

  for (const row of rowsById.values()) {
    row.budget = sumBudgetK(data.budgets, period, filter, { ccId: row.id });
  }

  return [...rowsById.values()]
    .filter((row) => !filter.ccId || row.id === filter.ccId)
    .sort((a, b) => b.actual - a.actual);
}

export async function getVendorRows(period: string, filter: DrillFilter, range: DateRange) {
  const data = loadDataset();
  const rowsById = new Map(
    data.vendors.map((v) => [
      v.id,
      {
        id: v.id,
        name: v.name,
        category: v.category,
        primaryGlId: v.primaryGlId,
        primaryCcId: v.primaryCcId,
        contractType: v.contractType,
        renewalDate: v.renewalDate,
        actual: 0,
        prior: 0,
        budget: 0,
      },
    ]),
  );

  for (const tx of data.transactions) {
    if (!matchesFilter(tx, filter)) continue;
    const row = rowsById.get(tx.vendorId);
    if (!row) continue;
    if (inRange(tx.date, range.startDate, range.endDate)) row.actual += tx.amount / 1000;
    if (inRange(tx.date, range.priorStartDate, range.priorEndDate)) row.prior += tx.amount / 1000;
  }

  for (const row of rowsById.values()) {
    row.budget = sumBudgetK(data.budgets, period, filter, { vendorId: row.id });
  }

  return [...rowsById.values()]
    .filter((row) => !filter.vendorId || row.id === filter.vendorId)
    .sort((a, b) => b.actual - a.actual);
}

export async function getTransactionsPage(
  filter: DrillFilter,
  range: DateRange,
  page: number,
  pageSize: number,
) {
  const data = loadDataset();
  const filtered = data.transactions
    .filter((tx) => inRange(tx.date, range.startDate, range.endDate))
    .filter((tx) => matchesFilter(tx, filter))
    .sort((a, b) => b.date.localeCompare(a.date));

  const start = (page - 1) * pageSize;
  const rows = filtered.slice(start, start + pageSize);

  return {
    rows,
    totalRows: filtered.length,
    page,
    pageSize,
  };
}

export async function getTrendRows(
  period: string,
  filter: DrillFilter,
  quarters: number,
) {
  const data = loadDataset();
  const anchor = /^Q[1-4]\s\d{4}$/.test(period) ? period : currentQuarterLabel();
  const labels: string[] = [];
  for (let i = quarters - 1; i >= 0; i -= 1) {
    labels.push(shiftQuarter(anchor, -i));
  }

  const actualByQuarter = new Map<string, number>();
  for (const tx of data.transactions) {
    if (!matchesFilter(tx, filter)) continue;
    const q = quarterLabelFromDate(tx.date);
    if (!labels.includes(q)) continue;
    actualByQuarter.set(q, (actualByQuarter.get(q) ?? 0) + tx.amount / 1000);
  }

  return labels.map((label) => ({
    period: label,
    actual: actualByQuarter.get(label) ?? 0,
    budget: sumBudgetK(data.budgets, label, filter),
  }));
}
