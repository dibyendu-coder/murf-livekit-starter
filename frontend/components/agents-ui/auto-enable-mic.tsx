"use client";

import { useEffect } from 'react';
import { useTrackToggle } from '@livekit/components-react';
import { Track } from 'livekit-client';

export function AutoEnableMic() {
  const micToggle = useTrackToggle({ source: Track.Source.Microphone });

  useEffect(() => {
    let mounted = true;

    const enableMic = async () => {
      if (!mounted) return;

      try {
        // Prompt for microphone permission
        await navigator.mediaDevices.getUserMedia({ audio: true });
        // Toggle microphone on
        await micToggle.toggle(true);
      } catch (err) {
        // Permission denied or other error; log for debugging
        // eslint-disable-next-line no-console
        console.warn('AutoEnableMic: could not enable microphone', err);
      }
    };

    enableMic();

    return () => {
      mounted = false;
    };
  }, [micToggle]);

  return null;
}
