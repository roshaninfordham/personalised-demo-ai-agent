import { notFound } from "next/navigation";

import { LiveDemoShell } from "../../../components/live-demo/LiveDemoShell";

const UUID_LIKE = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

type DemoSessionPageProps = {
  params: Promise<{
    sessionId: string;
  }>;
};

export default async function DemoSessionPage({ params }: DemoSessionPageProps) {
  const { sessionId } = await params;
  if (!UUID_LIKE.test(sessionId)) notFound();

  return (
    <main className="page" style={{ maxWidth: 1480 }}>
      <LiveDemoShell sessionId={sessionId} />
    </main>
  );
}
