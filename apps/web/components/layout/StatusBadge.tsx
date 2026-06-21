import { Badge } from "../ui/Badge";

export function StatusBadge({
  status,
  tone = "neutral",
}: {
  status: string;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  return <Badge tone={tone}>{status}</Badge>;
}
