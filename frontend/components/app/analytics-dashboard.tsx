'use client';

import { useState, useEffect, useCallback, useTransition } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Globe,
  Mic,
  PhoneCall,
  RefreshCw,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface CallRecord {
  id: number;
  session_id: string;
  learner_id: string;
  call_type: string;
  started_at: string;
  ended_at: string | null;
  duration: number;
  exercise_started: boolean;
  exercise_completed: boolean;
  feedback_given: boolean;
  outcome: 'IN_PROGRESS' | 'SUCCESS' | 'FAILED';
}

export interface AnalyticsData {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
  average_duration: number;
  browser_calls: number;
  sip_calls: number;
  recent_calls: CallRecord[];
}

interface AnalyticsDashboardProps {
  initialData?: AnalyticsData;
}

const OUTCOME_CONFIG: Record<
  CallRecord['outcome'],
  { label: string; classes: string; icon: React.ReactNode }
> = {
  SUCCESS: {
    label: 'SUCCESS',
    classes: 'border-emerald-400/40 bg-emerald-500/15 text-emerald-300',
    icon: <CheckCircle2 className="size-3.5 text-emerald-400" />,
  },
  FAILED: {
    label: 'FAILED',
    classes: 'border-rose-400/40 bg-rose-500/15 text-rose-300',
    icon: <XCircle className="size-3.5 text-rose-400" />,
  },
  IN_PROGRESS: {
    label: 'IN PROGRESS',
    classes: 'border-amber-400/40 bg-amber-500/15 text-amber-300 animate-pulse',
    icon: <Clock className="size-3.5 text-amber-400" />,
  },
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return iso;
  }
}

