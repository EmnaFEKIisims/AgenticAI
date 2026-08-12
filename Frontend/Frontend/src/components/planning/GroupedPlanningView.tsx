import { useMemo } from "react";
import type { SessionSlot } from "../../types/planning";
import GroupCard from "./GroupCard";
import TrainerCard from "./TrainerCard";

interface GroupedPlanningViewProps {
  schedule: SessionSlot[];
  mode: "group" | "trainer";
  showReasoning?: boolean;
}

function groupByKey(
  sessions: SessionSlot[],
  key: "group_name" | "trainer_name"
): Record<string, SessionSlot[]> {
  return sessions.reduce<Record<string, SessionSlot[]>>((acc, session) => {
    const bucket = session[key];
    if (!acc[bucket]) acc[bucket] = [];
    acc[bucket].push(session);
    return acc;
  }, {});
}

export default function GroupedPlanningView({ schedule, mode, showReasoning = false }: GroupedPlanningViewProps) {
  const grouped = useMemo(() => {
    const key = mode === "group" ? "group_name" : "trainer_name";
    return groupByKey(schedule, key);
  }, [schedule, mode]);

  const names = useMemo(() => Object.keys(grouped).sort((a, b) => a.localeCompare(b)), [grouped]);

  if (!names.length) return null;

  return (
    <section className="planning-grouped-view">
      {mode === "group"
        ? names.map((name) => (
            <GroupCard key={name} groupName={name} sessions={grouped[name]} showReasoning={showReasoning} />
          ))
        : names.map((name) => (
            <TrainerCard key={name} trainerName={name} sessions={grouped[name]} showReasoning={showReasoning} />
          ))}
    </section>
  );
}
