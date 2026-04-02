import type React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  style?: React.CSSProperties;
  children: React.ReactNode;
}

export default function Button({ style, children, ...props }: ButtonProps) {
  return (
    <button {...props} style={style}>
      {children}
    </button>
  );
}
