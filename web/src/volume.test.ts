import { describe, expect, it } from "vitest";
import { frameStats } from "./measure";
import { gunzip, sliceOpacity } from "./volume";

describe("gunzip", () => {
  const raw = new Uint8Array([1, 2, 3, 250]);

  it("decompresses a gzip file", async () => {
    const packed = new Blob([raw]).stream().pipeThrough(new CompressionStream("gzip"));
    expect(await gunzip(await new Response(packed).arrayBuffer())).toEqual(raw);
  });

  it("keeps bytes the server already decompressed", async () => {
    expect(await gunzip(raw.buffer)).toEqual(raw);
  });
});

describe("sliceOpacity", () => {
  it("keeps the setting when there are as many slices as planes", () => {
    expect(sliceOpacity(0.45, 64)).toBeCloseTo(0.45, 12);
  });

  it("makes the whole stack as opaque as the 64 planes", () => {
    const one = sliceOpacity(0.45, 300);
    expect(1 - Math.pow(1 - one, 300)).toBeCloseTo(1 - Math.pow(0.55, 64), 12);
    expect(one).toBeLessThan(0.45);
  });
});

describe("frameStats", () => {
  it("reads the median, the 95th percentile and the slow frames", () => {
    const deltas = [...Array(95).fill(16.7), ...Array(5).fill(50)];
    const stats = frameStats(deltas);
    expect(stats).toMatchObject({ frames: 100, median: 16.7, p95: 50, slow: 5, longest: 50 });
    expect(stats.seconds).toBeCloseTo((95 * 16.7 + 5 * 50) / 1000, 9);
  });
});
