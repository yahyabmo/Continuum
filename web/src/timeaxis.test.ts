import { describe, expect, it } from "vitest";
import shared from "../../tests/timeaxis_cases.json";
import { Grid, rational } from "./timeaxis";

const grids = shared.grids as Record<string, { start: string; step: string; n: number }>;

describe("the contract shared with Python", () => {
  for (const c of shared.cases) {
    it(`${c.grid} at k = ${c.k}`, () => {
      const grid = new Grid(grids[c.grid]);
      const k = rational(c.k);
      const t = rational(c.t);
      const w = rational(c.w);
      expect(grid.time(k)).toBeCloseTo(t, 9);
      expect(grid.index(t)).toBeCloseTo(k, 9);
      expect(grid.tex(t)).toBeCloseTo(w, 9);
      expect(grid.texToTime(w)).toBeCloseTo(t, 9);
    });
  }
});
