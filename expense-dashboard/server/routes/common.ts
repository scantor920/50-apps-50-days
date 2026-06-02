import type { Request, Response } from 'express';
import { getCacheKey, routeCache } from '../lib/cache';

export function getCached<T>(req: Request): T | undefined {
  const key = getCacheKey(req.path, req.query as Record<string, unknown>);
  return routeCache.get<T>(key);
}

export function setCached<T>(req: Request, data: T): void {
  const key = getCacheKey(req.path, req.query as Record<string, unknown>);
  routeCache.set(key, data);
}

export function sendValidationError(res: Response, message: string): void {
  res.status(400).json({ error: message });
}
