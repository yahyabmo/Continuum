import { describe, expect, it } from "vitest";
import { cellUv, planeZ } from "./planes";

describe("cellUv", () => {
  it("puts the first plane in the top left corner", () => {
    expect(cellUv(0, 64, 8)).toEqual({ left: 0, right: 0.125, top: 1, bottom: 0.875 });
  });

  it("moves to the next row after the last column", () => {
    expect(cellUv(9, 64, 8)).toEqual({ left: 0.125, right: 0.25, top: 0.875, bottom: 0.75 });
  });

  it("puts the last plane in the bottom right corner", () => {
    expect(cellUv(63, 64, 8)).toEqual({ left: 0.875, right: 1, top: 0.125, bottom: 0 });
  });
});

describe("planeZ", () => {
  it("is centred and follows the spacing", () => {
    expect(planeZ(0, 3, 2)).toBe(-2);
    expect(planeZ(1, 3, 2)).toBe(0);
    expect(planeZ(2, 3, 2)).toBe(2);
  });
});
