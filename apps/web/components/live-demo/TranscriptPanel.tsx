"use client";

import { useEffect, useRef, useState } from "react";

import type { TranscriptItem } from "../../lib/events/eventTypes";
import { formatClock } from "../../lib/utils/time";
import { Badge } from "../ui/Badge";
import { EmptyState } from "./EmptyState";

export function TranscriptPanel({ items, debug = false }: { items: TranscriptItem[]; debug?: boolean }) {
  const listRef = useRef<HTMLDivElement | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [newMessages, setNewMessages] = useState(false);

  useEffect(() => {
    const node = listRef.current;
    if (node === null) return;
    if (autoScroll) {
      node.scrollTop = node.scrollHeight;
      setNewMessages(false);
    } else {
      setNewMessages(true);
    }
  }, [autoScroll, items.length]);

  function handleScroll(): void {
    const node = listRef.current;
    if (node === null) return;
    const atBottom = node.scrollHeight - node.scrollTop - node.clientHeight < 80;
    setAutoScroll(atBottom);
    if (atBottom) setNewMessages(false);
  }

  return (
    <section className="card">
      <div className="card-body stack">
        <div className="panel-title">
          <h2>Transcript</h2>
          <Badge>{String(items.length)} events</Badge>
        </div>
        <div ref={listRef} className="transcript-list" onScroll={handleScroll}>
          {items.length === 0 ? (
            <EmptyState title="No transcript yet">Partial and final transcript events will appear here.</EmptyState>
          ) : (
            items.map((item) => (
              <article key={item.transcriptEventId} className="transcript-item">
                <div className="row">
                  <strong>{item.speaker}</strong>
                  <Badge tone={item.chunkType === "interrupted" ? "warning" : "neutral"}>{item.chunkType}</Badge>
                  <span className="muted">{formatClock(item.createdAt)}</span>
                </div>
                <p>{item.text}</p>
                {debug && item.confidence !== undefined ? (
                  <span className="muted">confidence {item.confidence.toFixed(2)}</span>
                ) : null}
              </article>
            ))
          )}
        </div>
        {newMessages ? (
          <button
            type="button"
            className="button button-secondary"
            onClick={() => {
              setAutoScroll(true);
              const node = listRef.current;
              if (node !== null) node.scrollTop = node.scrollHeight;
            }}
          >
            New messages
          </button>
        ) : null}
      </div>
    </section>
  );
}
