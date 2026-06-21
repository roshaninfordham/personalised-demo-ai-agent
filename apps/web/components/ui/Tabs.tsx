"use client";

import { useState, type ReactNode } from "react";

export type TabItem = {
  id: string;
  label: string;
  content: ReactNode;
};

export function Tabs({ tabs, initialTabId }: { tabs: TabItem[]; initialTabId?: string }) {
  const firstTab = tabs[0];
  const [activeId, setActiveId] = useState(initialTabId ?? firstTab?.id ?? "");
  const activeTab = tabs.find((tab) => tab.id === activeId) ?? firstTab;

  return (
    <div className="stack">
      <div className="tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className="button button-secondary tab-button"
            role="tab"
            aria-selected={tab.id === activeId}
            onClick={() => {
              setActiveId(tab.id);
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div role="tabpanel">{activeTab?.content}</div>
    </div>
  );
}
