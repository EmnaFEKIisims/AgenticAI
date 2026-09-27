import type { SessionSlot } from "../../types/planning";
import EntityScheduleCard from "./EntityScheduleCard";

interface TrainerCardProps {
  trainerName: string;
  sessions: SessionSlot[];
  showReasoning?: boolean;
}

export default function TrainerCard({ trainerName, sessions, showReasoning = false }: TrainerCardProps) {
  return <EntityScheduleCard title={trainerName} sessions={sessions} entityType="Trainer" />;
}
