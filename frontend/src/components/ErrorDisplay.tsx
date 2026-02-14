interface ErrorDisplayProps {
  error: string | null;
}

/**
 * Renders an error message panel.
 */
export function ErrorDisplay({ error }: ErrorDisplayProps) {
  if (!error) return null;

  return (
    <div className="error-display" role="alert" data-testid="error-display">
      <strong>Error:</strong> {error}
    </div>
  );
}
