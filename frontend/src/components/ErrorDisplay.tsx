interface ErrorDisplayProps {
  error: string | null;
}

/** Map error messages to user-friendly descriptions. */
function getErrorInfo(error: string): { icon: string; title: string; hint: string } {
  const lower = error.toLowerCase();

  if (lower.includes('rate limit')) {
    return { icon: '⏱️', title: 'Rate Limited', hint: 'Too many requests — wait a moment and try again.' };
  }
  if (lower.includes('public demo') || lower.includes('403')) {
    return { icon: '🔒', title: 'Demo Mode Restricted', hint: 'Execute mode is disabled in the public demo.' };
  }
  if (lower.includes('too large') || lower.includes('413')) {
    return { icon: '📏', title: 'Request Too Large', hint: 'Your message is too long — try a shorter prompt.' };
  }
  if (lower.includes('network') || lower.includes('fetch') || lower.includes('econnrefused')) {
    return { icon: '🔌', title: 'Backend Unreachable', hint: 'The API server may be down — check if it is running.' };
  }
  if (lower.includes('policy') || lower.includes('blocked') || lower.includes('denied')) {
    return { icon: '🛡️', title: 'Policy Violation', hint: 'The security policy blocked this request.' };
  }
  return { icon: '⚠️', title: 'Error', hint: '' };
}

/**
 * Renders a contextual error message panel with icon and recovery hints.
 */
export function ErrorDisplay({ error }: ErrorDisplayProps) {
  if (!error) return null;

  const { icon, title, hint } = getErrorInfo(error);

  return (
    <div className="error-display" role="alert" data-testid="error-display">
      <div className="error-header">
        <span className="error-icon">{icon}</span>
        <strong>{title}:</strong> {error}
      </div>
      {hint && <p className="error-hint" data-testid="error-hint">{hint}</p>}
    </div>
  );
}
