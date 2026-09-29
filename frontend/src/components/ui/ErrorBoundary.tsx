import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('POLAR-TWIN UI ErrorBoundary caught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="p-6 m-4 bg-slate-900 border border-rose-800/80 rounded-lg text-slate-100 font-mono space-y-4">
          <div className="flex items-center gap-3 text-rose-400">
            <AlertTriangle className="w-6 h-6" />
            <h2 className="text-base font-bold uppercase tracking-wider">UI Render Error Shield Active</h2>
          </div>
          <p className="text-xs text-slate-300">
            A component exception occurred: <span className="text-rose-300 font-bold">{this.state.error?.message}</span>
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="flex items-center gap-2 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold rounded shadow transition-colors"
          >
            <RefreshCw className="w-4 h-4" /> Reset View Context
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
