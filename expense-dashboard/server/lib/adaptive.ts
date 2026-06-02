/**
 * Workday Adaptive Planning REST API client.
 *
 * Auth: Basic authentication (username + password encoded as Base64).
 * Docs: https://doc.workday.com/adaptive-planning/en-us/integration/adaptive-suite-rest-api.html
 *
 * Required env vars:
 *   ADAPTIVE_BASE_URL      e.g. "https://api.adaptiveinsights.com/api/v32"
 *   ADAPTIVE_USERNAME      Adaptive service-account username
 *   ADAPTIVE_PASSWORD      Adaptive service-account password
 *   ADAPTIVE_CALLER_NAME   Identifies this integration in Adaptive audit logs
 *
 * The Adaptive API uses XML for its legacy endpoints and JSON for v32+ REST
 * endpoints. This client targets the REST/JSON surface only.
 */

const BASE_URL       = process.env.ADAPTIVE_BASE_URL ?? '';
const USERNAME       = process.env.ADAPTIVE_USERNAME ?? '';
const PASSWORD       = process.env.ADAPTIVE_PASSWORD ?? '';
const CALLER_NAME    = process.env.ADAPTIVE_CALLER_NAME ?? 'expense-dashboard';

function authHeader(): string {
  const encoded = Buffer.from(`${USERNAME}:${PASSWORD}`).toString('base64');
  return `Basic ${encoded}`;
}

async function adaptiveFetch<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  url.searchParams.set('callerName', CALLER_NAME);

  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: {
      Authorization: authHeader(),
      Accept:        'application/json',
    },
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Adaptive API error ${response.status}: ${text}`);
  }

  return response.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Budget shapes returned by Adaptive v32 REST API
// ---------------------------------------------------------------------------

export interface AdaptiveBudgetRow {
  accountCode:    string;   // GL account code matching NetSuite segment
  accountName:    string;
  dimensionCode:  string;   // cost center / department code
  periodLabel:    string;   // e.g. "Q1 2026"
  amount:         number;   // in the functional currency, full dollars
  version:        string;   // budget version name, e.g. "FY2026 Budget"
}

/**
 * Fetch budget amounts for a given version and period label.
 *
 * Maps to the Adaptive "exportData" endpoint which returns a flat array of
 * account × dimension × period rows.
 *
 * NOTE: Replace `/versions/{versionId}/data` with the correct path for your
 * Adaptive instance. The versionId for the current fiscal budget should be
 * stored in ADAPTIVE_BUDGET_VERSION_ID.
 */
export async function fetchAdaptiveBudget(
  periodLabel: string,
): Promise<AdaptiveBudgetRow[]> {
  const versionId = process.env.ADAPTIVE_BUDGET_VERSION_ID ?? '';

  // TODO: confirm the exact endpoint path with your Workday Adaptive admin.
  // The shape below is the standard Adaptive REST v32 export format.
  const data = await adaptiveFetch<{ rows: AdaptiveBudgetRow[] }>(
    `/versions/${versionId}/data`,
    { period: periodLabel, includeChildren: 'true' },
  );

  return data.rows ?? [];
}

/** Test Adaptive connectivity — returns true if the API is reachable. */
export async function testAdaptiveConnection(): Promise<{ ok: boolean; detail: string }> {
  try {
    const versionId = process.env.ADAPTIVE_BUDGET_VERSION_ID ?? '';
    if (!versionId) {
      return { ok: false, detail: 'ADAPTIVE_BUDGET_VERSION_ID not set' };
    }
    // A lightweight call — just fetch the version metadata, not full data
    await adaptiveFetch(`/versions/${versionId}`);
    return { ok: true, detail: 'Workday Adaptive connected' };
  } catch (err) {
    return { ok: false, detail: err instanceof Error ? err.message : 'Adaptive unreachable' };
  }
}
