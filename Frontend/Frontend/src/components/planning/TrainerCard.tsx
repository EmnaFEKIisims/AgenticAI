import type { SessionSlot } from "../../types/planning";
import PlanningTable from "./PlanningTable";

interface TrainerCardProps {
  trainerName: string;
  sessions: SessionSlot[];
  showReasoning?: boolean;
}

export default function TrainerCard({ trainerName, sessions, showReasoning = false }: TrainerCardProps) {
  return (
    <article className="planning-entity-card">
      <div className="planning-entity-header">
        <h3 className="planning-entity-title">{trainerName}</h3>
        <span className="planning-entity-count">{sessions.length} session(s)</span>
      </div>

      <PlanningTable schedule={sessions} mode="trainer" showReasoning={showReasoning} />
    </article>
  );
}
