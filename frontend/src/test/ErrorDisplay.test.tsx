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
});
