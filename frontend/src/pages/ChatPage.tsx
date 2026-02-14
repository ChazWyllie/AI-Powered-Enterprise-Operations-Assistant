import { useState } from 'react';
import { ChatInput, ResponseRenderer, ErrorDisplay } from '../components';
import { sendChatMessage } from '../api';
import type { ChatMode, ChatResponse, ApiError } from '../types';

/**
 * Main chat page — prompt input, mode toggle, response rendering.
 */
export function ChatPage() {
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async (message: string, mode: ChatMode) => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await sendChatMessage({ message, mode });
      setResponse(result);
    } catch (err: unknown) {
      const apiError = err as ApiError;
      setError(apiError.detail ?? 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page chat-page">
      <h1>AI Enterprise Operations Assistant</h1>
      <p className="subtitle">
        AI-powered assistant for IBM Z / enterprise infrastructure operations
      </p>
      <ChatInput onSend={handleSend} isLoading={isLoading} />
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
