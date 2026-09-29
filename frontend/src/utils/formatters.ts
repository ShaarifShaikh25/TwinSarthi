export function formatTemp(tempC: number): string {
  const sign = tempC > 0 ? '+' : '';
  return `${sign}${tempC.toFixed(1)}°C`;
}

export function formatDateTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-GB', {
      timeZone: 'UTC',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }) + ' UTC';
  } catch {
    return isoString;
  }
}

export function getStatusBadgeClass(status: string): string {
  switch (status.toUpperCase()) {
    case 'NORMAL':
    case 'SUFFICIENT':
    case 'APPROVED':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200/80';
    case 'WARNING':
    case 'MEDIUM':
    case 'PENDING RESUPPLY':
    case 'MODIFIED':
      return 'bg-amber-50 text-amber-700 border-amber-200/80';
    case 'CRITICAL':
    case 'HIGH':
    case 'CRITICAL SHORTAGE':
    case 'REJECTED':
      return 'bg-rose-50 text-rose-700 border-rose-200/80';
    case 'OFFLINE':
    default:
      return 'bg-slate-100 text-slate-600 border-slate-200';
  }
}

export function getContinuityScoreColor(score: number): string {
  if (score >= 90) return 'text-emerald-700';
  if (score >= 75) return 'text-amber-600';
  return 'text-rose-600';
}
