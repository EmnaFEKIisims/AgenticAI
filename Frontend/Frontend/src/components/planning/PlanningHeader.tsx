import Card from "../ui/Card";
import { Sparkles } from "lucide-react";

interface PlanningHeaderProps {
  title: string;
  subtitle: string;
}

export default function PlanningHeader({
  title,
  subtitle,
}: PlanningHeaderProps) {
  return (
    <header className="planning-header">
      <Card className="planning-header-inner">
        <div className="planning-logo-mark" aria-hidden="true">
          <Sparkles size={30} />
        </div>
        <div>
          <h1 className="planning-title">{title}</h1>
          <p className="planning-subtitle">{subtitle}</p>
        </div>
      </Card>
    </header>
  );
}
