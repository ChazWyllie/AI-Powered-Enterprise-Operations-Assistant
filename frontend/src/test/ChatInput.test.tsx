import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ChatInput } from '../components/ChatInput';

function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

describe('ChatInput', () => {
  let mockOnSend: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnSend = vi.fn();
  });

  it('renders textarea, mode toggle, and send button', () => {
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={false} />);

    expect(screen.getByTestId('chat-textarea')).toBeInTheDocument();
    expect(screen.getByTestId('mode-toggle')).toBeInTheDocument();
    expect(screen.getByTestId('send-button')).toBeInTheDocument();
  });

  it('send request triggers fetch — calls onSend with message and mode', async () => {
    const user = userEvent.setup();
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={false} />);

    const textarea = screen.getByTestId('chat-textarea');
    await user.type(textarea, 'Show system status');
    await user.click(screen.getByTestId('send-button'));

    expect(mockOnSend).toHaveBeenCalledWith('Show system status', 'plan_only');
  });

  it('mode toggle affects payload — sends execute_safe when toggled', async () => {
    const user = userEvent.setup();
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={false} />);

    // Toggle to execute_safe
    const executeRadio = screen.getByLabelText('Execute Safe');
    await user.click(executeRadio);

    const textarea = screen.getByTestId('chat-textarea');
    await user.type(textarea, 'Check logs');
    await user.click(screen.getByTestId('send-button'));

    expect(mockOnSend).toHaveBeenCalledWith('Check logs', 'execute_safe');
  });

  it('defaults to plan_only mode', () => {
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={false} />);

    const planRadio = screen.getByLabelText('Plan Only') as HTMLInputElement;
    expect(planRadio.checked).toBe(true);
  });

  it('disables inputs when loading', () => {
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={true} />);

    expect(screen.getByTestId('chat-textarea')).toBeDisabled();
    expect(screen.getByTestId('send-button')).toBeDisabled();
  });

  it('does not send empty or whitespace-only messages', async () => {
    const user = userEvent.setup();
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={false} />);

    // Button should be disabled with empty textarea
    expect(screen.getByTestId('send-button')).toBeDisabled();

    // Type only spaces
    const textarea = screen.getByTestId('chat-textarea');
    await user.type(textarea, '   ');
    expect(screen.getByTestId('send-button')).toBeDisabled();
  });

  it('clears textarea after sending', async () => {
    const user = userEvent.setup();
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={false} />);

    const textarea = screen.getByTestId('chat-textarea') as HTMLTextAreaElement;
    await user.type(textarea, 'Hello');
    await user.click(screen.getByTestId('send-button'));

    expect(textarea.value).toBe('');
  });

  it('shows "Sending…" text when loading', () => {
    renderWithRouter(<ChatInput onSend={mockOnSend} isLoading={true} />);

    expect(screen.getByTestId('send-button')).toHaveTextContent('Sending…');
  });
});
