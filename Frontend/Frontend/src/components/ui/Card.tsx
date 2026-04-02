import type React from "react";

interface CardProps {
  style?: React.CSSProperties;
  className?: string;
  children: React.ReactNode;
}

export default function Card({ style, className, children }: CardProps) {
  return (
    <div style={style} className={className}>
      {children}
    </div>
  );
}
