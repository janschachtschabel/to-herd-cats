/** Postbox item + response shapes (mirror the backend InboxItem schemas). */

export interface InboxItem {
  id: string;
  run_id: string;
  agent_id: string;
  type: string;
  payload: Record<string, unknown>;
  allowed_responses: string[];
  status: string;
  response: Record<string, unknown> | null;
  created_at: string;
}

export interface InboxResponse {
  action: string;
  content?: string;
  responded_by?: string;
}
