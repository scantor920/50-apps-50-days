import { Router } from 'express';
import { getPnlRows } from '../lib/db';
import { periodSchema, resolvePeriodToDateRange } from '../lib/period';
import { getCached, sendValidationError, setCached } from './common';

const router = Router();

interface PnlRow {
  id: string;
  name: string;
  parentId: string | null;
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

  const cached = getCached<PnlRow[]>(req);
  if (cached) {
    res.json(cached);
    return;
  }

  const { period, glId } = parsed.data;
  const range = resolvePeriodToDateRange(period);
  const rows = (await getPnlRows(period, { glId }, range)) as PnlRow[];

  setCached(req, rows);
  res.json(rows);
});

export default router;
