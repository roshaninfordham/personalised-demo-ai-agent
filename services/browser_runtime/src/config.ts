export type ServiceSettings = {
  app_env: string;
  log_level: string;
  port: number;
};

function readInteger(value: string | undefined, fallback: number): number {
  if (value === undefined || value.trim() === "") {
    return fallback;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? fallback : parsed;
}

export function getSettings(env: NodeJS.ProcessEnv = process.env): ServiceSettings {
  return {
    app_env: env.APP_ENV ?? "local",
    log_level: env.LOG_LEVEL ?? "info",
    port: readInteger(env.BROWSER_RUNTIME_PORT, 8010),
  };
}
