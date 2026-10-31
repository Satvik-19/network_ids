export function isAnomalyFlagged(
  score: number | null | undefined,
  threshold: number | null | undefined,
): boolean | null {
  if (score == null || threshold == null || !Number.isFinite(score) || !Number.isFinite(threshold)) return null;
  return score < threshold;
}

export function unknownExplanation(label: string | null | undefined): string {
  const prediction = label === "BENIGN"
    ? "The supervised classifier predicted benign traffic."
    : label
      ? `The supervised classifier predicted ${label} without sufficient confidence for a known-attack decision.`
      : "The supervised classifier did not confidently identify a known attack.";
  return `${prediction} The anomaly detector flagged behavior outside its learned benign baseline, so the hybrid IDS escalated it as suspicious.`;
}

export function scenarioOutcome(truth: string, classification: string): string {
  const alert = classification !== "BENIGN";
  return truth === "BENIGN"
    ? alert ? "False alert" : "Correct benign"
    : alert ? "Detected threat" : "Missed threat";
}
