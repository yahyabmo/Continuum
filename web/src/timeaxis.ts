// The browser side of continuum/timeaxis.py. Both read tests/timeaxis_cases.json.

export interface GridData {
  start: string;
  step: string;
  n: number;
}

export function rational(text: string): number {
  const [num, den = "1"] = text.split("/");
  return Number(num) / Number(den);
}

export class Grid {
  readonly start: number;
  readonly step: number;
  readonly n: number;

  constructor(data: GridData) {
    this.start = rational(data.start);
    this.step = rational(data.step);
    this.n = data.n;
  }

  time(k: number): number {
    return this.start + k * this.step;
  }

  index(t: number): number {
    return (t - this.start) / this.step;
  }

  tex(t: number): number {
    return (this.index(t) + 0.5) / this.n;
  }

  texToTime(w: number): number {
    return this.time(w * this.n - 0.5);
  }
}
