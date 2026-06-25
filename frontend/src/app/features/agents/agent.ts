/** Agent shapes used by the cockpit UI (mirror the backend Agent schemas). */

export interface Agent {
  id: string;
  name: string;
  role?: string | null;
  goal?: string | null;
  status: string;
  created_at: string;
}

export interface AgentCreate {
  name: string;
  goal?: string;
}
