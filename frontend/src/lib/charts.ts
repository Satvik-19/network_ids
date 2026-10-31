export const RISK_DOMAIN: [number, number] = [0, 100];
export function signedContributions(values: number[]) {
  const extent = Math.max(...values.map(Math.abs), 0) || 1;
  return { extent, bars: values.map(value => ({
    left: value < 0 ? 50 + value / extent * 50 : 50,
    width: Math.abs(value) / extent * 50,
  })) };
}
