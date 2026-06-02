import { Router } from 'express';
import { getVendorRows } from '../lib/db';
import { periodSchema, resolvePeriodToDateRange } from '../lib/period';
import { getCached, sendValidationError, setCached } from './common';

const router = Router();

interface VendorRow {
  id: string;
  name: string;
  category: string;
  primaryGlId: string;
  primaryCcId: string;
  contractType: string;
  renewalDate: string | null;
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

  const cached = getCached<VendorRow[]>(req);
  if (cached) {
    res.json(cached);
    return;
  }

  const { period, glId, ccId } = parsed.data;
  const range = resolvePeriodToDateRange(period);
  const rows = (await getVendorRows(period, { glId, ccId }, range)) as VendorRow[];

  setCached(req, rows);
  res.json(rows);
});

export default router;
