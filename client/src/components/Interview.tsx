import { useEffect, useRef } from "react";
import type { InterviewSchema } from "../types/schema";
import { useInterview } from "../hooks/useInterview";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";

interface InterviewProps {
  schema: InterviewSchema;
}

export function Interview({ schema }: InterviewProps) {
  const {
    messages,
    isComplete,
    currentData,
    loading,
    error,
    serverErrors,
    start,
    submitFormData,
    sendTextMessage,
  } = useInterview(schema);

  const scrollRef = useRef<HTMLDivElement>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (!startedRef.current) {
      startedRef.current = true;
      start();
    }
  }, [start]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  return (
    <div className="mx-auto flex h-screen max-w-2xl flex-col">
      <header className="border-b border-gray-200 px-4 py-3">
        <h1 className="text-lg font-semibold text-gray-900">Interview</h1>
        {isComplete && <p className="text-sm text-green-600">Interview complete</p>}
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4">
        <MessageList
          messages={messages}
          onFormSubmit={submitFormData}
          serverErrors={serverErrors}
          loading={loading}
        />
        {loading && <div className="mt-4 text-center text-sm text-gray-500">Thinking...</div>}
        {error && <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      </div>

      {!isComplete && (
        <div className="border-t border-gray-200 p-4">
          <MessageInput onSend={sendTextMessage} disabled={loading} />
        </div>
      )}

      {isComplete && (
        <div className="border-t border-gray-200 p-4">
          <details className="text-sm">
            <summary className="cursor-pointer font-medium text-gray-700">Collected Data</summary>
            <pre className="mt-2 overflow-auto rounded bg-gray-50 p-3 text-xs">
              {JSON.stringify(currentData, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
