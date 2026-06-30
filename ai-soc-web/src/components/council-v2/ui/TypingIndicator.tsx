"use client";

interface TypingIndicatorProps {
  name?: string;
  color?: string;
}

export function TypingIndicator({ name, color = "#60a5fa" }: TypingIndicatorProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 text-xs text-white/40">
      {name && <span style={{ color }}>{name}</span>}
      <span className="flex gap-0.5">
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full"
            style={{
              backgroundColor: color,
              opacity: 0.6,
              animation: `typing-bounce 1.4s ease-in-out ${i * 0.16}s infinite`,
            }}
          />
        ))}
      </span>
      <style jsx>{`
        @keyframes typing-bounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.3; }
          30% { transform: translateY(-4px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
