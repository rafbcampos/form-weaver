import { useCallback, useRef, useState } from "react";
import type { InterviewSchema } from "../types/schema";
import type { UIBlock } from "../types/ui-blocks";
import { startInterview, submitForm, sendMessage } from "../api/client";

export interface Message {
  id: string;
  role: "assistant" | "user";
  blocks?: UIBlock[];
  text?: string;
}

interface UseInterviewReturn {
  messages: Message[];
  isComplete: boolean;
  currentData: Record<string, unknown>;
  loading: boolean;
  error: string | null;
  serverErrors: Record<string, string[]>;
  start: () => Promise<void>;
  submitFormData: (data: Record<string, unknown>) => Promise<void>;
  sendTextMessage: (text: string) => Promise<void>;
}

let nextId = 0;
function makeId(): string {
  return `msg-${++nextId}`;
}

export function useInterview(schema: InterviewSchema): UseInterviewReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [currentData, setCurrentData] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serverErrors, setServerErrors] = useState<Record<string, string[]>>({});
  const sessionIdRef = useRef<string | null>(null);

  const start = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await startInterview(schema);
      sessionIdRef.current = res.session_id;
      setCurrentData(res.current_data);
      setIsComplete(res.is_complete);
      setMessages([
        {
          id: makeId(),
          role: "assistant",
          blocks: res.blocks,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start interview");
    } finally {
      setLoading(false);
    }
  }, [schema]);

  const submitFormData = useCallback(async (data: Record<string, unknown>) => {
    if (!sessionIdRef.current) return;
    setLoading(true);
    setError(null);
    setServerErrors({});

    setMessages((prev) => [...prev, { id: makeId(), role: "user", text: "Submitted form data" }]);

    try {
      const res = await submitForm(sessionIdRef.current, data);
      setCurrentData(res.current_data);
      setIsComplete(res.is_complete);

      if (Object.keys(res.errors).length > 0) {
        setServerErrors(res.errors);
        // Remove the user message we just added
        setMessages((prev) => prev.slice(0, -1));
      } else {
        setMessages((prev) => [...prev, { id: makeId(), role: "assistant", blocks: res.blocks }]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit form");
    } finally {
      setLoading(false);
    }
  }, []);

  const sendTextMessage = useCallback(async (text: string) => {
    if (!sessionIdRef.current) return;
    setLoading(true);
    setError(null);
    setServerErrors({});

    setMessages((prev) => [...prev, { id: makeId(), role: "user", text }]);

    try {
      const res = await sendMessage(sessionIdRef.current, text);
      setCurrentData(res.current_data);
      setIsComplete(res.is_complete);
      setMessages((prev) => [...prev, { id: makeId(), role: "assistant", blocks: res.blocks }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to send message");
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    messages,
    isComplete,
    currentData,
    loading,
    error,
    serverErrors,
    start,
    submitFormData,
    sendTextMessage,
  };
}
