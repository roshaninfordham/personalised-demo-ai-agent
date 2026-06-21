import { rbacPermissions } from "@live-demo-agent/policies";

export function hasPermission(role: string, permission: string): boolean {
  const permissions = new Set(
    (rbacPermissions.roles as Record<string, readonly string[]>)[role] ?? [],
  );
  if (permissions.has("*") || permissions.has(permission)) return true;
  const resource = permission.split(":", 1)[0];
  if (!resource) return false;
  return permissions.has(`${resource}:*`);
}
