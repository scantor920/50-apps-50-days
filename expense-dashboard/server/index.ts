import cors from 'cors';
import express from 'express';
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import { auditLogger } from './lib/audit';
import { testConnection } from './lib/db';
import costCentersRoute from './routes/costCenters';
import pnlRoute from './routes/pnl';
import transactionsRoute from './routes/transactions';
import trendRoute from './routes/trend';
import vendorsRoute from './routes/vendors';

const app = express();
const port = Number(process.env.PORT ?? 3001);

app.use(helmet());
app.use(
  cors({
    origin: process.env.CORS_ORIGIN?.split(',') ?? '*',
    methods: ['GET'],
  }),
);
app.use(
  rateLimit({
    windowMs: 60 * 1000,
    max: 300,
  }),
);
app.use(express.json());
app.use(auditLogger);

app.get('/api/health', async (_req, res) => {
  const db = await testConnection();
  const statusCode = db.ok ? 200 : 503;
  res.status(statusCode).json({ ok: db.ok, warehouse: db.detail });
});

app.use('/api/pnl', pnlRoute);
app.use('/api/cost-centers', costCentersRoute);
app.use('/api/vendors', vendorsRoute);
app.use('/api/transactions', transactionsRoute);
app.use('/api/trend', trendRoute);

app.use((error: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  const message = error instanceof Error ? error.message : 'Unknown server error';
  res.status(500).json({ error: message });
});

app.listen(port, () => {
  console.log(`Expense API running on :${port}`);
});