function formatDuration(seconds: number): string {
  if (seconds <= 0) return '0s';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs}s`;
}

function formatSessionId(id: string): string {
  if (id.length > 24) {
    return `${id.slice(0, 10)}...${id.slice(-8)}`;
  }
  return id;
}

export function AnalyticsDashboard({ initialData }: AnalyticsDashboardProps) {
  const [data, setData] = useState<AnalyticsData>(
    initialData ?? {
      total_calls: 0,
      successful_calls: 0,
      failed_calls: 0,
      success_rate: 0,
      average_duration: 0,
      browser_calls: 0,
      sip_calls: 0,
      recent_calls: [],
    }
  );

  const [isPending, startTransition] = useTransition();
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    try {
      const res = await fetch('/api/analytics', { cache: 'no-store' });
      if (!res.ok) return;
      const json = await res.json();
      startTransition(() => {
        setData(json);
        setLastUpdated(new Date());
      });
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  }, []);

  // Poll every 3 seconds for real-time updates
  useEffect(() => {
    if (!autoRefresh) return;
    const timer = setInterval(() => {
      fetchAnalytics();
    }, 3000);
    return () => clearInterval(timer);
  }, [autoRefresh, fetchAnalytics]);

  return (
    <div className="min-h-svh bg-[radial-gradient(ellipse_at_top,_oklch(0.22_0.08_265)_0%,_oklch(0.12_0.04_265)_55%,_oklch(0.09_0.04_270)_100%)] text-white font-sans antialiased">
      {/* Background glow effects */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-40 right-1/4 h-[500px] w-[500px] rounded-full bg-indigo-500/10 blur-[120px]" />
        <div className="absolute top-1/2 left-10 h-[400px] w-[400px] rounded-full bg-emerald-500/8 blur-[100px]" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-white/10 pb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <Link
                href="/"
                className="inline-flex items-center gap-1 text-xs text-white/60 hover:text-white transition-colors"
              >
                <ArrowLeft className="size-3.5" /> Landing
              </Link>
              <span className="text-white/30">•</span>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1 text-xs text-white/60 hover:text-white transition-colors"
              >
                Teacher Escalations
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-emerald-500 p-0.5 shadow-lg shadow-indigo-500/20">
                <div className="flex size-full items-center justify-center rounded-[10px] bg-slate-950">
                  <Activity className="size-5 text-emerald-400" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Call Analytics
                </h1>
                <p className="text-xs text-white/60">
                  Real-time voice session telemetry & outcome tracking
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-white/40 hidden sm:inline">
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
            <Button
              onClick={() => setAutoRefresh(!autoRefresh)}
              variant="outline"
              size="sm"
              className={`rounded-lg border-white/10 ${
                autoRefresh
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                  : 'bg-white/5 text-white/60'
              }`}
            >
              <span className={`size-2 rounded-full mr-2 ${autoRefresh ? 'bg-emerald-400 animate-ping' : 'bg-white/30'}`} />
              {autoRefresh ? 'Live Syncing' : 'Paused'}
            </Button>
            <Button
              onClick={() => fetchAnalytics()}
              disabled={isPending}
              variant="outline"
              size="sm"
              className="rounded-lg border-white/10 bg-white/5 text-white hover:bg-white/10"
            >
              <RefreshCw className={`size-3.5 mr-1.5 ${isPending ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </header>

        {/* ── Main Required Metrics Cards ────────────────────────────── */}
        <section className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-3">
          {/* 1. TOTAL CALLS */}
          <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl transition-all hover:border-white/20">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-white/60 uppercase">
                TOTAL CALLS
              </span>
              <div className="flex size-8 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                <PhoneCall className="size-4" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold tracking-tight text-white">
                {data.total_calls}
              </span>
              <span className="text-xs text-white/50">real sessions</span>
            </div>
            <p className="mt-2 text-xs text-white/40">
              Total voice calls recorded in database
            </p>
          </div>

          {/* 2. SUCCESSFUL CALLS */}
          <div className="relative overflow-hidden rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-6 backdrop-blur-xl transition-all hover:border-emerald-500/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-emerald-400 uppercase">
                SUCCESSFUL CALLS
              </span>
              <div className="flex size-8 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                <CheckCircle2 className="size-4" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold tracking-tight text-emerald-400">
                {data.successful_calls}
              </span>
              <span className="text-xs text-emerald-400/70">completed exercises</span>
            </div>
            <p className="mt-2 text-xs text-white/40">
              Learner completed exercise & received feedback
            </p>
          </div>

          {/* 3. FAILED CALLS */}
          <div className="relative overflow-hidden rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6 backdrop-blur-xl transition-all hover:border-rose-500/30">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold tracking-wider text-rose-400 uppercase">
                FAILED CALLS
              </span>
              <div className="flex size-8 items-center justify-center rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/30">
                <XCircle className="size-4" />
              </div>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-4xl font-extrabold tracking-tight text-rose-400">
                {data.failed_calls}
              </span>
              <span className="text-xs text-rose-400/70">ended early</span>
            </div>
            <p className="mt-2 text-xs text-white/40">
              Call ended before completing an exercise
            </p>
          </div>
        </section>

        {/* ── Optional Useful Metrics ────────────────────────────────── */}
        <section className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs text-white/50 mb-1">
              <TrendingUp className="size-3.5 text-indigo-400" />
              Success Rate
            </div>
            <div className="text-xl font-bold text-white">
              {data.success_rate}%
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs text-white/50 mb-1">
              <Clock className="size-3.5 text-amber-400" />
              Avg Call Duration
            </div>
            <div className="text-xl font-bold text-white">
              {formatDuration(data.average_duration)}
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs text-white/50 mb-1">
              <Globe className="size-3.5 text-blue-400" />
              Browser Calls
            </div>
            <div className="text-xl font-bold text-white">
              {data.browser_calls}
            </div>
          </div>

          <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs text-white/50 mb-1">
              <PhoneCall className="size-3.5 text-purple-400" />
              SIP Calls
            </div>
            <div className="text-xl font-bold text-white">
              {data.sip_calls}
            </div>
          </div>
        </section>

        {/* ── Recent Call History ────────────────────────────────────── */}
        <section className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">
                Recent Call History
              </h2>
              <p className="text-xs text-white/50">
                Log of real voice sessions with exercise completion status
              </p>
            </div>
            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60">
              {data.recent_calls.length} entries
            </span>
          </div>

          {data.recent_calls.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center border border-dashed border-white/10 rounded-xl">
              <Mic className="size-10 text-white/20 mb-3" />
              <p className="text-sm font-medium text-white/70">No calls recorded yet</p>
              <p className="text-xs text-white/40 max-w-sm mt-1">
                Start a voice session from the tutor app to record call telemetry automatically.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-white/80">
                <thead className="border-b border-white/10 text-xs font-semibold tracking-wider text-white/40 uppercase">
                  <tr>
                    <th className="py-3 px-4">Reference / Session ID</th>
                    <th className="py-3 px-4">Call Type</th>
                    <th className="py-3 px-4">Started At</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4">Exercise Completed</th>
                    <th className="py-3 px-4 text-right">Outcome</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.recent_calls.map((call) => {
                    const outcomeCfg = OUTCOME_CONFIG[call.outcome] ?? OUTCOME_CONFIG.FAILED;
                    return (
                      <tr key={call.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3.5 px-4 font-mono text-xs text-amber-300/90 font-medium">
                          {formatSessionId(call.session_id)}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium border ${
                            call.call_type === 'sip'
                              ? 'border-purple-400/30 bg-purple-500/10 text-purple-300'
                              : 'border-blue-400/30 bg-blue-500/10 text-blue-300'
                          }`}>
                            {call.call_type === 'sip' ? <PhoneCall className="size-3" /> : <Globe className="size-3" />}
                            {call.call_type === 'sip' ? 'SIP Call' : 'Browser'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-white/60">
                          {formatDate(call.started_at)}
                        </td>
                        <td className="py-3.5 px-4 text-xs font-mono text-white/70">
                          {call.outcome === 'IN_PROGRESS' ? (
                            <span className="text-amber-400 animate-pulse">Active</span>
                          ) : (
                            formatDuration(call.duration)
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            call.exercise_completed
                              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                              : 'bg-white/5 text-white/40 border border-white/10'
                          }`}>
                            {call.exercise_completed ? 'Yes' : 'No'}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold border ${outcomeCfg.classes}`}>
                            {outcomeCfg.icon}
                            {outcomeCfg.label}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
