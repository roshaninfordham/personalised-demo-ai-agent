export function JsonValidationMessage({ message, tone }: { message: string | null; tone: "error" | "warning" }) {
  if (message === null) return null;
  return <p className={tone === "error" ? "field-error" : "field-warning"}>{message}</p>;
}
