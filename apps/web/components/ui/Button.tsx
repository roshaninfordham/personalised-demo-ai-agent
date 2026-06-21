import type { ButtonHTMLAttributes, ReactNode } from "react";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
  children: ReactNode;
};

export function Button({ variant = "primary", className, children, ...props }: ButtonProps) {
  const variantClass = variant === "primary" ? "" : ` button-${variant}`;
  return (
    <button className={`button${variantClass}${className === undefined ? "" : ` ${className}`}`} {...props}>
      {children}
    </button>
  );
}
