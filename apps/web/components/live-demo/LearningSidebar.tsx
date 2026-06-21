import type { LearningState, LiveDemoEvent } from "../../lib/events/eventTypes";
import { formatClock } from "../../lib/utils/time";
import { Badge } from "../ui/Badge";

export function LearningSidebar({
  learning,
  recentEvents,
}: {
  learning: LearningState;
  recentEvents: LiveDemoEvent[];
}) {
  const milestones = Array.from(learning.milestones.entries());
  const timeline = recentEvents.slice(-100).reverse();
  return (
    <section className="card">
      <div className="card-body stack">
        <div className="panel-title">
          <h2>Learning sidebar</h2>
          <Badge>{String(learning.safeActionCount)} safe actions</Badge>
        </div>
        <div className="timeline">
          {milestones.map(([id, milestone]) => (
            <div key={id} className="timeline-item">
              <div className="row">
                <Badge tone={milestone.completed ? "success" : "neutral"}>
                  {milestone.completed ? "done" : "pending"}
                </Badge>
                <strong>{milestone.label}</strong>
              </div>
              {milestone.updatedAt === undefined ? null : (
                <span className="muted">{formatClock(milestone.updatedAt)}</span>
              )}
            </div>
          ))}
        </div>
        <div className="panel-title">
          <h3>Recent events</h3>
        </div>
        <div className="timeline">
          {timeline.length === 0 ? (
            <div className="empty-state">No events received yet.</div>
          ) : (
            timeline.map((event) => (
              <div key={event.event_id} className="timeline-item">
                <strong>{event.event_type}</strong>
                <div className="muted">{formatClock(event.created_at)}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
