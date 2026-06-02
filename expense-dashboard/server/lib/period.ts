import { z } from 'zod';

export const periodSchema = z.object({
  period: z.string().min(1),
  comparePeriod: z.string().optional(),
  glId: z.string().optional(),
  ccId: z.string().optional(),
  vendorId: z.string().optional(),
  quarters: z.coerce.number().int().positive().max(12).optional(),
  page: z.coerce.number().int().positive().optional(),
  pageSize: z.coerce.number().int().positive().max(1000).optional(),
});

export interface DateRange {
  startDate: string;
  endDate: string;
  priorStartDate: string;
  priorEndDate: string;
}

function quarterToRange(period: string): DateRange {
  const match = /^Q([1-4])\s(\d{4})$/.exec(period);
  if (!match) {
    throw new Error(`Invalid quarter period: ${period}`);
  }

  const quarter = Number(match[1]);
  const year = Number(match[2]);
  const startMonth = (quarter - 1) * 3;

  const startDate = new Date(Date.UTC(year, startMonth, 1));
  const endDate = new Date(Date.UTC(year, startMonth + 3, 0));
  const priorStartDate = new Date(Date.UTC(year - 1, startMonth, 1));
  const priorEndDate = new Date(Date.UTC(year - 1, startMonth + 3, 0));

  return {
    startDate: startDate.toISOString().slice(0, 10),
    endDate: endDate.toISOString().slice(0, 10),
    priorStartDate: priorStartDate.toISOString().slice(0, 10),
    priorEndDate: priorEndDate.toISOString().slice(0, 10),
  };
}

export function resolvePeriodToDateRange(period: string): DateRange {
  if (period === 'YTD') {
    const now = new Date();
    const year = now.getUTCFullYear();
    return {
      startDate: `${year}-01-01`,
      endDate: now.toISOString().slice(0, 10),
      priorStartDate: `${year - 1}-01-01`,
      priorEndDate: `${year - 1}-${String(now.getUTCMonth() + 1).padStart(2, '0')}-${String(now.getUTCDate()).padStart(2, '0')}`,
    };
  }

  if (period === 'TTM') {
    const now = new Date();
    const endDate = now.toISOString().slice(0, 10);
    const start = new Date(now);
    start.setUTCFullYear(start.getUTCFullYear() - 1);
    start.setUTCDate(start.getUTCDate() + 1);
    const priorEnd = new Date(start);
    priorEnd.setUTCDate(priorEnd.getUTCDate() - 1);
    const priorStart = new Date(priorEnd);
    priorStart.setUTCFullYear(priorStart.getUTCFullYear() - 1);
    priorStart.setUTCDate(priorStart.getUTCDate() + 1);
    return {
      startDate: start.toISOString().slice(0, 10),
      endDate,
      priorStartDate: priorStart.toISOString().slice(0, 10),
      priorEndDate: priorEnd.toISOString().slice(0, 10),
    };
  }

  return quarterToRange(period);
}
