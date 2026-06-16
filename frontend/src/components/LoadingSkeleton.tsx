export function CardSkeleton() {
  return (
    <div className="card animate-pulse">
      <div className="space-y-3">
        <div className="h-4 w-1/3 rounded bg-gray-200" />
        <div className="h-3 w-full rounded bg-gray-100" />
        <div className="h-3 w-2/3 rounded bg-gray-100" />
      </div>
    </div>
  );
}

export function ListItemSkeleton() {
  return (
    <div className="card flex animate-pulse items-center justify-between">
      <div className="space-y-2">
        <div className="h-4 w-48 rounded bg-gray-200" />
        <div className="h-3 w-32 rounded bg-gray-100" />
      </div>
      <div className="flex items-center gap-3">
        <div className="h-5 w-16 rounded-full bg-gray-100" />
        <div className="h-4 w-12 rounded bg-gray-100" />
      </div>
    </div>
  );
}

export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3" data-testid="list-skeleton">
      {Array.from({ length: rows }).map((_, i) => (
        <ListItemSkeleton key={i} />
      ))}
    </div>
  );
}

export function ChunkSkeleton() {
  return (
    <div className="card animate-pulse space-y-2">
      <div className="h-3 w-20 rounded bg-gray-200" />
      <div className="h-3 w-full rounded bg-gray-100" />
      <div className="h-3 w-5/6 rounded bg-gray-100" />
      <div className="h-3 w-4/6 rounded bg-gray-100" />
    </div>
  );
}
