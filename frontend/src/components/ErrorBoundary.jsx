import React from 'react';
import { AlertTriangle, RotateCcw, ShieldAlert } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Curatorial Error Boundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleResetState = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-archive-alabaster flex items-center justify-center p-6 text-archive-charcoal font-sans">
          <div className="max-w-xl w-full bg-archive-ivory border-2 border-archive-hairline rounded shadow-2xl p-8 space-y-6">
            {/* Header Stamp */}
            <div className="flex items-center justify-between pb-4 border-b border-archive-hairline">
              <div className="flex items-center gap-2 text-rose-700 font-mono text-xs uppercase tracking-stamp font-bold">
                <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                <span>ARCHIVAL SYSTEM // RUNTIME RECOVERY GATE</span>
              </div>
              <span className="font-mono text-[10px] bg-rose-100 text-rose-800 px-2 py-0.5 rounded border border-rose-200">
                CLIENT FAULT MITIGATED
              </span>
            </div>

            {/* Error Monograph Description */}
            <div className="space-y-3">
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-archive-charcoal">
                Registry Interface Encountered an Interruption
              </h2>
              <p className="text-xs sm:text-sm text-archive-stone leading-relaxed bg-archive-alabaster p-4 rounded border border-archive-hairline font-sans">
                The visual verification client caught an unexpected rendering exception. Your local database and session cache remain uncorrupted.
              </p>
            </div>

            {/* Error Message Snippet */}
            {this.state.error && (
              <div className="bg-rose-50 border border-rose-200 p-3.5 rounded font-mono text-xs text-rose-900 overflow-x-auto">
                <div className="text-[10px] uppercase font-bold text-rose-700 mb-1">Exception Trace:</div>
                <code>{this.state.error.toString()}</code>
              </div>
            )}

            {/* Actions */}
            <div className="pt-2 flex flex-col sm:flex-row items-center gap-3">
              <button
                onClick={this.handleReload}
                className="w-full sm:w-auto flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-archive-charcoal hover:bg-black text-white font-mono text-xs uppercase tracking-wider rounded shadow transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5 text-archive-parchment" />
                <span>Reload Registry</span>
              </button>
              <button
                onClick={this.handleResetState}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-white hover:bg-archive-alabaster text-archive-charcoal border border-archive-hairline font-mono text-xs uppercase tracking-wider rounded transition-colors"
              >
                <span>Retry View</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

