import clsx from "clsx";

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-emerald-100 text-emerald-800",
  duplicate: "bg-amber-100 text-amber-800",
  quarantined: "bg-red-100 text-red-800",
  queued: "bg-blue-100 text-blue-800",
  processing: "bg-blue-100 text-blue-800",
  failed: "bg-red-100 text-red-800",
};

const FORMAT_STYLES = "bg-gray-100 text-gray-700";

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize",
        STATUS_STYLES[status] ?? "bg-gray-100 text-gray-700"
      )}
    >
      {status}
    </span>
  );
}

export function FormatBadge({ format }: { format: string | null }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium uppercase tracking-wide",
        FORMAT_STYLES
      )}
    >
      {format || "?"}
    </span>
  );
}
