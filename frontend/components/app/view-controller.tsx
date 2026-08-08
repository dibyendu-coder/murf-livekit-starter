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
    <section className="mx-auto flex w-full max-w-md flex-col items-center rounded-3xl border bg-card p-8 text-center shadow-sm">
      <div className="mb-5 flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
        {loading ? <Loader2 className="size-6 animate-spin" /> : <Phone className="size-6" />}
      </div>
      <p className="text-xs font-bold tracking-[0.2em] text-muted-foreground uppercase">Call status</p>
      <h1 className="mt-2 text-2xl font-semibold">{title}</h1>
      <p className="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
      {action && actionLabel && (
        <button
          type="button"
          onClick={action}
          className="mt-7 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
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
