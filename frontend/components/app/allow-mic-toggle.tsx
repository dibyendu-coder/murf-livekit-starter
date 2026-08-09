'use client';

import { useState } from 'react';
import { Loader2, Mic } from 'lucide-react';
import { Toggle } from '@/components/ui/toggle';

interface AllowMicToggleProps {
  label: string;
  onAllowed: () => void;
}

export function AllowMicToggle({ label, onAllowed }: AllowMicToggleProps) {
  const [isAllowed, setIsAllowed]     = useState(false);
  const [isRequesting, setIsRequesting] = useState(false);

  const handlePressedChange = async (nextPressed: boolean) => {
    if (isAllowed || !nextPressed || isRequesting) {
      return;
    }

    try {
      setIsRequesting(true);
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setIsAllowed(true);
      onAllowed();
    } catch (error) {
      console.warn('AllowMicToggle: microphone permission was not granted', error);
      setIsAllowed(false);
    } finally {
      setIsRequesting(false);
    }
  };

  return (
    <Toggle
      size="lg"
      pressed={isAllowed}
      disabled={isRequesting}
      onPressedChange={handlePressedChange}
      aria-label="Allow microphone access"
      className={[
        'w-full rounded-full px-6 text-sm font-bold transition-all duration-300',
        isAllowed
          ? 'bg-gradient-to-r from-amber-400 to-amber-500 text-slate-900 shadow-lg shadow-amber-500/40'
          : 'border border-amber-400/30 bg-amber-400/10 text-amber-200 hover:bg-amber-400/20 hover:text-amber-100',
        isRequesting ? 'cursor-wait opacity-70' : '',
      ].join(' ')}
    >
      {isRequesting
        ? <Loader2 className="size-4 animate-spin" />
        : <Mic className="size-4" />}
      {isRequesting ? 'Requesting mic access…' : label}
    </Toggle>
  );
}
