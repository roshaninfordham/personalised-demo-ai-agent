"use client";

import { useEffect, useState } from "react";

import type { DemoSessionStateResponse } from "@live-demo-agent/contracts";
import { getDemoSessionState } from "../lib/api/demoSessionsApi";
import { isApiClientError } from "../lib/api/apiErrors";

export type DemoSessionLoadState =
  | { status: "idle" | "loading" }
  | { status: "loaded"; data: DemoSessionStateResponse }
  | { status: "failed"; message: string };

export function useDemoSession(sessionId: string): DemoSessionLoadState {
  const [state, setState] = useState<DemoSessionLoadState>({ status: "idle" });
  useEffect(() => {
    let active = true;
    setState({ status: "loading" });
    void getDemoSessionState(sessionId)
      .then((data) => {
        if (active) setState({ status: "loaded", data });
      })
      .catch((error: unknown) => {
        if (!active) return;
        setState({
          status: "failed",
          message: isApiClientError(error) ? error.apiError.message : "Session state is unavailable.",
        });
      });
    return () => {
      active = false;
    };
  }, [sessionId]);
  return state;
}
