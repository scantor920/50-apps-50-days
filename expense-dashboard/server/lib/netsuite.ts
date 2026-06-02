/**
 * NetSuite REST API client using SuiteQL.
 *
 * Auth: Token-Based Authentication (TBA) with OAuth 1.0a HMAC-SHA256.
 * Docs: https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/section_157375785975.html
 *
 * Required env vars:
 *   NETSUITE_ACCOUNT_ID      e.g. "12345678" or "12345678_SB1" for sandbox
 *   NETSUITE_CONSUMER_KEY
 *   NETSUITE_CONSUMER_SECRET
 *   NETSUITE_TOKEN_ID
 *   NETSUITE_TOKEN_SECRET
 */

import crypto from 'crypto';

const ACCOUNT_ID      = process.env.NETSUITE_ACCOUNT_ID ?? '';
const CONSUMER_KEY    = process.env.NETSUITE_CONSUMER_KEY ?? '';
const CONSUMER_SECRET = process.env.NETSUITE_CONSUMER_SECRET ?? '';
const TOKEN_ID        = process.env.NETSUITE_TOKEN_ID ?? '';
const TOKEN_SECRET    = process.env.NETSUITE_TOKEN_SECRET ?? '';

const BASE_URL = `https://${ACCOUNT_ID.toLowerCase().replace('_', '-')}.suitetalk.api.netsuite.com/services/rest/query/v1/suiteql`;

/** Build an OAuth 1.0a Authorization header for a given URL + method. */
function buildOAuthHeader(method: string, url: string): string {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = crypto.randomBytes(16).toString('hex');

  const params: Record<string, string> = {
    oauth_consumer_key:     CONSUMER_KEY,
    oauth_nonce:            nonce,
    oauth_signature_method: 'HMAC-SHA256',
    oauth_timestamp:        timestamp,
    oauth_token:            TOKEN_ID,
    oauth_version:          '1.0',
  };

  // Signature base string
  const sortedParams = Object.keys(params)
    .sort()
    .map((k) => `${encodeURIComponent(k)}=${encodeURIComponent(params[k]!)}`)
    .join('&');

  const base = [
    method.toUpperCase(),
    encodeURIComponent(url),
    encodeURIComponent(sortedParams),
  ].join('&');

  const signingKey = `${encodeURIComponent(CONSUMER_SECRET)}&${encodeURIComponent(TOKEN_SECRET)}`;
  const signature = crypto
    .createHmac('sha256', signingKey)
    .update(base)
    .digest('base64');

  params['oauth_signature'] = signature;

  const headerValue = Object.keys(params)
    .map((k) => `${encodeURIComponent(k)}="${encodeURIComponent(params[k]!)}"`)
    .join(', ');

  return `OAuth realm="${ACCOUNT_ID}", ${headerValue}`;
}

export interface SuiteQLResponse<T> {
  items: T[];
  totalResults: number;
  hasMore: boolean;
  offset: number;
  count: number;
}

/**
 * Run a SuiteQL query.
 * NetSuite paginates at 1000 rows max per request; this helper fetches all pages.
 */
export async function suiteql<T extends Record<string, unknown>>(
  query: string,
  limit = 1000,
  offset = 0,
): Promise<T[]> {
  const url = `${BASE_URL}?limit=${limit}&offset=${offset}`;
  const authHeader = buildOAuthHeader('POST', BASE_URL);

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization:  authHeader,
      'Content-Type': 'application/json',
      'prefer':       'transient',
    },
    body: JSON.stringify({ q: query }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`NetSuite SuiteQL error ${response.status}: ${text}`);
  }

  const data = (await response.json()) as SuiteQLResponse<T>;
  const items: T[] = data.items ?? [];

  // Recurse for remaining pages
  if (data.hasMore) {
    const nextPage = await suiteql<T>(query, limit, offset + limit);
    return [...items, ...nextPage];
  }

  return items;
}

/** Test NetSuite connectivity — returns true if the account is reachable. */
export async function testNetSuiteConnection(): Promise<{ ok: boolean; detail: string }> {
  try {
    await suiteql('SELECT 1 AS ok FROM dual', 1);
    return { ok: true, detail: 'NetSuite connected' };
  } catch (err) {
    return { ok: false, detail: err instanceof Error ? err.message : 'NetSuite unreachable' };
  }
}
