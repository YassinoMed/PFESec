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
  // Géométrie de la jauge circulaire
  const size = 128;
  const stroke = 4;
  const r = 56;
  const c = 2 * Math.PI * r;
  const offset = c - (stability / 100) * c;

  return (
    <section className="stitch-glass-panel flex flex-1 flex-col overflow-hidden rounded-xl">
      {/* Header */}
      <div
        className="border-b px-5 py-4"
        style={{
          backgroundColor: "rgba(40, 41, 51, 0.5)",
          borderColor: "rgba(60, 73, 78, 0.3)",
        }}
      >
        <h2 className="flex items-center gap-2 text-lg font-semibold">
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

      <div className="flex flex-1 flex-col gap-4 p-5">
        {/* Jauge circulaire STABILITY */}
        <div className="flex items-center justify-center py-4">
          <div
            className="relative flex items-center justify-center rounded-full border-4"
            style={{
              width: size,
              height: size,
              borderColor: "var(--stitch-container-highest)",
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
              <div className="text-3xl font-bold" style={{ color: "var(--stitch-on-surface)" }}>
                {stability}
                <span className="text-sm">%</span>
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

        {/* Matrice de vote */}
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
    bg: "rgba(56, 56, 67, 1)",
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
      className="flex items-center justify-between rounded border p-2"
      style={{
        backgroundColor: "rgba(51, 52, 62, 0.4)",
        borderColor: "rgba(60, 73, 78, 0.2)",
      }}
    >
      <span className="sentinel-mono text-sm" style={{ color: "var(--stitch-on-surface)" }}>
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
