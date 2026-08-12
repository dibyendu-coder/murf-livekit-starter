import Image from 'next/image';
import Link from 'next/link';
import { BookOpen, Languages, Mic, Sparkles, Star, Users } from 'lucide-react';
import type { AppConfig } from '@/app-config';
import { Button } from '@/components/ui/button';

interface LandingViewProps {
  appConfig: AppConfig;
}

const features = [
  {
    icon: Mic,
    title: 'Speak, don\'t type',
    text: 'Real-time voice conversation — just talk and your tutor listens, corrects, and guides you.',
    delay: '0ms',
  },
  {
    icon: Languages,
    title: 'Hindi · English · Mix',
    text: 'Start in Hindi, Hinglish, or full English — the tutor mirrors your natural language.',
    delay: '80ms',
  },
  {
    icon: BookOpen,
    title: 'Picks up where you left off',
    text: 'With your permission, the tutor remembers your level, topics, and progress between sessions.',
    delay: '160ms',
  },
  {
    icon: Sparkles,
    title: 'Gentle & encouraging',
    text: 'Every correction is kind. Wrong answers are praised for effort and quietly fixed.',
    delay: '240ms',
  },
];

const levels = ['Beginner', 'Intermediate', 'Advanced'];
const tags   = ['Greetings', 'Past tense', 'Pronunciation', 'Vocabulary', 'Fluency'];

