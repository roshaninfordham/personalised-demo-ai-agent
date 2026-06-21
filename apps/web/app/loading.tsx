import { Spinner } from "../components/ui/Spinner";

export default function Loading() {
  return (
    <main className="page">
      <div className="row">
        <Spinner />
        <span>Loading frontend shell...</span>
      </div>
    </main>
  );
}
