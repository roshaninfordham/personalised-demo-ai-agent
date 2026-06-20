export type HealthStatus = {
  status: "ok";
  service: "browser-runtime";
  version: "0.1.0";
};

export function getHealth(): HealthStatus {
  return { status: "ok", service: "browser-runtime", version: "0.1.0" };
}
