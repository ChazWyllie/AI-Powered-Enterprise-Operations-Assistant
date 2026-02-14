import { useState, type FormEvent } from 'react';
import type { ChatMode } from '../types';

interface ChatInputProps {
  onSend: (message: string, mode: ChatMode) => void;
  isLoading: boolean;
}

/**
 * Chat input form with message textarea and mode toggle.
 */
export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [mode, setMode] = useState<ChatMode>('plan_only');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed, mode);
    setMessage('');
  };

  return (
    <form onSubmit={handleSubmit} className="chat-input" data-testid="chat-form">
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask about enterprise operations..."
        rows={3}
        disabled={isLoading}
        aria-label="Chat message"
        data-testid="chat-textarea"
      />
      <div className="chat-input-controls">
        <div className="mode-toggle" data-testid="mode-toggle">
          <label>
            <input
              type="radio"
              name="mode"
              value="plan_only"
              checked={mode === 'plan_only'}
              onChange={() => setMode('plan_only')}
              disabled={isLoading}
            />
            Plan Only
          </label>
          <label>
            <input
              type="radio"
              name="mode"
              value="execute_safe"
              checked={mode === 'execute_safe'}
              onChange={() => setMode('execute_safe')}
              disabled={isLoading}
            />
            Execute Safe
          </label>
        </div>
        <button type="submit" disabled={isLoading || !message.trim()} data-testid="send-button">
          {isLoading ? 'Sending…' : 'Send'}
        </button>
      </div>
    </form>
  );
}
