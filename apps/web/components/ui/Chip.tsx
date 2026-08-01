import { ButtonHTMLAttributes } from "react";

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
}

export function Chip({ active = false, className = "", ...props }: ChipProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center rounded-full border px-3 py-1.5 font-mono text-xs transition-colors ${
        active
          ? "border-accent bg-accent text-accent-ink"
          : "border-line bg-transparent text-ink-soft"
      } ${className}`}
      {...props}
    />
  );
}
