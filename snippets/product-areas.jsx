export const ProductAreas = () => {
  const run = ["p", "p", "f", "p", "p", "p", "f", "p", "p"];
  const live = Array.from({ length: 18 }, (_, i) => (i === 13 ? "f" : ""));
  const rank = ["100%", "62%", "34%"];
  const areas = [
    {
      name: "Test",
      href: "/test/simulations/create",
      text: "Find where your agent fails before real customers reach it.",
      glyph: (
        <span className="bj-area-g bj-area-g-run">
          {run.map((c, i) => <i key={i} className={c} />)}
        </span>
      ),
    },
    {
      name: "Monitor",
      href: "/monitor/logs",
      text: "Grade your real conversations and get alerted when they fail.",
      glyph: (
        <span className="bj-area-g bj-area-g-live">
          {live.map((c, i) => <i key={i} className={c} />)}
        </span>
      ),
    },
    {
      name: "Improve",
      href: "/improve/bluejay-ai",
      text: "Find out why conversations fail and what to fix first.",
      glyph: (
        <span className="bj-area-g bj-area-g-rank">
          {rank.map((w, i) => <i key={i} className={i === 0 ? "f" : ""} style={{ "--w": w }} />)}
        </span>
      ),
    },
  ];
  return (
    <nav className="bj-areas not-prose" aria-label="Product areas">
      {areas.map((a) => (
        <a key={a.name} className="bj-area" href={a.href}>
          <span className="bj-area-glyph" aria-hidden="true">{a.glyph}</span>
          <span className="bj-area-name">{a.name}</span>
          <span className="bj-area-text">{a.text}</span>
        </a>
      ))}
    </nav>
  );
};
