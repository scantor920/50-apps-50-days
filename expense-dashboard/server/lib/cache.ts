import NodeCache from 'node-cache';

export const routeCache = new NodeCache({ stdTTL: 300, checkperiod: 60 });

export function getCacheKey(path: string, query: Record<string, unknown>): string {
  return `${path}:${JSON.stringify(query)}`;
}
