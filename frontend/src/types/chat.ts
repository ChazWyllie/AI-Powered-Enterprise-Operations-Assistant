/** Chat mode matching the backend's ChatMode enum. */
export type ChatMode = 'plan_only' | 'execute_safe';

/** Request payload for POST /chat. */
export interface ChatRequest {
  message: string;
  mode: ChatMode;
}

/** Audit metadata from the backend response. */
export interface AuditInfo {
  trace_id: string;
  mode: string;
}

/** Plan step from the orchestrator. */
export interface PlanStep {
  tool: string;
  args: Record<string, unknown>;
  reasoning: string;
  executed: boolean;
}

/** Action result from execute_safe mode. */
export interface ActionResult {
  tool: string;
  args: Record<string, unknown>;
  success: boolean;
  result?: Record<string, unknown>;
  error?: string;
}

/** Response payload from POST /chat. */
export interface ChatResponse {
  answer: string;
  plan: PlanStep[];
  actions_taken: ActionResult[];
  script: string | null;
  audit: AuditInfo;
}

/** Application error shape. */
export interface ApiError {
  detail: string;
  status: number;
}
