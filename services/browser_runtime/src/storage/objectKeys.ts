const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const screenIdPattern = /^screen_[a-zA-Z0-9_-]+$/;
const extensions = new Set(["webp", "png", "jpeg"]);

export function screenshotObjectKey(input: {
  organizationId: string;
  demoSessionId: string;
  browserSessionId: string;
  screenId: string;
  extension: string;
}): string {
  assertUuid(input.organizationId);
  assertUuid(input.demoSessionId);
  assertUuid(input.browserSessionId);
  if (!screenIdPattern.test(input.screenId)) {
    throw new Error("Invalid screen_id for object key.");
  }
  if (!extensions.has(input.extension)) {
    throw new Error("Invalid screenshot extension.");
  }
  return `org/${input.organizationId}/sessions/${input.demoSessionId}/browser/${input.browserSessionId}/screenshots/${input.screenId}.${input.extension}`;
}

function assertUuid(value: string): void {
  if (!uuidPattern.test(value)) {
    throw new Error("Invalid UUID for object key.");
  }
}
