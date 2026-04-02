import type React from "react";

interface BadgeProps {
  style?: React.CSSProperties;
  className?: string;
  children: React.ReactNode;
}

export default function Badge({ style, className, children }: BadgeProps) {
  return (
    <span style={style} className={className}>
      {children}
    </span>
  );
}
