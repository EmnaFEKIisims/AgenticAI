import { Search } from "lucide-react";

interface Props {
  value:       string;
  onChange:    (v: string) => void;
  placeholder?: string;
}

export default function SearchBar({ value, onChange, placeholder = "Search..." }: Props) {
  return (
    <div className="crud-search">
      <Search className="crud-search-icon" aria-hidden="true" />
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="crud-search-input"
      />
    </div>
  );
}