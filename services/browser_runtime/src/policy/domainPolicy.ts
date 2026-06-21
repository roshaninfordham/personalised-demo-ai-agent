export function isDomainAllowed(url: string, allowedDomains: string[]): boolean {
  if (allowedDomains.length === 0) return false;
  try {
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol)) return false;
    const host = parsed.hostname.toLowerCase().replace(/\.$/u, "");
    return allowedDomains.some((domain) => {
      const normalized = domain.toLowerCase();
      if (normalized.startsWith("*.")) return host.endsWith(`.${normalized.slice(2)}`);
      return host === normalized;
    });
  } catch {
    return false;
  }
}
