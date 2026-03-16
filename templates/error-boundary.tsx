/**
 * Error Boundary: Catches React render errors with fallback UI
 * Usage:
 *   <ErrorBoundary fallback={<ErrorFallback />}>
 *     <App />
 *   </ErrorBoundary>
 */
"use client";

import { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
    children: ReactNode;
    fallback?: ReactNode;
    onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
        console.error("[ErrorBoundary]", error, errorInfo);
        this.props.onError?.(error, errorInfo);
        // TODO: Report to Sentry
        // Sentry.captureException(error, { extra: { componentStack: errorInfo.componentStack } });
    }

    render(): ReactNode {
        if (this.state.hasError) {
            return this.props.fallback ?? <DefaultErrorFallback error={this.state.error} onRetry={() => this.setState({ hasError: false, error: null })} />;
        }
        return this.props.children;
    }
}

// ---- Default Fallback UI ----

function DefaultErrorFallback({ error, onRetry }: { error: Error | null; onRetry: () => void }) {
    return (
        <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "200px",
            padding: "2rem",
            textAlign: "center",
            gap: "1rem",
        }}>
            <h2 style={{ fontSize: "1.25rem", fontWeight: 600 }}>Something went wrong</h2>
            {error && (
                <p style={{ color: "#6b7280", fontSize: "0.875rem", maxWidth: "400px" }}>
                    {error.message}
                </p>
            )}
            <button
                onClick={onRetry}
                style={{
                    padding: "0.5rem 1.5rem",
                    borderRadius: "0.5rem",
                    border: "1px solid #d1d5db",
                    background: "#fff",
                    cursor: "pointer",
                    fontSize: "0.875rem",
                    fontWeight: 500,
                }}
            >
                Try again
            </button>
        </div>
    );
}
