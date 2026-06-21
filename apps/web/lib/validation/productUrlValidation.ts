export type UrlValidationResult = {
  valid: boolean;
  normalizedUrl?: string;
  error?: string;
  warning?: string;
};

const forbiddenSchemes = new Set(["javascript:", "file:", "data:", "mailto:", "ftp:"]);

export function validateProductUrl(value: string, allowLocal = false): UrlValidationResult {
  const trimmed = value.trim();
  if (trimmed.length === 0) return { valid: false, error: "Product URL is required." };
  if (trimmed.length > 2048) return { valid: false, error: "Product URL is too long." };
  try {
    const parsed = new URL(trimmed);
    parsed.hash = "";
    parsed.protocol = parsed.protocol.toLowerCase();
    parsed.hostname = parsed.hostname.toLowerCase();
    if (forbiddenSchemes.has(parsed.protocol) || !["http:", "https:"].includes(parsed.protocol)) {
      return { valid: false, error: "Use an http or https URL." };
    }
    if (parsed.username || parsed.password) {
      return { valid: false, error: "URLs with embedded credentials are not allowed." };
    }
    const localWarning = isLocalHost(parsed.hostname) && !allowLocal;
    const result: UrlValidationResult = { valid: true, normalizedUrl: parsed.toString() };
    if (localWarning) {
      result.warning = "Local/private URLs are only allowed in local development.";
    }
    return result;
  } catch {
    return { valid: false, error: "Enter a valid URL." };
  }
}

function isLocalHost(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "::1" ||
    hostname.startsWith("10.") ||
    hostname.startsWith("192.168.") ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
  );
}
