import type { SessionSlot } from "../../types/planning";
import EntityScheduleCard from "./EntityScheduleCard";

interface TrainerCardProps {
  trainerName: string;
  sessions: SessionSlot[];
  timeSlots: string[];
  showReasoning?: boolean;
}

export default function TrainerCard({ trainerName, sessions, timeSlots, showReasoning = false }: TrainerCardProps) {
  return <EntityScheduleCard title={trainerName} sessions={sessions} entityType="Trainer" timeSlots={timeSlots} />;
}
