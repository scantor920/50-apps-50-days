import type { NextFunction, Request, Response } from 'express';

export function auditLogger(req: Request, res: Response, next: NextFunction): void {
  const start = Date.now();
  const userId = (req.headers['x-user-id'] as string | undefined) ?? 'unknown';

  res.on('finish', () => {
    const responseMs = Date.now() - start;
    const payload = {
      userId,
      endpoint: req.path,
      filterParams: req.query,
      responseMs,
      statusCode: res.statusCode,
      at: new Date().toISOString(),
    };
    console.log(JSON.stringify(payload));
  });

  next();
}
