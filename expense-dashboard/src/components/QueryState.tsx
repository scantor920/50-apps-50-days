import { ReactNode } from 'react';

interface QueryStateProps {
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
  children: ReactNode;
}

export function QueryState({ isLoading, isError, onRetry, children }: QueryStateProps) {
  if (isLoading) {
    return <div className="panel" style={{ padding: 18 }}>Loading data...</div>;
  }

  if (isError) {
    return (
      <div className="panel" style={{ padding: 18 }}>
        Could not load data.
        <button type="button" onClick={onRetry} style={{ marginLeft: 8 }}>
          Retry
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
