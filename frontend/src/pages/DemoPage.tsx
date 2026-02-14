import { useState } from 'react';
import { ChatInput, ResponseRenderer, ErrorDisplay } from '../components';
import { sendChatMessage } from '../api';
import type { ChatResponse, ApiError } from '../types';

const DEMO_PROMPTS = [
  { label: 'System Status', message: 'Show me the current system status and CPU usage' },
  { label: 'View Logs', message: 'Show me the last 20 syslog entries' },
  { label: 'List Files', message: 'List files in the simulator directory' },
  { label: 'Error Analysis', message: 'Check error logs and show recent issues' },
  { label: 'Security Test', message: 'Try to run rm -rf / on the system' },
  { label: 'Config Update', message: 'Update the log level to debug' },
];

/**
 * Demo page with preset prompts and guided experience.
 */
export function DemoPage() {
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (message: string) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await sendChatMessage({ message, mode: 'plan_only' });
      setResponse(result);
    } catch (err: unknown) {
      const apiError = err as ApiError;
      setError(apiError.detail ?? 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page demo-page">
      <h1>Interactive Demo</h1>
      <p className="subtitle">
        Try these preset prompts to see the assistant in action. All requests use{' '}
        <strong>plan_only</strong> mode — no commands are executed.
      </p>

      <h2>Preset Prompts</h2>
      <div className="demo-prompts" data-testid="demo-prompts">
        {DEMO_PROMPTS.map((prompt, i) => (
          <button
            key={i}
            className="demo-prompt-button"
            onClick={() => handleSend(prompt.message)}
            disabled={isLoading}
            data-testid={`demo-prompt-${i}`}
          >
            <strong>{prompt.label}</strong>
            <span>{prompt.message}</span>
          </button>
        ))}
      </div>

      <h2>Or ask your own question</h2>
      <ChatInput onSend={(msg) => handleSend(msg)} isLoading={isLoading} />

      {isLoading && (
        <div className="loading" data-testid="loading-indicator">
          Processing your request…
        </div>
      )}
      <ErrorDisplay error={error} />
      <ResponseRenderer response={response} />
    </div>
  );
}
