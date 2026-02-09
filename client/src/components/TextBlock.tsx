import type { TextBlock as TextBlockType } from "../types/ui-blocks";

interface TextBlockProps {
  block: TextBlockType;
}

export function TextBlock({ block }: TextBlockProps) {
  return <div className="rounded-lg bg-blue-50 px-4 py-3 text-sm text-gray-800">{block.value}</div>;
}
