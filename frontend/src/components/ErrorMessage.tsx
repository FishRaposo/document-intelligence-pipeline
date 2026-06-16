import { AlertCircle } from "lucide-react";

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
    >
      <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-400" />
      <div className="flex-1">
        <p className="font-medium text-red-800">Unable to load data</p>
        <p className="mt-0.5 text-red-600">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg border border-red-300 bg-white px-3 py-1.5 text-xs font-medium text-red-700 transition-colors hover:bg-red-100"
        >
          Retry
        </button>
      )}
    </div>
  );
}
