import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ErrorDisplay } from '../components/ErrorDisplay';

describe('ErrorDisplay', () => {
  it('renders nothing when error is null', () => {
    const { container } = render(<ErrorDisplay error={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders error message when provided', () => {
    render(<ErrorDisplay error="Something went wrong" />);
    const display = screen.getByTestId('error-display');
    expect(display).toHaveTextContent('Something went wrong');
  });

  it('has alert role for accessibility', () => {
    render(<ErrorDisplay error="Access denied" />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('shows rate limit hint', () => {
    render(<ErrorDisplay error="Rate limit exceeded" />);
    expect(screen.getByTestId('error-hint')).toHaveTextContent('wait a moment');
  });

  it('shows demo mode hint for 403', () => {
    render(<ErrorDisplay error="execute_safe is not available in public demo mode" />);
    expect(screen.getByTestId('error-hint')).toHaveTextContent('disabled in the public demo');
  });

  it('shows backend unreachable hint', () => {
    render(<ErrorDisplay error="Failed to fetch" />);
    expect(screen.getByTestId('error-hint')).toHaveTextContent('API server may be down');
  });

  it('shows policy violation hint', () => {
    render(<ErrorDisplay error="Policy blocked this command" />);
    expect(screen.getByTestId('error-hint')).toHaveTextContent('security policy');
  });

  it('shows request too large hint', () => {
    render(<ErrorDisplay error="Request body too large" />);
    expect(screen.getByTestId('error-hint')).toHaveTextContent('shorter prompt');
  });
});
