const docs = [
  ["Local setup", "/docs/setup/local-setup.md"],
  ["Architecture", "/docs/architecture/system-design.md"],
  ["Provider switching", "/docs/providers/provider-switching.md"],
  ["Demo recipe guide", "/docs/recipes/demo-recipe-guide.md"],
  ["Troubleshooting", "/docs/troubleshooting/troubleshooting.md"],
  ["Interview demo script", "/docs/demo/interview-demo-script.md"],
] as const;

export default function DocsPage() {
  return (
    <main className="page stack">
      <div className="page-heading">
        <div>
          <h1>Docs</h1>
          <p className="muted">
            Documentation lives in the repository. These links point to local Markdown paths for
            engineers running the project from a checkout.
          </p>
        </div>
      </div>
      <section className="status-grid">
        {docs.map(([label, path]) => (
          <div className="card" key={path}>
            <div className="card-body stack">
              <h2>{label}</h2>
              <code>{path}</code>
            </div>
          </div>
        ))}
      </section>
    </main>
  );
}
