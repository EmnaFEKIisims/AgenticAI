interface EmptyStateProps {
  title?: string;
  description?: string;
}

export default function EmptyState({
  title = "No planning generated",
  description = "Run planning to generate sessions.",
}: EmptyStateProps) {
  return (
    <div className="planning-empty-state">
      <p className="planning-empty-title">{title}</p>
      <p className="planning-empty-description">{description}</p>
    </div>
  );
}
