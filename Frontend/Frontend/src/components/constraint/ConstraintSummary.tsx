import { Ban, CalendarClock, Settings2, GraduationCap, Layers } from "lucide-react";
import type { ConstraintSummaryData } from "../../types/constraintTypes";

interface ConstraintSummaryProps {
  data: ConstraintSummaryData;
}

interface SectionProps {
  icon: React.ElementType;
  title: string;
  items: string[];
  tone: "violet" | "amber" | "slate" | "rose";
}

const TONE_STYLES = {
  violet: {
    icon: "bg-violet-50 text-violet-600 border-violet-100",
    badge: "bg-violet-50 text-violet-700 border-violet-100",
  },
  amber: {
    icon: "bg-amber-50 text-amber-600 border-amber-100",
    badge: "bg-amber-50 text-amber-700 border-amber-100",
  },
  slate: {
    icon: "bg-slate-100 text-slate-600 border-slate-200",
    badge: "bg-slate-100 text-slate-700 border-slate-200",
  },
  rose: {
    icon: "bg-rose-50 text-rose-600 border-rose-100",
    badge: "bg-rose-50 text-rose-700 border-rose-100",
  },
} as const;

function Section({ icon: Icon, title, items, tone }: SectionProps) {
  const styles = TONE_STYLES[tone];
  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50/50 p-5">
      <header className="mb-4 flex items-center gap-3">
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border ${styles.icon}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
        </div>
        <span className={`shrink-0 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${styles.badge}`}>
          {items.length}
        </span>
      </header>
      <div className="space-y-1.5 text-sm text-slate-700">
        {items.length ? (
          items.map((item) => (
            <div key={item} className="leading-relaxed">
              {item}
            </div>
          ))
        ) : (
          <p className="text-slate-400">No data provided.</p>
        )}
      </div>
    </div>
  );
}

export default function ConstraintSummary({ data }: ConstraintSummaryProps) {
  return (
    <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <header className="flex items-center gap-4 border-b border-slate-100 bg-linear-to-br from-slate-50 via-white to-white px-6 py-6 sm:px-8">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
          <Layers className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <h3 className="text-lg font-semibold tracking-tight text-slate-900">
            Merged constraints
          </h3>
          <p className="mt-0.5 text-sm text-slate-500">
            Final rules applied to the planning agent.
          </p>
        </div>
      </header>

      <div className="grid gap-4 bg-slate-50/40 p-6 sm:grid-cols-2 sm:p-8">
        <Section icon={Ban} title="Forbidden days" items={data.forbiddenDays} tone="rose" />

        <div className="rounded-2xl border border-slate-100 bg-slate-50/50 p-5">
          <header className="mb-4 flex items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-sky-100 bg-sky-50 text-sky-600">
              <CalendarClock className="h-4 w-4" aria-hidden="true" />
            </span>
            <h4 className="flex-1 text-sm font-semibold text-slate-800">
              Trainer availability
            </h4>
            <span className="shrink-0 rounded-full border border-sky-100 bg-sky-50 px-2 py-0.5 text-[10px] font-semibold text-sky-700">
              {data.trainerAvailability.length}
            </span>
          </header>
          <div className="space-y-2 text-sm text-slate-700">
            {data.trainerAvailability.length ? (
              data.trainerAvailability.map((entry) => (
                <div
                  key={entry.trainer}
                  className="flex items-center justify-between gap-3 rounded-lg border border-slate-100 bg-white px-3 py-2"
                >
                  <span className="font-medium text-slate-900">{entry.trainer}</span>
                  <span className="text-xs text-slate-500">
                    {entry.availability.length
                      ? entry.availability.join(" · ")
                      : "No availability"}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-slate-400">No trainer availability.</p>
            )}
          </div>
        </div>

        <Section
          icon={Settings2}
          title="Planning parameters"
          items={data.planningParameters.map((p) => `${p.label} — ${p.value}`)}
          tone="slate"
        />

        <Section
          icon={GraduationCap}
          title="Pedagogical rules"
          items={data.pedagogicalRules}
          tone="violet"
        />
      </div>
    </section>
  );
}