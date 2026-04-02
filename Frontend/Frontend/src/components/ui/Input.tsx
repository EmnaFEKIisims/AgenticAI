import type React from "react";

type InputElement = HTMLInputElement | HTMLTextAreaElement;

interface SharedInputProps {
  style?: React.CSSProperties;
  className?: string;
  disabled?: boolean;
  value: string;
  placeholder?: string;
  multiline?: boolean;
  rows?: number;
  onChange: (value: string) => void;
}

export default function Input({
  style,
  className,
  disabled,
  value,
  placeholder,
  multiline = false,
  rows = 3,
  onChange,
}: SharedInputProps) {
  const handleChange = (event: React.ChangeEvent<InputElement>) => {
    onChange(event.target.value);
  };

  if (multiline) {
    return (
      <textarea
        style={style}
        className={className}
        disabled={disabled}
        value={value}
        rows={rows}
        placeholder={placeholder}
        onChange={handleChange}
      />
    );
  }

  return (
    <input
      style={style}
      className={className}
      disabled={disabled}
      value={value}
      placeholder={placeholder}
      onChange={handleChange}
    />
  );
}
