"use client";

export interface Vote {
  expert: string;
  verdict: "CONFIRM" | "UNCERTAIN" | "REJECT";
}

export function ConsensusEnginePanel({
  stability,
  votes,
}: {
  stability: number; // 0..100
  votes: Vote[];
}) {
  // Géométrie de la jauge — w-28 h-28 (112px) du design Stitch
  const size = 112;
  const stroke = 4;
  const r = 48;
  const c = 2 * Math.PI * r;
  const offset = c - (stability / 100) * c;

  return (
    <section className="stitch-glass-panel stitch-animate-in stitch-delay-300 flex flex-[1.2] flex-col overflow-hidden rounded-xl">
      {/* Header */}
      <div className="stitch-panel-header">
        <h2 className="sentinel-headline flex items-center gap-2">
          <span style={{ color: "var(--stitch-secondary)" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path
                d="M8 12h8M12 8v8M3 12a9 9 0 1018 0 9 9 0 00-18 0z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </span>
          Consensus Engine
        </h2>
      </div>

      <div className="stitch-panel-body sentinel-scroll flex flex-1 flex-col gap-4 overflow-y-auto">
        {/* Jauge circulaire STABILITY — exact du design */}
        <div className="flex items-center justify-center py-2">
          <div
            className="relative flex items-center justify-center rounded-full border-4"
            style={{
              width: size,
              height: size,
              borderColor: "rgba(51, 52, 62, 0.5)",
              boxShadow: "inset 0 0 20px rgba(0,0,0,0.5)",
            }}
          >
            <svg className="absolute inset-0 h-full w-full -rotate-90">
              <circle
                cx={size / 2}
                cy={size / 2}
                r={r}
                fill="none"
                stroke="var(--stitch-primary)"
                strokeWidth={stroke}
                strokeDasharray={c}
                strokeDashoffset={offset}
                strokeLinecap="round"
                style={{
                  transition: "stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1)",
                  filter: "drop-shadow(0 0 8px rgba(0,209,255,0.8))",
                }}
              />
            </svg>
            <div className="text-center">
              <div
                style={{
                  fontFamily: "var(--font-inter), 'Inter', system-ui, sans-serif",
                  fontSize: "32px",
                  fontWeight: 700,
                  lineHeight: 1.2,
                  letterSpacing: "-0.02em",
                  color: "var(--stitch-on-surface)",
                }}
              >
                {stability}
                <span style={{ fontSize: "14px" }}>%</span>
              </div>
              <div
                className="sentinel-caps"
                style={{ color: "var(--stitch-on-surface-variant)" }}
              >
                Stability
              </div>
            </div>
          </div>
        </div>

        {/* Voting Matrix — backdrop-blur-sm sur chaque row */}
        <div className="mt-2 flex flex-col gap-2">
          {votes.map((vote, i) => (
            <VoteRow key={i} vote={vote} />
          ))}
        </div>
      </div>
    </section>
  );
}

const verdictStyle: Record<Vote["verdict"], { bg: string; color: string; border: string }> = {
  CONFIRM: {
    bg: "rgba(164, 230, 255, 0.2)",
    color: "var(--stitch-primary)",
    border: "rgba(164, 230, 255, 0.3)",
  },
  UNCERTAIN: {
    bg: "rgba(56, 56, 67, 0.5)",
    color: "var(--stitch-on-surface-variant)",
    border: "rgba(60, 73, 78, 0.5)",
  },
  REJECT: {
    bg: "rgba(255, 180, 171, 0.15)",
    color: "var(--stitch-error)",
    border: "rgba(255, 180, 171, 0.4)",
  },
};

function VoteRow({ vote }: { vote: Vote }) {
  const s = verdictStyle[vote.verdict];
  return (
    <div
      className="stitch-glass-micro flex items-center justify-between rounded border p-2"
      style={{
        backgroundColor: "rgba(51, 52, 62, 0.4)",
        borderColor: "rgba(60, 73, 78, 0.2)",
      }}
    >
      <span className="sentinel-mono" style={{ color: "var(--stitch-on-surface)" }}>
        {vote.expert}
      </span>
      <span
        className="sentinel-caps rounded border px-2 py-1"
        style={{ backgroundColor: s.bg, color: s.color, borderColor: s.border }}
      >
        {vote.verdict}
      </span>
    </div>
  );
}
