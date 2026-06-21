import { DemoStartForm } from "../../components/demo-start/DemoStartForm";
import { Card, CardBody } from "../../components/ui/Card";

export default function DemoStartPage() {
  return (
    <main className="page">
      <div className="stack demo-form">
        <div>
          <h1 style={{ marginBottom: 8 }}>Start a live demo session</h1>
          <p className="muted" style={{ marginTop: 0 }}>
            Enter a product URL. Optional guidance and recipe JSON can shape the session when the
            backend supports those records.
          </p>
        </div>
        <Card>
          <CardBody>
            <DemoStartForm />
          </CardBody>
        </Card>
      </div>
    </main>
  );
}
