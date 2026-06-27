"use client";

export function DecisionJournal({
  title,
  summary,
  details,
}: {
  title: string;
  summary: string;
  details?: string;
}) {
  return (
    <section className="stitch-glass-panel stitch-animate-in stitch-delay-300 flex flex-[0.8] flex-col overflow-hidden rounded-xl">
      {/* Header */}
      <div
        className="flex items-center gap-2 border-b px-4 py-3"
        style={{
          backgroundColor: "rgba(51, 52, 62, 0.6)",
          borderColor: "rgba(60, 73, 78, 0.3)",
        }}
      >
        <span style={{ color: "var(--stitch-error)" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path
              d="M4 4h16v16H4zM8 8h8M8 12h6M8 16h4"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <h2 className="sentinel-headline">Decision Journal</h2>
      </div>

      {/* Body */}
      <div
        className="stitch-panel-body flex flex-col gap-2"
        style={{
          fontSize: "14px",
          lineHeight: "1.5",
        }}
      >
        <div style={{ color: "var(--stitch-on-surface)" }}>
          <span className="font-bold" style={{ color: "var(--stitch-error)" }}>
            {title}:
          </span>{" "}
          {summary}
        </div>
        {details && (
          <div
            className="mt-1"
            style={{
              color: "var(--stitch-on-surface-variant)",
              fontSize: "13px",
            }}
          >
            {details}
          </div>
        )}
      </div>
    </section>
  );
}
