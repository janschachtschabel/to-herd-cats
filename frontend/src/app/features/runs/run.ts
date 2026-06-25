/** Run + metrics-summary shapes (mirror the backend Run / metrics schemas). */

export interface Run {
  id: string;
  agent_id: string;
  status: string;
  result: Record<string, unknown>;
  metrics: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface MetricsSummary {
  total_runs: number;
  by_status: Record<string, number>;
  total_tokens: number;
  total_cost: number;
}
