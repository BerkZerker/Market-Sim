import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex items-center justify-center py-20">
          <div className="bg-gray-900 border border-red-800 rounded-lg p-8 max-w-md w-full text-center">
            <h2 className="text-xl font-bold text-red-400 mb-2">
              Something went wrong
            </h2>
            <p className="text-gray-400 text-sm mb-6">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-500 transition text-sm"
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
