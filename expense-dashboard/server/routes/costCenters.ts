import { Router } from 'express';
import { getCostCenterRows } from '../lib/db';
import { periodSchema, resolvePeriodToDateRange } from '../lib/period';
import { getCached, sendValidationError, setCached } from './common';

const router = Router();

interface CostCenterRow {
  id: string;
  name: string;
  lead: string;
  headcount: number;
  actual: number;
  prior: number;
  budget: number;
}

router.get('/', async (req, res) => {
  const parsed = periodSchema.safeParse(req.query);
  if (!parsed.success) {
    sendValidationError(res, parsed.error.flatten().formErrors.join(', '));
    return;
  }

  const cached = getCached<CostCenterRow[]>(req);
  if (cached) {
    res.json(cached);
    return;
  }

  const { period, glId } = parsed.data;
  const range = resolvePeriodToDateRange(period);
  const rows = (await getCostCenterRows(period, { glId }, range)) as CostCenterRow[];

  setCached(req, rows);
  res.json(rows);
});

export default router;
