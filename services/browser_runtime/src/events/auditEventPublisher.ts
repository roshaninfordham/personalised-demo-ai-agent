export type AuditEventPayload = {
  action: string;
  resource_type: string;
  resource_id?: string | null;
  risk_level?: string | null;
  policy_decision?: string | null;
  reason_codes: string[];
  metadata: Record<string, unknown>;
};

export class AuditEventPublisher {
  public events: AuditEventPayload[] = [];

  publish(payload: AuditEventPayload): void {
    this.events.push({ ...payload, metadata: { ...payload.metadata } });
  }
}
