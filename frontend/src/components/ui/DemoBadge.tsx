import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface DemoBadgeProps {
  label?: string;
  tooltip?: string;
}

export const DemoBadge: React.FC<DemoBadgeProps> = ({
  label = 'DEMO MODE',
  tooltip = 'Running on simulated local telemetry engine. Backend endpoint not connected.',
}) => {
  return (
    <span
      title={tooltip}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono font-semibold bg-amber-50 text-amber-800 border border-amber-200 rounded shadow-xs"
    >
      <ShieldAlert className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
      {label}
    </span>
  );
};
