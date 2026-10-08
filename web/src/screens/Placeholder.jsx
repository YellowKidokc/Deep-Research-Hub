export default function Placeholder({ screen, tab }) {
  return (
    <div>
      <h1>{screen.n}. {screen.name} — {tab}</h1>
      <p className="dim">Not built yet. Comes in milestone {screen.build}.</p>
    </div>
  );
}
