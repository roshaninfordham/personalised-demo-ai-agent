export function confirmationRequired(riskLevel: string, confirmed: boolean): boolean {
  return riskLevel === "high" && !confirmed;
}
