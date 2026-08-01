import { HTMLAttributes } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-lg border border-line bg-bg-elevated p-4 shadow-sm ${className}`}
      {...props}
    />
  );
}
