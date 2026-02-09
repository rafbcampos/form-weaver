import type { InterviewSchema } from "./schema";
import type { UIBlock } from "./ui-blocks";

export interface StartRequest {
  schema: InterviewSchema;
  initial_data?: Record<string, unknown>;
}

export interface StartResponse {
  session_id: string;
  blocks: UIBlock[];
  is_complete: boolean;
  current_data: Record<string, unknown>;
}

export interface SubmitRequest {
  type: "form" | "message";
  data?: Record<string, unknown>;
  text?: string;
}

export interface SubmitResponse {
  blocks: UIBlock[];
  is_complete: boolean;
  current_data: Record<string, unknown>;
  errors: Record<string, string[]>;
}

export interface StatusResponse {
  current_data: Record<string, unknown>;
  is_complete: boolean;
  missing_fields: string[];
}
