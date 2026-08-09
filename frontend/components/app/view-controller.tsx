'use client';

import { useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext } from '@livekit/components-react';
import { Loader2, Phone, RotateCcw } from 'lucide-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

function CallStateCard({
  title,
  description,
  action,
  actionLabel,
  loading = false,
}: {
  title: string;
  description: string;
  action?: () => void;
  actionLabel?: string;
  loading?: boolean;
}) {
  return (
    <section className="relative mx-auto flex w-full max-w-sm flex-col items-center overflow-hidden rounded-3xl border border-white/10 bg-white/6 px-8 py-10 text-center shadow-2xl shadow-black/40 backdrop-blur-xl">
      {/* Amber glow */}
      <div className="pointer-events-none absolute -top-10 left-1/2 h-28 w-28 -translate-x-1/2 rounded-full bg-amber-400/20 blur-3xl" aria-hidden />

      <div className="relative mb-5 flex size-16 items-center justify-center rounded-full bg-gradient-to-br from-amber-400/20 to-amber-500/10 ring-1 ring-amber-400/30">
        {loading
          ? <Loader2 className="size-7 animate-spin text-amber-300" />
          : <Phone className="size-7 text-amber-300" />}
      </div>

      <p className="text-xs font-bold tracking-[0.2em] text-amber-300/60 uppercase">Call status</p>
      <h1 className="mt-2 text-2xl font-bold text-white">{title}</h1>
      <p className="mt-3 text-sm leading-6 text-white/50">{description}</p>

      {action && actionLabel && (
        <button
          type="button"
          onClick={action}
          className="mt-7 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-amber-400 to-amber-500 px-6 py-3 text-sm font-bold text-slate-900 shadow-lg shadow-amber-500/30 transition-all hover:scale-105 hover:shadow-amber-500/50"
        >
          <RotateCcw className="size-4" />
          {actionLabel}
        </button>
      )}
    </section>
  );
}

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const session = useSessionContext();
  const { state: agentState } = useAgent();
  const { resolvedTheme } = useTheme();
  const [hasStarted, setHasStarted] = useState(false);

  const startCall = () => {
    setHasStarted(true);
    void session.start();
  };

  const endCall = () => {
    void session.end();
  };

  const isConnecting = session.connectionState === 'connecting' ||
    (session.isConnected && ['connecting', 'initializing', 'pre-connect-buffering'].includes(agentState));
  const hasEnded = hasStarted && !session.isConnected && session.connectionState === 'disconnected';

  return (
    <AnimatePresence mode="wait">
      {!hasStarted && !session.isConnected && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={startCall}
        />
      )}
      {isConnecting && (
        <motion.div key="connecting" {...VIEW_MOTION_PROPS}>
          <CallStateCard title="Connecting" description="Your voice agent is joining the call. Please wait a moment." loading />
        </motion.div>
      )}
      {hasEnded && (
        <motion.div key="ended" {...VIEW_MOTION_PROPS}>
          <CallStateCard
            title="Call ended"
            description="The conversation is over. You can start a new practice session whenever you are ready."
            action={startCall}
            actionLabel="Start again"
          />
        </motion.div>
      )}
      {session.isConnected && !isConnecting && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
          onEndCall={endCall}
        />
      )}
    </AnimatePresence>
  );
}
