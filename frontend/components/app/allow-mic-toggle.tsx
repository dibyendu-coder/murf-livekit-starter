'use client';

import { useState } from 'react';
import { Loader2, Mic } from 'lucide-react';
import { Toggle } from '@/components/ui/toggle';

interface AllowMicToggleProps {
  label: string;
  onAllowed: () => void;
}

export function AllowMicToggle({ label, onAllowed }: AllowMicToggleProps) {
  const [isAllowed, setIsAllowed] = useState(false);
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
      variant="outline"
      pressed={isAllowed}
      disabled={isRequesting}
      onPressedChange={handlePressedChange}
      aria-label="Allow microphone access"
      className="w-full rounded-full border-white/15 bg-white/5 px-6 text-sm font-semibold text-white hover:bg-white/10"
    >
      {isRequesting ? <Loader2 className="size-4 animate-spin" /> : <Mic className="size-4" />}
      {isRequesting ? 'Requesting mic access...' : label}
    </Toggle>
  );
}
