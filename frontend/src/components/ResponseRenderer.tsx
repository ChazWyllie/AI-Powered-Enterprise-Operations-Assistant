import type { ChatResponse } from '../types';

interface ResponseRendererProps {
  response: ChatResponse | null;
}

/**
 * Renders a structured chat response: answer, plan, actions, script, audit.
 * Handles missing/empty fields gracefully.
 */
export function ResponseRenderer({ response }: ResponseRendererProps) {
  if (!response) return null;

  return (
    <div className="response" data-testid="response">
      {/* Answer */}
      <section className="response-answer" data-testid="response-answer">
        <h3>Answer</h3>
        <p>{response.answer}</p>
      </section>

      {/* Plan */}
      {response.plan.length > 0 && (
        <section className="response-plan" data-testid="response-plan">
          <h3>Plan ({response.plan.length} step{response.plan.length !== 1 ? 's' : ''})</h3>
          <ul>
            {response.plan.map((step, i) => (
              <li key={i} className={step.executed ? 'executed' : 'pending'}>
                <strong>{step.tool}</strong>
                {step.reasoning && <span className="reasoning"> — {step.reasoning}</span>}
                {step.executed && <span className="badge executed-badge">✓ Executed</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Actions Taken */}
      {response.actions_taken.length > 0 && (
        <section className="response-actions" data-testid="response-actions">
          <h3>Actions Taken</h3>
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
        </section>
      )}

      {/* Generated Script */}
      {response.script && (
        <section className="response-script" data-testid="response-script">
          <h3>Generated Script</h3>
          <pre><code>{response.script}</code></pre>
        </section>
      )}

      {/* Audit */}
      <section className="response-audit" data-testid="response-audit">
        <h3>Audit</h3>
        <dl>
          <dt>Trace ID</dt>
          <dd><code>{response.audit.trace_id}</code></dd>
          <dt>Mode</dt>
          <dd>{response.audit.mode}</dd>
        </dl>
      </section>
    </div>
  );
}
