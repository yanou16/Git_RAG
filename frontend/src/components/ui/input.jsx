import { cn } from "../../lib/utils.js";

export function Input({ className, ...props }) {
  return (
    <input
      className={cn(
        "flex h-11 w-full border border-c-hairline bg-white px-3 py-2",
        "text-sm text-c-ink placeholder:text-c-muted",
        "focus:outline-none focus:border-[#9b60aa] focus:ring-1 focus:ring-[#9b60aa]",
        "disabled:cursor-not-allowed disabled:opacity-40 disabled:bg-c-stone",
        "transition-colors touch-manipulation",
        "rounded",   /* 4px — Cohere xs */
        className
      )}
      {...props}
    />
  );
}
