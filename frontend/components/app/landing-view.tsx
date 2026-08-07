import Link from 'next/link';
import { ArrowRight, Headphones, Languages, Mic, Sparkles } from 'lucide-react';
import type { AppConfig } from '@/app-config';
import { Button } from '@/components/ui/button';

interface LandingViewProps {
  appConfig: AppConfig;
}

const highlights = [
  {
    icon: Mic,
    title: 'Speak naturally',
    text: 'Short voice exchanges adapt to age, English level, and the way the user speaks.',
  },
  {
    icon: Languages,
    title: 'Code-mixed friendly',
    text: 'Hindi, English, or a mix of both is welcome when that is the user\'s natural register.',
  },
  {
    icon: Sparkles,
    title: 'Gentle correction',
    text: 'The tutor stays encouraging, corrects softly, and never shames a wrong answer.',
  },
];

export function LandingView({ appConfig }: LandingViewProps) {
  const { companyName, pageTitle, pageDescription } = appConfig;

  return (
    <main className="relative min-h-svh overflow-hidden bg-[radial-gradient(circle_at_top,_rgba(245,158,11,0.2),_transparent_30%),linear-gradient(180deg,_rgba(15,23,42,0.98),_rgba(2,6,23,1))] text-white">
      <div className="absolute inset-0 bg-[linear-gradient(120deg,rgba(255,255,255,0.08)_0%,transparent_32%,transparent_68%,rgba(255,255,255,0.06)_100%)] opacity-80" />

      <div className="relative mx-auto flex min-h-svh w-full max-w-7xl flex-col px-6 py-8 md:px-10 lg:px-12">
        <header className="flex items-center justify-between gap-6">
          <a href="/" className="flex items-center gap-3">
            <span className="flex size-10 items-center justify-center rounded-xl bg-white text-sm font-bold text-slate-950 shadow-lg shadow-black/20">
              M
            </span>
            <div>
              <p className="font-mono text-[10px] font-bold tracking-[0.35em] text-white/60 uppercase">
                {companyName}
              </p>
              <p className="text-sm text-white/70">Live English practice</p>
            </div>
          </a>

          <Button
            asChild
            variant="outline"
            className="rounded-full border-white/15 bg-white/5 text-white hover:bg-white/10"
          >
            <Link href="/agent">Go to agent</Link>
          </Button>
        </header>

        <section className="grid flex-1 items-center gap-12 py-12 lg:grid-cols-[1.15fr_0.85fr] lg:py-0">
          <div className="max-w-3xl">
            <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/8 px-4 py-2 text-xs font-semibold tracking-[0.22em] text-white/75 uppercase backdrop-blur-sm">
              <Headphones className="size-4" />
              {pageTitle}
            </p>
            <h1 className="max-w-2xl text-4xl leading-tight font-semibold tracking-tight text-balance md:text-6xl">
              A voice tutor that meets you where you are.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-7 text-white/75 md:text-lg">
              {pageDescription}
            </p>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <Button asChild size="lg" className="rounded-full bg-white px-7 text-slate-950 hover:bg-white/90">
                <Link href="/agent" className="inline-flex items-center gap-2">
                  Enter the agent
                  <ArrowRight className="size-4" />
                </Link>
              </Button>
              <div className="rounded-full border border-white/12 bg-white/6 px-5 py-3 text-sm text-white/75 backdrop-blur-sm">
                First users see this page, then they move to the agent page where mic access is requested.
              </div>
            </div>
          </div>

          <div className="grid gap-4 rounded-[2rem] border border-white/12 bg-white/6 p-5 shadow-2xl shadow-black/30 backdrop-blur-xl md:p-6">
            {highlights.map((item) => (
              <article
                key={item.title}
                className="rounded-[1.5rem] border border-white/10 bg-slate-950/35 p-5 transition-transform duration-300 hover:-translate-y-1"
              >
                <item.icon className="mb-4 size-5 text-amber-300" />
                <h2 className="text-lg font-semibold text-white">{item.title}</h2>
                <p className="mt-2 text-sm leading-6 text-white/70">{item.text}</p>
              </article>
            ))}

            <div className="rounded-[1.5rem] border border-amber-300/20 bg-amber-300/10 p-5 text-sm leading-6 text-amber-50">
              Warm, concise, and multilingual. The tutor mirrors Hindi-English code-mix or another
              language and then guides the user back into practice.
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
