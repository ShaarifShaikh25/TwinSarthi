import React, { useState } from 'react';
import { Recommendation } from '../../types';
import { useStation } from '../../hooks/useStation';
import { Badge } from './Badge';
import { CheckCircle2, Edit3, XCircle, AlertTriangle, ShieldCheck, X } from 'lucide-react';

interface RecommendationModalProps {
  recommendation: Recommendation | null;
  onClose: () => void;
}

export const RecommendationModal: React.FC<RecommendationModalProps> = ({
  recommendation,
  onClose,
}) => {
  const { handleApproveRecommendation, handleModifyRecommendation, handleRejectRecommendation } =
    useStation();

  const [mode, setMode] = useState<'VIEW' | 'MODIFY' | 'REJECT_REASON'>('VIEW');
  const [modifiedParams, setModifiedParams] = useState<Record<string, any>>({});
  const [rejectReason, setRejectReason] = useState<string>('');
  const [confirmingAction, setConfirmingAction] = useState<string | null>(null);

  if (!recommendation) return null;

  const handleStartModify = () => {
    setModifiedParams(recommendation.parameters ? { ...recommendation.parameters } : {});
    setMode('MODIFY');
  };

  const handleSaveModify = () => {
    handleModifyRecommendation(recommendation.id, modifiedParams);
    onClose();
  };

  const handleConfirmApprove = () => {
    handleApproveRecommendation(recommendation.id);
    onClose();
  };

  const handleConfirmReject = () => {
    handleRejectRecommendation(recommendation.id, rejectReason);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
      <div className="relative w-full max-w-2xl bg-white border border-slate-200 p-6 shadow-xl rounded-lg">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-start gap-3 mb-4">
          <div className="p-2.5 bg-teal-50 text-teal-700 rounded-md border border-teal-200">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-slate-500">{recommendation.id}</span>
              <Badge status={recommendation.status} />
              <Badge status={recommendation.risk} label={`Risk: ${recommendation.risk}`} />
            </div>
            <h3 className="text-lg font-bold text-[#183153]">{recommendation.title}</h3>
            <p className="text-xs text-teal-700 font-mono mt-0.5">{recommendation.category}</p>
          </div>
        </div>

        {/* Content Body */}
        <div className="space-y-4 text-sm text-slate-600 my-4 border-y border-slate-200 py-4">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Recommendation Context
            </h4>
            <p className="bg-slate-50 p-3 rounded border border-slate-200 text-[#183153]">
              {recommendation.description}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-emerald-50/70 p-3 rounded border border-emerald-200">
              <span className="text-xs font-semibold text-emerald-800 uppercase tracking-wider block mb-1">
                Expected Operational Impact
              </span>
              <p className="text-xs text-slate-700">{recommendation.impact}</p>
            </div>
            <div className="bg-amber-50/70 p-3 rounded border border-amber-200">
              <span className="text-xs font-semibold text-amber-800 uppercase tracking-wider block mb-1">
                Suggested Operational Action
              </span>
              <p className="text-xs text-slate-700">{recommendation.suggestedAction}</p>
            </div>
          </div>

          {/* Parameters View / Edit */}
          {recommendation.parameters && (
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Action Parameters
              </h4>
              {mode === 'MODIFY' ? (
                <div className="bg-slate-50 p-3 rounded border border-teal-300 space-y-2">
                  <p className="text-xs text-teal-800 font-mono mb-2">
                    Adjust control variables before approving modification:
                  </p>
                  {Object.entries(modifiedParams).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-3">
                      <label className="text-xs font-mono text-slate-600 w-36 truncate">{key}:</label>
                      <input
                        type={typeof val === 'number' ? 'number' : 'text'}
                        value={val}
                        onChange={(e) =>
                          setModifiedParams({
                            ...modifiedParams,
                            [key]:
                              typeof val === 'number'
                                ? parseFloat(e.target.value) || 0
                                : e.target.value,
                          })
                        }
                        className="flex-1 bg-white border border-slate-300 rounded px-2.5 py-1 text-xs font-mono text-[#183153] focus:outline-none focus:border-teal-600"
                      />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-slate-50 p-2.5 rounded border border-slate-200 font-mono text-xs text-slate-700 space-y-1">
                  {Object.entries(recommendation.parameters).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-slate-200 pb-1">
                      <span className="text-slate-500">{k}:</span>
                      <span className="text-teal-700 font-semibold">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Reject Reason Form */}
          {mode === 'REJECT_REASON' && (
            <div className="bg-rose-50 p-3 rounded border border-rose-200">
              <label className="block text-xs font-semibold text-rose-800 uppercase tracking-wider mb-1">
                Operator Rejection Rationale (Required for NCPOR audit log)
              </label>
              <textarea
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="Specify reason (e.g. Field inspection overrides temperature setpoint)..."
                rows={2}
                className="w-full bg-white border border-rose-300 rounded p-2 text-xs text-[#183153] focus:outline-none focus:border-rose-600"
              />
            </div>
          )}
        </div>

        {/* Confirmation Banner */}
        {confirmingAction && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-300 rounded flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-900 text-xs font-medium">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Confirm execution of action: <strong>{confirmingAction}</strong>?</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  if (confirmingAction === 'APPROVE') handleConfirmApprove();
                  if (confirmingAction === 'MODIFY') handleSaveModify();
                  if (confirmingAction === 'REJECT') handleConfirmReject();
                }}
                className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded"
              >
                Confirm
              </button>
              <button
                onClick={() => setConfirmingAction(null)}
                className="px-3 py-1 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs rounded"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Modal Controls */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
          <div className="text-xs text-slate-400 font-mono">
            Human-in-the-Loop Protocol Required
          </div>

          <div className="flex items-center gap-2">
            {mode === 'VIEW' && (
              <>
                <button
                  onClick={() => setConfirmingAction('APPROVE')}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded shadow transition-colors"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  APPROVE
                </button>
                <button
                  onClick={handleStartModify}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded shadow transition-colors"
                >
                  <Edit3 className="w-4 h-4" />
                  MODIFY
                </button>
                <button
                  onClick={() => setMode('REJECT_REASON')}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded shadow transition-colors"
                >
                  <XCircle className="w-4 h-4" />
                  REJECT
                </button>
              </>
            )}

            {mode === 'MODIFY' && (
              <>
                <button
                  onClick={() => setConfirmingAction('MODIFY')}
                  className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded shadow"
                >
                  Save Modified Action
                </button>
                <button
                  onClick={() => setMode('VIEW')}
                  className="px-3.5 py-1.5 bg-slate-200 text-slate-700 text-xs rounded"
                >
                  Back
                </button>
              </>
            )}

            {mode === 'REJECT_REASON' && (
              <>
                <button
                  onClick={() => setConfirmingAction('REJECT')}
                  className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded shadow"
                >
                  Submit Rejection
                </button>
                <button
                  onClick={() => setMode('VIEW')}
                  className="px-3.5 py-1.5 bg-slate-200 text-slate-700 text-xs rounded"
                >
                  Back
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
