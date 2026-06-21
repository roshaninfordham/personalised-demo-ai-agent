import type { ReactNode } from "react";

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={`card${className === undefined ? "" : ` ${className}`}`}>{children}</section>;
}

export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={`card-body${className === undefined ? "" : ` ${className}`}`}>{children}</div>;
}
