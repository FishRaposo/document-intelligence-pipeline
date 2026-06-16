import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  children?: ReactNode;
}

export default function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  children,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-300 bg-gray-50 px-6 py-12 text-center">
      <Icon className="mb-3 h-10 w-10 text-gray-400" />
      <h3 className="text-base font-semibold text-gray-700">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-gray-500">{description}</p>
      )}
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}
