import React from 'react';
import { getStatusBadgeClass } from '../../utils/formatters';

interface BadgeProps {
  status: string;
  label?: string;
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ status, label, size = 'sm' }) => {
  const badgeClass = getStatusBadgeClass(status);
  const sizeClass = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center font-mono font-semibold rounded border uppercase tracking-wider ${badgeClass} ${sizeClass}`}
    >
      {label || status}
    </span>
  );
};
