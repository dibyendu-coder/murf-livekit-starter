'use client';

import { AllowMicToggle } from '@/components/app/allow-mic-toggle';

/** Animated waveform SVG — tutor branding */
function TutorWave() {
  return (
    <svg
      width="72"
      height="48"
      viewBox="0 0 72 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {[
        { x: 6,  h: 18, delay: '0s' },
        { x: 18, h: 36, delay: '0.15s' },
        { x: 30, h: 48, delay: '0.3s' },
        { x: 42, h: 30, delay: '0.45s' },
        { x: 54, h: 42, delay: '0.6s' },
        { x: 66, h: 20, delay: '0.75s' },
      ].map(({ x, h, delay }) => (
        <rect
          key={x}
          x={x - 3}
          y={(48 - h) / 2}
          width="6"
          height={h}
          rx="3"
          fill="currentColor"
          className="animate-float text-amber-400"
          style={{ animationDelay: delay }}
        />
      ))}
    </svg>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="w-full px-4">
      {/* Card */}
      <section className="relative mx-auto flex w-full max-w-sm flex-col items-center overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-white/8 to-white/3 px-8 py-10 text-center shadow-2xl shadow-black/40 backdrop-blur-xl">

        {/* Ambient glow */}
        <div className="pointer-events-none absolute -top-12 left-1/2 h-32 w-32 -translate-x-1/2 rounded-full bg-amber-400/20 blur-3xl" aria-hidden />

        {/* Icon with pulse rings */}
        <div className="relative mb-6 flex items-center justify-center">
          <span className="animate-pulse-ring absolute h-20 w-20 rounded-full bg-amber-400/25" style={{ animationDelay: '0s' }} />
          <span className="animate-pulse-ring absolute h-20 w-20 rounded-full bg-amber-400/15" style={{ animationDelay: '0.6s' }} />
          <span className="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-amber-400 to-amber-500 shadow-xl shadow-amber-500/40">
            <TutorWave />
          </span>
        </div>

        {/* Tutor name */}
        <p className="mb-1 font-mono text-[10px] font-bold tracking-[0.3em] text-amber-300/70 uppercase">
          SpeakEasy Tutor
        </p>

        <h1 className="text-2xl font-bold text-white">Ready to practise?</h1>

        <p className="mt-3 max-w-[22ch] text-sm leading-6 text-white/55">
          Allow microphone access and your AI English tutor will be right with you.
        </p>

        {/* What to expect pills */}
        <div className="mt-5 flex flex-wrap justify-center gap-2">
          {['Speak naturally', 'Get corrections', 'Track progress'].map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-white/12 bg-white/6 px-3 py-1 text-[11px] font-medium text-white/60"
            >
              {tag}
            </span>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-7 flex w-full flex-col gap-3">
          <AllowMicToggle label={startButtonText} onAllowed={onStartCall} />
          <p className="text-[11px] leading-5 text-white/35">
            Your microphone is only active during the session.
          </p>
        </div>
      </section>
    </div>
  );
};
