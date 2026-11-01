export interface Layout {
  columns: number;
  width: number;
  height: number;
}

/** Corners of a cell of the atlas in UV space, the origin being at the bottom left. */
export function cellUv(index: number, count: number, columns: number) {
  const rows = Math.ceil(count / columns);
  const column = index % columns;
  const row = Math.floor(index / columns);
  return {
    left: column / columns,
    right: (column + 1) / columns,
    top: 1 - row / rows,
    bottom: 1 - (row + 1) / rows,
  };
}

/** Colour given in the address of the page, such as ?fond=ffffff. */
export function colorFromQuery(value: string | null, fallback: string): string {
  return value && /^[0-9a-f]{6}$/i.test(value) ? `#${value.toLowerCase()}` : fallback;
}

/** Position along the time axis, centred on the middle plane. */
export function planeZ(index: number, count: number, spacing: number): number {
  return (index - (count - 1) / 2) * spacing;
}
