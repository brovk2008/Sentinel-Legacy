import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle } from 'lucide-react';

interface HITLCountdownTimerProps {
  timeoutAt: number; // Unix timestamp in seconds or milliseconds
  onTimeout?: () => void;
}

export const HITLCountdownTimer: React.FC<HITLCountdownTimerProps> = ({
  timeoutAt,
  onTimeout,
}) => {
  // Normalize timeout timestamp to milliseconds
  const targetMs = timeoutAt > 1e11 ? timeoutAt : timeoutAt * 1000;

  const calculateRemaining = () => {
    const diff = Math.max(0, Math.floor((targetMs - Date.now()) / 1000));
    return diff;
  };

  const [remainingSeconds, setRemainingSeconds] = useState(calculateRemaining());

  useEffect(() => {
    const interval = setInterval(() => {
      const remaining = calculateRemaining();
      setRemainingSeconds(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        if (onTimeout) onTimeout();
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [targetMs, onTimeout]);

  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  const formatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  // Color dynamics: green > 180s, amber > 60s, red <= 60s
  let colorClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  let pulse = false;

  if (remainingSeconds <= 60) {
    colorClass = 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    pulse = true;
  } else if (remainingSeconds <= 180) {
    colorClass = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
  }

  return (
    <div className={`px-2.5 py-1 rounded-lg border font-mono text-xs flex items-center gap-1.5 font-bold ${colorClass}`}>
      <Clock className={`w-3.5 h-3.5 ${pulse ? 'animate-spin' : ''}`} />
      <span>{formatted}</span>
      <span className="text-[10px] font-normal text-slate-400">
        {remainingSeconds <= 0 ? '(EXPIRED / FAIL-CLOSED)' : 'REMAINING'}
      </span>
      {remainingSeconds <= 60 && remainingSeconds > 0 && (
        <AlertTriangle className="w-3.5 h-3.5 text-rose-400 animate-bounce ml-0.5" />
      )}
    </div>
  );
};
