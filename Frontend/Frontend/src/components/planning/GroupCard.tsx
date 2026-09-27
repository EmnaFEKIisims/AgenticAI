import type { SessionSlot } from "../../types/planning";
import EntityScheduleCard from "./EntityScheduleCard";

interface GroupCardProps {
  groupName: string;
  sessions: SessionSlot[];
  showReasoning?: boolean;
}

export default function GroupCard({ groupName, sessions, showReasoning = false }: GroupCardProps) {
  return <EntityScheduleCard title={groupName} sessions={sessions} entityType="Group" />;
}
