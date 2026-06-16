import { AtSign, Link2, Phone, Tag } from "lucide-react";
import type { DocumentEntities } from "@/types";

const GROUPS: {
  key: keyof DocumentEntities;
  label: string;
  icon: typeof AtSign;
}[] = [
  { key: "capitalised", label: "Names", icon: Tag },
  { key: "emails", label: "Emails", icon: AtSign },
  { key: "urls", label: "URLs", icon: Link2 },
  { key: "phones", label: "Phones", icon: Phone },
];

export default function EntityList({ entities }: { entities: DocumentEntities }) {
  const total =
    entities.emails.length +
    entities.urls.length +
    entities.phones.length +
    entities.capitalised.length;

  if (total === 0) {
    return (
      <p className="text-sm text-gray-400">No entities extracted.</p>
    );
  }

  return (
    <div className="space-y-3">
      {GROUPS.map(({ key, label, icon: Icon }) => {
        const values = entities[key];
        if (!values || values.length === 0) return null;
        return (
          <div key={key}>
            <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
              <Icon className="h-3.5 w-3.5" />
              {label}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {values.map((v) => (
                <span
                  key={v}
                  className="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                >
                  {v}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
