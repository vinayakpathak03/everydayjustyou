import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "muted";

const VARIANT_CLASSES: Record<Variant, string> = {
  primary: "bg-ink text-bg-elevated disabled:bg-line disabled:text-ink-faint",
  secondary: "bg-accent-soft text-ink border border-line",
  muted: "bg-line text-ink-faint",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", ...props }, ref) => (
    <button
      ref={ref}
      className={`rounded-full px-5 py-3 text-sm font-medium tracking-wide transition-opacity active:opacity-80 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  )
);
Button.displayName = "Button";
