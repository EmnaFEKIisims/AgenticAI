import type { SessionSlot } from "../../types/planning";
import PlanningTable from "./PlanningTable";

interface GroupCardProps {
  groupName: string;
  sessions: SessionSlot[];
}

export default function GroupCard({ groupName, sessions }: GroupCardProps) {
  return (
    <article className="planning-entity-card">
      <div className="planning-entity-header">
        <h3 className="planning-entity-title">{groupName}</h3>
        <span className="planning-entity-count">{sessions.length} session(s)</span>
      </div>

      <PlanningTable schedule={sessions} mode="group" />
    </article>
  );
}
