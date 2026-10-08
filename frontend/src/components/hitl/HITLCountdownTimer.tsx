import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle } from 'lucide-react';

interface HITLCountdownTimerProps {
  timeoutAt: number;
  onTimeout?: () => void;
}

export const HITLCountdownTimer: React.FC<HITLCountdownTimerProps> = ({
  timeoutAt,
  onTimeout,
}) => {
  const targetMs = timeoutAt > 1e11 ? timeoutAt : timeoutAt * 1000;

  const calculateRemaining = () => {
    return Math.max(0, Math.floor((targetMs - Date.now()) / 1000));
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

  // Clean corporate semantic colors
  let colorClass = 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40';

  if (remainingSeconds <= 60) {
    colorClass = 'text-rose-400 bg-rose-950/50 border-rose-800/60';
  } else if (remainingSeconds <= 180) {
    colorClass = 'text-amber-400 bg-amber-950/40 border-amber-800/40';
  }

  return (
    <div className={`px-2.5 py-1 rounded-md border font-mono text-xs flex items-center gap-1.5 font-medium ${colorClass}`}>
      <Clock className="w-3.5 h-3.5" />
      <span>{formatted}</span>
      <span className="text-[10px] text-slate-400">
        {remainingSeconds <= 0 ? '(EXPIRED · FAIL-CLOSED)' : 'REMAINING'}
      </span>
      {remainingSeconds <= 60 && remainingSeconds > 0 && (
        <AlertTriangle className="w-3 h-3 text-rose-400 ml-0.5" />
      )}
    </div>
  );
};
