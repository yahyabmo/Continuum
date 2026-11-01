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

/** Position along the time axis, centred on the middle plane. */
export function planeZ(index: number, count: number, spacing: number): number {
  return (index - (count - 1) / 2) * spacing;
}
