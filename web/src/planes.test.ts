import { describe, expect, it } from "vitest";
import { cellUv, colorFromQuery, planeZ, viewFromQuery } from "./planes";

describe("viewFromQuery", () => {
  it("reads the whole image view", () => {
    expect(viewFromQuery("image")).toBe("image");
  });

  it("shows the object by default", () => {
    expect(viewFromQuery(null)).toBe("objet");
    expect(viewFromQuery("autre")).toBe("objet");
  });
});

describe("colorFromQuery", () => {
  it("reads a colour", () => {
    expect(colorFromQuery("FFAA00", "#000000")).toBe("#ffaa00");
  });

  it("keeps the default without a valid colour", () => {
    expect(colorFromQuery(null, "#000000")).toBe("#000000");
    expect(colorFromQuery("rouge", "#000000")).toBe("#000000");
    expect(colorFromQuery("fff", "#000000")).toBe("#000000");
  });
});

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
