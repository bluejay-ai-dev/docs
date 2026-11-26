const areas = [
  {
    name: "Test",
    href: "/test/simulations/create",
    text: "Find your agent's weak spots.",
    pages: [
      ["Simulations", "/test/simulations/create", "flask-vial"],
      ["Digital Humans", "/test/simulations/digital-humans", "users"],
      ["Red Teaming", "/test/red-teaming/overview", "shield-halved"],
    ],
  },
  {
    name: "Monitor",
    href: "/monitor/logs",
    text: "Verify your agent runs smoothly in production.",
    pages: [
      ["Logs", "/monitor/logs", "list"],
      ["Uptime", "/monitor/uptime/overview", "wave-pulse"],
      ["Issues", "/monitor/issues", "triangle-exclamation"],
      ["Alerts", "/monitor/alerts", "bell"],
    ],
  },
  {
    name: "Improve",
    href: "/improve/bluejay-ai",
    text: "Strengthen your agent, automatically.",
    pages: [
      ["Bluejay AI", "/improve/bluejay-ai", null],
      ["Self-Improve", "/improve/self-improve", "wand-magic-sparkles"],
    ],
  },
];

export const HomeAreas = () => {
  return (
    <div className="bj-areas not-prose">
      {areas.map((a) => (
        <section key={a.name} className="bj-area" aria-label={a.name}>
          <a className="bj-area-name" href={a.href}>{a.name}</a>
          <span className="bj-area-text">{a.text}</span>
          <div className="bj-area-links">
            {a.pages.map(([title, href, icon]) => (
              <a key={href} className="bj-area-link" href={href}>
                <span className="bj-card-icon" aria-hidden="true">
                  {icon ? <span className="bj-icon" data-icon={icon} /> : <span className="bj-card-icon-flywheel" />}
                </span>
                <span>{title}</span>
              </a>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
};
