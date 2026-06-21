import { Spinner } from "../../../components/ui/Spinner";

export default function DemoSessionLoading() {
  return (
    <main className="page">
      <div className="row">
        <Spinner />
        <span>Loading session...</span>
      </div>
    </main>
  );
}
