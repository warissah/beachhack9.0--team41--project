import { useEffect, useState } from "react";
import { Flame, Hourglass, CheckCircle2, CircleSlash, PauseCircle } from "lucide-react";

type Reflection = "done" | "blocked" | "partial";

interface SessionStripProps {
  taskId: string;
  taskTitle: string;
  nextStepTitle?: string | null;
  sessionActive: boolean;
  sessionTaskId: string | null;
  sessionStartedAt: string | null;
  onStart: () => Promise<void>;
  onEnd: (reflection: Reflection) => Promise<void>;
}

function formatElapsed(startedAt: string | null, now: number): string {
  if (!startedAt) return "0m";
  const started = new Date(startedAt).getTime();
  if (Number.isNaN(started)) return "0m";
  const elapsedSeconds = Math.max(0, Math.floor((now - started) / 1000));
  const hours = Math.floor(elapsedSeconds / 3600);
  const minutes = Math.floor((elapsedSeconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export default function SessionStrip({
  taskId,
  taskTitle,
  nextStepTitle,
  sessionActive,
  sessionTaskId,
  sessionStartedAt,
  onStart,
  onEnd,
}: SessionStripProps) {
  const [now, setNow] = useState(() => Date.now());
  const [ending, setEnding] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showReflection, setShowReflection] = useState(false);
  const [lastReflection, setLastReflection] = useState<Reflection | null>(null);

  const isThisSession = sessionActive && sessionTaskId === taskId;

  useEffect(() => {
    if (!isThisSession) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [isThisSession]);

  useEffect(() => {
    if (!sessionActive) {
      setShowReflection(false);
    }
  }, [sessionActive]);

  useEffect(() => {
    if (lastReflection === null) return;
    const timer = window.setTimeout(() => setLastReflection(null), 4000);
    return () => window.clearTimeout(timer);
  }, [lastReflection]);

  const start = async () => {
    setStarting(true);
    setError(null);
    setLastReflection(null);
    try {
      await onStart();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't start the session.");
    } finally {
      setStarting(false);
    }
  };

  const requestEnd = () => {
    setShowReflection(true);
    setError(null);
  };

  const submitReflection = async (reflection: Reflection) => {
    setEnding(true);
    setError(null);
    try {
      await onEnd(reflection);
      setLastReflection(reflection);
      setShowReflection(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't save the session.");
    } finally {
      setEnding(false);
    }
  };

  if (!sessionActive && lastReflection) {
    const copy = {
      done: "Session logged. That counts.",
      partial: "Session logged. Momentum still matters.",
      blocked: "Session logged. Good catch. Use the coach below to shrink the next step.",
    }[lastReflection];
    return (
      <div className="mt-4 mb-6 rounded-[24px] border border-emerald-200/80 bg-[linear-gradient(135deg,#f7fffb_0%,#eefcf6_100%)] px-5 py-4 shadow-[0_18px_45px_-35px_rgba(16,185,129,0.45)]">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-2xl bg-emerald-500 text-white">
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-700">Focus Logged</p>
            <p className="mt-1 text-sm font-medium text-gray-900">{copy}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`mt-4 mb-6 overflow-hidden rounded-[28px] border px-5 py-4 shadow-[0_22px_70px_-55px_rgba(15,23,42,0.45)] transition-all ${
        isThisSession
          ? "border-amber-300/80 bg-[linear-gradient(135deg,#fff7e8_0%,#fffdf7_100%)]"
          : "border-gray-200/80 bg-[linear-gradient(135deg,#ffffff_0%,#f6f7fb_100%)]"
      }`}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <div className={`flex h-9 w-9 items-center justify-center rounded-2xl ${isThisSession ? "bg-amber-500 text-white" : "bg-gray-900 text-white"}`}>
              <Flame className="h-4 w-4" />
            </div>
            <div>
              <p className={`text-[11px] font-semibold uppercase tracking-[0.18em] ${isThisSession ? "text-amber-700" : "text-gray-500"}`}>
                {isThisSession ? "In Focus" : "Focus Ritual"}
              </p>
              <p className="text-sm font-medium text-gray-900">
                {isThisSession ? "You are in a work block." : "Ready for a focus block?"}
              </p>
            </div>
          </div>
          <div className="mt-3 rounded-2xl bg-white/75 px-4 py-3 ring-1 ring-inset ring-white/60">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400">Current Task</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">{taskTitle}</p>
            {nextStepTitle && (
              <p className="mt-1 text-sm text-gray-600">
                Next move: <span className="font-medium text-gray-800">{nextStepTitle}</span>
              </p>
            )}
            {!isThisSession && <p className="mt-2 text-[12px] text-gray-500">No timer pressure. Just begin.</p>}
          </div>
        </div>

        <div className="sm:w-[250px] sm:flex-shrink-0">
          {isThisSession ? (
            <div className="rounded-2xl border border-amber-200/70 bg-white/80 px-4 py-3">
              <div className="flex items-center gap-2 text-amber-700">
                <Hourglass className="h-4 w-4" />
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em]">Elapsed</span>
              </div>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-gray-900">
                {formatElapsed(sessionStartedAt, now)}
              </p>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={requestEnd}
                  disabled={ending}
                  className="flex-1 rounded-xl bg-gray-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-800 disabled:opacity-50"
                >
                  End Session
                </button>
                <button
                  disabled
                  className="rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-400"
                >
                  Still Working
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={start}
              disabled={starting || sessionActive}
              className="w-full rounded-2xl bg-gray-900 px-4 py-4 text-left text-white shadow-[0_18px_45px_-28px_rgba(17,24,39,0.75)] transition-all hover:-translate-y-0.5 hover:bg-black disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="block text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-300">Start</span>
              <span className="mt-1 block text-base font-semibold">
                {starting ? "Starting session..." : "Begin Session"}
              </span>
            </button>
          )}
        </div>
      </div>

      {showReflection && isThisSession && (
        <div className="mt-4 rounded-2xl border border-gray-200/80 bg-white/80 px-4 py-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500">How did that block go?</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            <button
              onClick={() => submitReflection("done")}
              disabled={ending}
              className="flex items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-3 text-sm font-medium text-emerald-800 transition-colors hover:bg-emerald-100 disabled:opacity-50"
            >
              <CheckCircle2 className="h-4 w-4" />
              Done
            </button>
            <button
              onClick={() => submitReflection("partial")}
              disabled={ending}
              className="flex items-center justify-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-3 text-sm font-medium text-amber-800 transition-colors hover:bg-amber-100 disabled:opacity-50"
            >
              <PauseCircle className="h-4 w-4" />
              Partial
            </button>
            <button
              onClick={() => submitReflection("blocked")}
              disabled={ending}
              className="flex items-center justify-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-3 text-sm font-medium text-rose-800 transition-colors hover:bg-rose-100 disabled:opacity-50"
            >
              <CircleSlash className="h-4 w-4" />
              Blocked
            </button>
          </div>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-red-500">{error}</p>}
      {sessionActive && !isThisSession && (
        <p className="mt-3 text-[12px] text-gray-500">Another session is already running. Finish it before starting a new one.</p>
      )}
    </div>
  );
}