export function LandingView({ appConfig }: LandingViewProps) {
  const { companyName } = appConfig;

  return (
    <main className="relative min-h-svh overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_oklch(0.25_0.09_265)_0%,_oklch(0.13_0.04_265)_55%,_oklch(0.10_0.05_270)_100%)] text-white">

      {/* Ambient glow blobs */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-32 -left-32 h-[520px] w-[520px] rounded-full bg-amber-400/10 blur-[100px]" />
        <div className="absolute top-1/3 -right-24 h-[380px] w-[380px] rounded-full bg-indigo-500/10 blur-[90px]" />
        <div className="absolute bottom-0 left-1/4 h-[260px] w-[260px] rounded-full bg-amber-300/8 blur-[80px]" />
      </div>

      {/* Subtle dot-grid texture */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            'radial-gradient(circle, white 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
        aria-hidden
      />

      <div className="relative mx-auto flex min-h-svh w-full max-w-7xl flex-col px-6 py-8 md:px-10 lg:px-14">

        {/* ── Header ───────────────────────────────────────────────── */}
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Animated mic logo */}
            <div className="relative flex size-10 items-center justify-center">
              <span className="animate-pulse-ring absolute inset-0 rounded-full bg-amber-400/40" />
              <span className="relative flex size-10 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-amber-500 shadow-lg shadow-amber-500/30">
                <Mic className="size-4 text-slate-900" />
              </span>
            </div>
            <div>
              <p className="font-mono text-[10px] font-bold tracking-[0.35em] text-amber-300/80 uppercase">
                {companyName}
              </p>
              <p className="text-xs text-white/50">AI Voice Tutor</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              asChild
              variant="ghost"
              size="sm"
              className="rounded-full border border-white/10 bg-white/5 text-white/60 backdrop-blur-sm hover:bg-white/10 hover:text-white"
            >
              <Link href="/dashboard" className="flex items-center gap-1.5">
                <Users className="size-3.5" />
                Teacher Dashboard
              </Link>
            </Button>

            <Button
              asChild
              variant="outline"
              size="sm"
              className="rounded-full border-white/15 bg-white/5 text-white backdrop-blur-sm hover:bg-white/10"
            >
              <Link href="/agent">Start practising →</Link>
            </Button>
          </div>
        </header>


        {/* ── Hero ─────────────────────────────────────────────────── */}
        <section className="grid flex-1 items-center gap-16 py-14 lg:grid-cols-2 lg:py-0">

          {/* Left — copy */}
          <div className="flex flex-col gap-7">
            {/* Pill badge */}
            <span className="inline-flex w-fit items-center gap-2 rounded-full border border-amber-400/25 bg-amber-400/10 px-4 py-1.5 text-xs font-semibold tracking-widest text-amber-300 uppercase backdrop-blur-sm">
              <Star className="size-3 fill-amber-400 text-amber-400" />
              Personalised practice for every learner
            </span>

            <h1 className="text-4xl font-bold leading-[1.15] tracking-tight text-balance md:text-5xl lg:text-6xl">
              Your patient{' '}
              <span className="shimmer-text">English tutor</span>
              <br />
              is just one{' '}
              <span className="relative inline-block">
                tap away.
                <svg
                  className="absolute -bottom-1.5 left-0 w-full"
                  viewBox="0 0 240 10"
                  fill="none"
                  aria-hidden
                >
                  <path
                    d="M4 7 Q 60 2, 120 6 T 236 5"
                    stroke="#f59e0b"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    fill="none"
                    opacity="0.7"
                  />
                </svg>
              </span>
            </h1>

            <p className="max-w-lg text-base leading-7 text-white/65 md:text-lg">
              Speak naturally in Hindi, English, or a mix of both.
              Get gentle corrections, short drills, and a tutor that
              remembers your progress every time you call.
            </p>

            {/* Level pills */}
            <div className="flex flex-wrap gap-2">
              {levels.map((l) => (
                <span
                  key={l}
                  className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs font-medium text-white/60 backdrop-blur-sm"
                >
                  {l}
                </span>
              ))}
              <span className="rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-300">
                All ages welcome
              </span>
            </div>

            {/* CTA */}
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button
                asChild
                size="lg"
                className="group relative overflow-hidden rounded-full bg-gradient-to-r from-amber-400 to-amber-500 px-8 font-semibold text-slate-900 shadow-lg shadow-amber-500/30 transition-all duration-300 hover:shadow-amber-500/50 hover:scale-[1.02]"
              >
                <Link href="/agent" className="inline-flex items-center gap-2">
                  <Mic className="size-4" />
                  Start a free session
                  <span className="absolute inset-0 bg-white/10 opacity-0 transition-opacity group-hover:opacity-100" />
                </Link>
              </Button>
              <p className="text-xs text-white/40">
                No sign-up required · works on any device
              </p>
            </div>
          </div>

          {/* Right — illustration + feature cards */}
          <div className="flex flex-col gap-4">
            {/* Hero illustration */}
            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-white/5 to-white/2 p-1 shadow-2xl shadow-black/40 backdrop-blur-sm">
              <Image
                src="/tutor-hero.png"
                alt="Friendly English tutor surrounded by speech bubbles"
                width={720}
                height={420}
                className="w-full rounded-[1.35rem] object-cover"
                priority
              />
              {/* Floating topic tags over image */}
              <div className="absolute inset-x-0 bottom-4 flex flex-wrap justify-center gap-2 px-4">
                {tags.map((tag, i) => (
                  <span
                    key={tag}
                    className="animate-float rounded-full border border-amber-300/30 bg-slate-900/70 px-3 py-1 text-[11px] font-semibold text-amber-200 backdrop-blur-sm"
                    style={{ animationDelay: `${i * 0.4}s` }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Feature cards — 2-column grid */}
            <div className="grid grid-cols-2 gap-3">
              {features.map((f) => (
                <article
                  key={f.title}
                  className="group flex flex-col gap-2 rounded-2xl border border-white/8 bg-white/4 p-4 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-amber-400/20 hover:bg-white/7"
                  style={{ animationDelay: f.delay }}
                >
                  <span className="flex size-8 items-center justify-center rounded-xl bg-amber-400/15">
                    <f.icon className="size-4 text-amber-300" />
                  </span>
                  <h2 className="text-sm font-semibold text-white">{f.title}</h2>
                  <p className="text-[12px] leading-5 text-white/55">{f.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
