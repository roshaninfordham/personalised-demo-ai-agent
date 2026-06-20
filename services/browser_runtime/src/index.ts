import { createServer } from "node:http";

import { getSettings } from "./config.js";
import { getHealth } from "./health.js";

export async function startServer(): Promise<void> {
  const settings = getSettings();

  const server = createServer((request, response) => {
    if (request.url === "/healthz") {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify(getHealth()));
      return;
    }

    response.writeHead(404, { "content-type": "application/json" });
    response.end(JSON.stringify({ error: "not_found" }));
  });

  await new Promise<void>((resolve) => {
    server.listen(settings.port, "0.0.0.0", resolve);
  });

  console.log(
    `Browser runtime skeleton listening on port ${String(settings.port)}. Browser automation is not implemented in Phase 1.`,
  );
}

void startServer();
