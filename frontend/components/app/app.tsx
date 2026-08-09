'use client';

import { useMemo } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { AutoEnableMic } from '@/components/agents-ui/auto-enable-mic';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

// ---------------------------------------------------------------------------
// Stable caller identity — persisted in localStorage so the agent can
// recognise the same person across separate calls / browser sessions.
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'speakeasy_user_id';

function getOrCreateUserId(): string {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
    // Generate a stable, human-unguessable id
    const newId = `caller_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    localStorage.setItem(STORAGE_KEY, newId);
    return newId;
  } catch {
    // localStorage unavailable (e.g. SSR, private browsing without storage)
    return `caller_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
  }
}

// ---------------------------------------------------------------------------

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const tokenSource = useMemo(() => {
    if (typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string') {
      return getSandboxTokenSource(appConfig);
    }

    // Custom token source that sends the stable user_id so the backend can
    // key the caller memory DB record consistently across sessions.
    return TokenSource.custom(async () => {
      const userId = getOrCreateUserId();
      const res = await fetch('/api/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });
      if (!res.ok) throw new Error(`Token fetch failed: ${res.status}`);
      return res.json();
    });
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />
      {session.isConnected && <AutoEnableMic />}

      {/* Deep indigo + amber ambient bg — matches landing page */}
      <div className="relative min-h-svh overflow-hidden bg-[radial-gradient(ellipse_at_top_left,_oklch(0.25_0.09_265)_0%,_oklch(0.13_0.04_265)_55%,_oklch(0.10_0.05_270)_100%)]">
        {/* Ambient glows */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
          <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-amber-400/10 blur-[90px]" />
          <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-indigo-500/10 blur-[80px]" />
        </div>

        <main className="relative grid h-svh grid-cols-1 place-content-center">
          <ViewController appConfig={appConfig} />
        </main>
      </div>

      <StartAudioButton label="Enable audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
