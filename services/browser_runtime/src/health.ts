export type HealthStatus = {
  status: "ok";
  service: "browser-runtime";
};

export function getHealth(): HealthStatus {
  return { status: "ok", service: "browser-runtime" };
}
