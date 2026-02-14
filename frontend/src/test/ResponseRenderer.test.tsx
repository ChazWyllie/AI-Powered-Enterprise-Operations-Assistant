import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ResponseRenderer } from '../components/ResponseRenderer';
import type { ChatResponse } from '../types';

const FULL_RESPONSE: ChatResponse = {
  answer: 'System is healthy with normal load.',
  plan: [
    {
      tool: 'get_system_status',
      args: {},
      reasoning: 'Check current metrics',
      executed: true,
    },
    {
      tool: 'get_logs',
      args: { source: 'syslog', tail: 20 },
      reasoning: 'Review recent entries',
      executed: false,
    },
  ],
  actions_taken: [
    { tool: 'get_system_status', args: {}, success: true, result: { cpu: 42 } },
  ],
  script: '#!/bin/bash\necho "hello"',
  audit: { trace_id: 'trace-abc-123', mode: 'plan_only' },
};

const MINIMAL_RESPONSE: ChatResponse = {
  answer: 'Checked status.',
  plan: [],
  actions_taken: [],
  script: null,
  audit: { trace_id: 'trace-xyz', mode: 'plan_only' },
};

describe('ResponseRenderer', () => {
  it('renders nothing when response is null', () => {
    const { container } = render(<ResponseRenderer response={null} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders answer section', () => {
    render(<ResponseRenderer response={FULL_RESPONSE} />);
    expect(screen.getByTestId('response-answer')).toHaveTextContent('System is healthy');
  });

  it('renders plan with correct step count', () => {
    render(<ResponseRenderer response={FULL_RESPONSE} />);
    const plan = screen.getByTestId('response-plan');
    expect(plan).toHaveTextContent('Plan (2 steps)');
    expect(plan).toHaveTextContent('get_system_status');
    expect(plan).toHaveTextContent('get_logs');
  });

  it('shows executed badge on executed steps', () => {
    render(<ResponseRenderer response={FULL_RESPONSE} />);
    expect(screen.getByTestId('response-plan')).toHaveTextContent('✓ Executed');
  });

  it('renders actions taken section', () => {
    render(<ResponseRenderer response={FULL_RESPONSE} />);
    const actions = screen.getByTestId('response-actions');
    expect(actions).toHaveTextContent('get_system_status');
    expect(actions).toHaveTextContent('✓ Success');
  });

  it('renders generated script', () => {
    render(<ResponseRenderer response={FULL_RESPONSE} />);
    const script = screen.getByTestId('response-script');
    expect(script).toHaveTextContent('#!/bin/bash');
    expect(script).toHaveTextContent('echo "hello"');
  });

  it('renders audit information', () => {
    render(<ResponseRenderer response={FULL_RESPONSE} />);
    const audit = screen.getByTestId('response-audit');
    expect(audit).toHaveTextContent('trace-abc-123');
    expect(audit).toHaveTextContent('plan_only');
  });

  it('handles missing fields gracefully — no plan, no actions, no script', () => {
    render(<ResponseRenderer response={MINIMAL_RESPONSE} />);

    expect(screen.getByTestId('response-answer')).toBeInTheDocument();
    expect(screen.queryByTestId('response-plan')).not.toBeInTheDocument();
    expect(screen.queryByTestId('response-actions')).not.toBeInTheDocument();
    expect(screen.queryByTestId('response-script')).not.toBeInTheDocument();
    expect(screen.getByTestId('response-audit')).toBeInTheDocument();
  });

  it('shows singular "step" for single plan item', () => {
    const singlePlan: ChatResponse = {
      ...MINIMAL_RESPONSE,
      plan: [{ tool: 'get_logs', args: {}, reasoning: 'test', executed: false }],
    };
    render(<ResponseRenderer response={singlePlan} />);
    expect(screen.getByTestId('response-plan')).toHaveTextContent('Plan (1 step)');
  });

  it('shows error badge for failed actions', () => {
    const failResponse: ChatResponse = {
      ...MINIMAL_RESPONSE,
      actions_taken: [
        { tool: 'run_command', args: {}, success: false, error: 'Command blocked' },
      ],
    };
    render(<ResponseRenderer response={failResponse} />);
    expect(screen.getByTestId('response-actions')).toHaveTextContent('✗ Command blocked');
  });
});
