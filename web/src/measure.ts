/** Frame times of the screen, read from requestAnimationFrame, in milliseconds. */
export interface FrameStats {
  frames: number;
  median: number;
  p95: number;
  slow: number;
}

const BUDGET_MS = 33;

function quantile(sorted: number[], q: number): number {
  return sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))];
}

export function frameStats(deltas: number[]): FrameStats {
  const sorted = [...deltas].sort((a, b) => a - b);
  return {
    frames: sorted.length,
    median: quantile(sorted, 0.5),
    p95: quantile(sorted, 0.95),
    slow: sorted.filter((d) => d > BUDGET_MS).length,
  };
}
