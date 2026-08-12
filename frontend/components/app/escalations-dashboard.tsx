'use client';

import { useState, useTransition, useCallback, useEffect } from 'react';
import Link from 'next/link';
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  ExternalLink,
  Loader2,
  Mic,
  RefreshCw,
  Users,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface Escalation {
  id: number;
  reference_id: string;
  learner_id: string;
  learner_name: string | null;
  reason: string;
  topic: string | null;
  summary: string;
  agent_actions: string[];
  urgency: string;
  language: string | null;
  preferred_follow_up: string | null;
  status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED';
  created_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
  Escalation['status'],
  { label: string; classes: string; icon: React.ReactNode }
> = {
  OPEN: {
    label: 'Open',
    classes:
      'border-amber-400/40 bg-amber-400/15 text-amber-300',
    icon: <AlertCircle className="size-3" />,
  },
  IN_PROGRESS: {
    label: 'In Progress',
    classes:
      'border-indigo-400/40 bg-indigo-400/15 text-indigo-300',
    icon: <Clock className="size-3" />,
  },
  RESOLVED: {
    label: 'Resolved',
    classes:
      'border-emerald-400/40 bg-emerald-400/15 text-emerald-300',
    icon: <CheckCircle2 className="size-3" />,
  },
};

const URGENCY_CONFIG: Record<string, { classes: string }> = {
  high: { classes: 'text-red-400 font-semibold' },
  normal: { classes: 'text-white/50' },
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: Escalation['status'] }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.OPEN;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${cfg.classes}`}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Status selector (dropdown)
// ---------------------------------------------------------------------------

function StatusSelector({
  escalation,
  onUpdated,
}: {
  escalation: Escalation;
  onUpdated: (refId: string, newStatus: Escalation['status']) => void;
}) {
  const [pending, startTransition] = useTransition();

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newStatus = e.target.value as Escalation['status'];
    startTransition(async () => {
      try {
        const res = await fetch(
          `/api/escalations/${encodeURIComponent(escalation.reference_id)}`,
          {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus }),
          }
        );
        if (res.ok) {
          onUpdated(escalation.reference_id, newStatus);
        }
      } catch {
        // silently ignore — the old status remains
      }
    });
  };

  return (
    <div className="relative flex items-center gap-2">
      {pending && <Loader2 className="size-3.5 animate-spin text-white/40" />}
      <select
        value={escalation.status}
        onChange={handleChange}
        disabled={pending}
        className="rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-xs text-white/80 outline-none transition hover:border-amber-400/30 focus:border-amber-400/40 focus:ring-1 focus:ring-amber-400/30 disabled:opacity-50"
      >
        <option value="OPEN">Open</option>
        <option value="IN_PROGRESS">In Progress</option>
        <option value="RESOLVED">Resolved</option>
      </select>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Single escalation card (expanded view)
// ---------------------------------------------------------------------------

function EscalationRow({
  escalation,
  onUpdated,
}: {
  escalation: Escalation;
  onUpdated: (refId: string, newStatus: Escalation['status']) => void;
}) {
  const urgencyClasses =
    URGENCY_CONFIG[escalation.urgency]?.classes ?? URGENCY_CONFIG.normal.classes;

  return (
    <article className="group flex flex-col gap-4 rounded-2xl border border-white/8 bg-white/4 p-5 backdrop-blur-sm transition-all hover:border-amber-400/20 hover:bg-white/6 md:flex-row md:items-start md:gap-6">
      {/* Left — IDs and meta */}
      <div className="flex min-w-[160px] flex-col gap-2">
        <span className="font-mono text-sm font-bold text-amber-300">
          {escalation.reference_id}
        </span>
        <StatusBadge status={escalation.status} />
        <p className={`text-xs ${urgencyClasses}`}>
          Urgency: {escalation.urgency}
        </p>
        <p className="text-[11px] text-white/35">
          {formatDate(escalation.created_at)}
        </p>
      </div>

      {/* Middle — details */}
      <div className="flex flex-1 flex-col gap-3">
        {/* Learner + Reason */}
        <div className="flex flex-wrap items-start gap-x-4 gap-y-1">
          <p className="text-sm font-semibold text-white">
            {escalation.learner_name ?? 'Learner'}
          </p>
          {escalation.topic && (
            <span className="rounded-full border border-indigo-400/25 bg-indigo-400/10 px-2 py-0.5 text-[11px] text-indigo-300">
              {escalation.topic}
            </span>
          )}
          {escalation.language && (
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-white/50">
              {escalation.language}
            </span>
          )}
        </div>

        {/* Reason */}
        <p className="text-xs font-medium text-amber-200/70">
          Reason: {escalation.reason}
        </p>

        {/* Summary (pre-formatted) */}
        <div className="rounded-xl border border-white/6 bg-white/3 px-4 py-3">
          <p className="whitespace-pre-line text-xs leading-5 text-white/65">
            {escalation.summary}
          </p>
        </div>

        {/* Agent actions */}
        {escalation.agent_actions && escalation.agent_actions.length > 0 && (
          <div>
            <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-white/35">
              Agent already tried:
            </p>
            <ul className="flex flex-col gap-1">
              {escalation.agent_actions.map((a, i) => (
                <li key={i} className="flex items-center gap-2 text-xs text-white/50">
                  <span className="size-1.5 rounded-full bg-amber-400/50" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Follow-up preference */}
        {escalation.preferred_follow_up && (
          <p className="text-[11px] text-white/40">
            Preferred follow-up:{' '}
            <span className="text-white/60">{escalation.preferred_follow_up}</span>
          </p>
        )}
      </div>

      {/* Right — status control */}
      <div className="flex items-center gap-3 md:flex-col md:items-end">
        <StatusSelector escalation={escalation} onUpdated={onUpdated} />
      </div>
    </article>
  );
}

// ---------------------------------------------------------------------------
// Stats bar
// ---------------------------------------------------------------------------

function StatsBar({ escalations }: { escalations: Escalation[] }) {
  const total = escalations.length;
  const open = escalations.filter((e) => e.status === 'OPEN').length;
  const inProgress = escalations.filter((e) => e.status === 'IN_PROGRESS').length;
  const resolved = escalations.filter((e) => e.status === 'RESOLVED').length;

  const stats = [
    { label: 'Total', value: total, color: 'text-white' },
    { label: 'Open', value: open, color: 'text-amber-300' },
    { label: 'In Progress', value: inProgress, color: 'text-indigo-300' },
    { label: 'Resolved', value: resolved, color: 'text-emerald-300' },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {stats.map((s) => (
        <div
          key={s.label}
          className="flex flex-col gap-1 rounded-xl border border-white/8 bg-white/4 px-4 py-3"
        >
          <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
          <p className="text-[11px] text-white/40 uppercase tracking-wide">{s.label}</p>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main dashboard component
// ---------------------------------------------------------------------------

interface EscalationsDashboardProps {
  initialEscalations: Escalation[];
}

export function EscalationsDashboard({
  initialEscalations,
}: EscalationsDashboardProps) {
  const [escalations, setEscalations] =
    useState<Escalation[]>(initialEscalations);
  const [isRefreshing, startRefresh] = useTransition();
  const [filterStatus, setFilterStatus] = useState<string>('ALL');

  const refresh = useCallback(() => {
    startRefresh(async () => {
      try {
        const res = await fetch('/api/escalations', { cache: 'no-store' });
        if (res.ok) {
          const data: Escalation[] = await res.json();
          setEscalations(data);
        }
      } catch {
        /* ignore */
      }
    });
  }, []);

  // Fetch on mount to ensure fresh data even if server-side prefetch failed
  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleStatusUpdate = useCallback(
    (refId: string, newStatus: Escalation['status']) => {
      setEscalations((prev) =>
        prev.map((e) =>
          e.reference_id === refId ? { ...e, status: newStatus } : e
        )
      );
    },
    []
  );

  const displayed =
    filterStatus === 'ALL'
      ? escalations
      : escalations.filter((e) => e.status === filterStatus);

  return (
    <div className="relative min-h-svh overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_oklch(0.25_0.09_265)_0%,_oklch(0.13_0.04_265)_55%,_oklch(0.10_0.05_270)_100%)] text-white">
      {/* Ambient blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-32 -left-32 h-[500px] w-[500px] rounded-full bg-amber-400/8 blur-[100px]" />
        <div className="absolute top-1/3 -right-24 h-[350px] w-[350px] rounded-full bg-indigo-500/8 blur-[90px]" />
      </div>

      {/* Dot grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
        aria-hidden
      />

      <div className="relative mx-auto flex min-h-svh max-w-6xl flex-col gap-8 px-6 py-8 md:px-10">

        {/* Header */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex size-10 items-center justify-center">
              <span className="animate-pulse-ring absolute inset-0 rounded-full bg-amber-400/40" />
              <span className="relative flex size-10 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-amber-500 shadow-lg shadow-amber-500/30">
                <Mic className="size-4 text-slate-900" />
              </span>
            </div>
            <div>
              <p className="font-mono text-[10px] font-bold tracking-[0.35em] text-amber-300/80 uppercase">
                SpeakEasy AI
              </p>
              <p className="text-xs text-white/50">Human Help Dashboard</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={refresh}
              disabled={isRefreshing}
              className="gap-2 rounded-full border border-white/10 bg-white/5 text-white/60 hover:text-white"
            >
              <RefreshCw
                className={`size-3.5 ${isRefreshing ? 'animate-spin' : ''}`}
              />
              Refresh
            </Button>
            <Button
              asChild
              variant="outline"
              size="sm"
              className="rounded-full border-white/15 bg-white/5 text-white backdrop-blur-sm hover:bg-white/10"
            >
              <Link href="/agent" className="flex items-center gap-1.5">
                <ExternalLink className="size-3.5" />
                Voice agent
              </Link>
            </Button>
          </div>
        </header>

        {/* Page title */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <Users className="size-5 text-amber-300" />
            <h1 className="text-2xl font-bold text-white">Human Help Requests</h1>
          </div>
          <p className="text-sm text-white/45">
            Teacher-help requests created by the voice agent when a learner needs
            human support.
          </p>
        </div>

        {/* Stats */}
        <StatsBar escalations={escalations} />

        {/* Filter bar */}
        <div className="flex flex-wrap gap-2">
          {['ALL', 'OPEN', 'IN_PROGRESS', 'RESOLVED'].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStatus(s)}
              className={`rounded-full border px-3.5 py-1.5 text-xs font-semibold uppercase tracking-wide transition ${
                filterStatus === s
                  ? 'border-amber-400/40 bg-amber-400/15 text-amber-300'
                  : 'border-white/10 bg-white/4 text-white/50 hover:border-white/20 hover:text-white/70'
              }`}
            >
              {s === 'IN_PROGRESS' ? 'In Progress' : s.charAt(0) + s.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        {/* List */}
        {displayed.length === 0 ? (
          <div className="flex flex-col items-center gap-4 rounded-2xl border border-white/8 bg-white/4 py-16 text-center">
            <CheckCircle2 className="size-12 text-white/20" />
            <p className="text-sm text-white/40">
              {filterStatus === 'ALL'
                ? 'No teacher-help requests yet. Start a voice session to generate one.'
                : `No ${filterStatus === 'IN_PROGRESS' ? 'in-progress' : filterStatus.toLowerCase()} requests.`}
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {displayed.map((e) => (
              <EscalationRow
                key={e.reference_id}
                escalation={e}
                onUpdated={handleStatusUpdate}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
