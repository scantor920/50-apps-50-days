export interface AuthContextValue {
  token: string | null;
  userId: string;
  displayName: string;
}

export function useAuth(): AuthContextValue {
  // TODO: Replace this stub with real auth integration.
  return {
    token: null,
    userId: 'local-user',
    displayName: 'Analyst',
  };
}
