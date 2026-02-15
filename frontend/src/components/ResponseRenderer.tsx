import { useState } from 'react';
import type { ChatResponse } from '../types';

interface ResponseRendererProps {
  response: ChatResponse | null;
}

/** Collapsible section wrapper. */
function CollapsibleSection({
  title,
  badge,
  testId,
  defaultOpen = true,
  children,
}: {
  title: string;
  badge?: string;
  testId: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="response-section" data-testid={testId}>
      <button
        className="section-toggle"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        data-testid={`${testId}-toggle`}
      >
        <span className="toggle-icon">{open ? '▼' : '▶'}</span>
        <h3>{title}{badge && <span className="section-badge">{badge}</span>}</h3>
      </button>
      {open && <div className="section-content">{children}</div>}
    </section>
  );
}

/** Copy-to-clipboard button. */
function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for environments without clipboard API
      setCopied(false);
    }
  };

  return (
    <button
      className="copy-button"
      onClick={handleCopy}
      title={`Copy ${label}`}
      data-testid={`copy-${label}`}
    >
      {copied ? '✓ Copied' : `📋 Copy`}
    </button>
  );
}

/**
 * Renders a structured chat response: answer, plan, actions, script, audit.
 * Supports collapsible sections and copy buttons.
 */
export function ResponseRenderer({ response }: ResponseRendererProps) {
  if (!response) return null;

  return (
    <div className="response" data-testid="response">
      {/* Answer — always visible */}
      <section className="response-answer" data-testid="response-answer">
        <h3>Answer</h3>
        <p>{response.answer}</p>
      </section>

      {/* Plan — collapsible */}
      {response.plan.length > 0 && (
        <CollapsibleSection
          title={`Plan`}
          badge={`${response.plan.length} step${response.plan.length !== 1 ? 's' : ''}`}
          testId="response-plan"
        >
          <ul>
            {response.plan.map((step, i) => (
              <li key={i} className={step.executed ? 'executed' : 'pending'}>
                <strong>{step.tool}</strong>
                {step.reasoning && <span className="reasoning"> — {step.reasoning}</span>}
                {step.executed && <span className="badge executed-badge">✓ Executed</span>}
              </li>
            ))}
          </ul>
        </CollapsibleSection>
      )}

      {/* Actions Taken — collapsible */}
      {response.actions_taken.length > 0 && (
        <CollapsibleSection
          title="Actions Taken"
          badge={`${response.actions_taken.length}`}
          testId="response-actions"
        >
          <ul>
            {response.actions_taken.map((action, i) => (
              <li key={i} className={action.success ? 'success' : 'error'}>
                <strong>{action.tool}</strong>
                {action.success
                  ? <span className="badge success-badge">✓ Success</span>
                  : <span className="badge error-badge">✗ {action.error}</span>
                }
              </li>
            ))}
          </ul>
        </CollapsibleSection>
      )}

      {/* Generated Script — collapsible with copy button */}
      {response.script && (
        <CollapsibleSection title="Generated Script" testId="response-script">
          <div className="script-container">
            <CopyButton text={response.script} label="script" />
            <pre><code>{response.script}</code></pre>
          </div>
        </CollapsibleSection>
      )}

      {/* Audit — collapsible with copy button on trace ID */}
      <CollapsibleSection title="Audit" testId="response-audit" defaultOpen={false}>
        <dl>
          <dt>Trace ID</dt>
          <dd>
            <code>{response.audit.trace_id}</code>
            <CopyButton text={response.audit.trace_id} label="trace-id" />
          </dd>
          <dt>Mode</dt>
          <dd><span className={`mode-badge mode-${response.audit.mode}`}>{response.audit.mode}</span></dd>
        </dl>
      </CollapsibleSection>
    </div>
  );
}
