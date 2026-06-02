import { Router } from 'express';
import { getTransactionsPage } from '../lib/db';
import { periodSchema, resolvePeriodToDateRange } from '../lib/period';
import { getCached, sendValidationError, setCached } from './common';

const router = Router();

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

interface TransactionPage {
  rows: TransactionRow[];
  totalRows: number;
  page: number;
  pageSize: number;
}

router.get('/', async (req, res) => {
  const parsed = periodSchema.safeParse(req.query);
  if (!parsed.success) {
    sendValidationError(res, parsed.error.flatten().formErrors.join(', '));
    return;
  }

  const cached = getCached<TransactionPage>(req);
  if (cached) {
    res.json(cached);
    return;
  }

  const { period, glId, ccId, vendorId, page = 1, pageSize = 200 } = parsed.data;
  const range = resolvePeriodToDateRange(period);
  const payload = (await getTransactionsPage({ glId, ccId, vendorId }, range, page, pageSize)) as TransactionPage;

  setCached(req, payload);
  res.json(payload);
});

export default router;
