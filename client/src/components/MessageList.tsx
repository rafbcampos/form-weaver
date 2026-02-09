import type { Message } from "../hooks/useInterview";
import { TextBlock } from "./TextBlock";
import { FormBlock } from "./FormBlock";

interface MessageListProps {
  messages: Message[];
  onFormSubmit: (data: Record<string, unknown>) => void;
  serverErrors: Record<string, string[]>;
  loading: boolean;
}

export function MessageList({ messages, onFormSubmit, serverErrors, loading }: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((msg, msgIdx) => {
        if (msg.role === "user") {
          return (
            <div key={msg.id} className="flex justify-end">
              <div className="rounded-lg bg-gray-100 px-4 py-2 text-sm text-gray-800 max-w-[80%]">
                {msg.text}
              </div>
            </div>
          );
        }

        const isLast = msgIdx === messages.length - 1;

        return (
          <div key={msg.id} className="space-y-3">
            {msg.blocks?.map((block, blockIdx) => {
              if (block.kind === "text") {
                return <TextBlock key={blockIdx} block={block} />;
              }
              return (
                <FormBlock
                  key={blockIdx}
                  block={block}
                  onSubmit={onFormSubmit}
                  serverErrors={isLast ? serverErrors : {}}
                  disabled={loading}
                />
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
