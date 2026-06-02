import { Router } from 'express';
import { getTrendRows } from '../lib/db';
import { periodSchema } from '../lib/period';
import { getCached, sendValidationError, setCached } from './common';

const router = Router();

interface TrendRow {
  period: string;
  actual: number;
  budget: number;
}

router.get('/', async (req, res) => {
  const parsed = periodSchema.safeParse(req.query);
  if (!parsed.success) {
    sendValidationError(res, parsed.error.flatten().formErrors.join(', '));
    return;
  }

  const cached = getCached<TrendRow[]>(req);
  if (cached) {
    res.json(cached);
    return;
  }

  const { period, glId, ccId, vendorId, quarters = 5 } = parsed.data;
  const trendRows = (await getTrendRows(period, { glId, ccId, vendorId }, quarters)) as TrendRow[];

  setCached(req, trendRows);
  res.json(trendRows);
});

export default router;
