export const AreaGlyph = ({ area }) => {
  if (area === "Test") {
    const run = ["p", "p", "f", "p", "p", "p", "f", "p", "p"];
    return (
      <span className="bj-area-g bj-area-g-run">
        {run.map((c, i) => <i key={i} className={c} />)}
      </span>
    );
  }
  if (area === "Monitor") {
    const live = Array.from({ length: 18 }, (_, i) => (i === 13 ? "f" : ""));
    return (
      <span className="bj-area-g bj-area-g-live">
        {live.map((c, i) => <i key={i} className={c} />)}
      </span>
    );
  }
  const rank = ["100%", "62%", "34%"];
  return (
    <span className="bj-area-g bj-area-g-rank">
      {rank.map((w, i) => <i key={i} className={i === 0 ? "f" : ""} style={{ "--w": w }} />)}
    </span>
  );
};

export const HomeGrid = () => {
  const main = [
    {
      name: "Test",
      text: "Find your agent's weak spots.",
      links: [
        ["Simulations", "/test/simulations/create"],
        ["Metrics", "/test/metrics"],
        ["Red Teaming", "/test/red-teaming/overview"],
        ["Issues", "/test/issues"],
        ["Knowledge Bases", "/test/simulations/reference#knowledge-bases"],
      ],
    },
    {
      name: "Monitor",
      text: "Verify your agent runs smoothly in production.",
      links: [
        ["Logs", "/monitor/logs"],
        ["Metrics", "/monitor/metrics"],
        ["Uptime", "/monitor/uptime/overview"],
        ["Issues", "/monitor/issues"],
        ["Alerts", "/monitor/alerts"],
      ],
    },
    {
      name: "Improve",
      text: "Strengthen your agent, automatically.",
      links: [
        ["Bluejay AI", "/improve/bluejay-ai"],
        ["Self-Improve", "/improve/self-improve"],
      ],
    },
  ];
  const more = [
    {
      name: "Cookbook",
      icon: "book-open",
      links: [
        ["A/B Test Two Agents", "/cookbook/ab-test-agents"],
        ["Improve Metric Accuracy", "/cookbook/improve-metric-accuracy"],
        ["After-Hours Uptime", "/cookbook/after-hours-uptime"],
        ["Phone Menus (IVR)", "/cookbook/ivr-phone-menu"],
        ["Red Team Before Launch", "/cookbook/red-team-before-launch"],
        ["Find a Regression", "/cookbook/find-regression-step"],
      ],
    },
    {
      name: "API/MCP",
      icon: "code",
      links: [
        ["Introduction", "/api-reference/introduction"],
        ["Cheat Sheet", "/api-reference/cheat-sheet"],
        ["Webhooks", "/api-reference/webhooks"],
        ["CI/CD Integration", "/api-reference/ci-cd"],
        ["MCP Server", "/mcp/overview"],
      ],
    },
    {
      name: "Bluejay as Code",
      icon: "file-code",
      links: [
        ["Overview", "/bluejay-as-code/overview"],
        ["Claude Code skill", "/bluejay-as-code/overview#claude-code-skill"],
        ["Cookbook", "/bluejay-as-code/cookbook"],
      ],
    },
  ];
  const chev = (
    <svg className="bj-home-chev" viewBox="0 0 16 16" aria-hidden="true">
      <path d="M6 3.5 10.5 8 6 12.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
  const rows = (links) => (
    <ul className="bj-home-rows">
      {links.map(([label, href]) => (
        <li key={href}>
          <a className="bj-home-row" href={href}>
            <span>{label}</span>
            {chev}
          </a>
        </li>
      ))}
    </ul>
  );
  return (
    <div className="bj-home-grid not-prose">
      <div className="bj-home-tier">
        {main.map((g) => (
          <section key={g.name} className="bj-home-card">
            <span className="bj-area-glyph bj-home-glyph" aria-hidden="true">{AreaGlyph({ area: g.name })}</span>
            <h3 className="bj-home-title">{g.name}</h3>
            <p className="bj-home-text">{g.text}</p>
            {rows(g.links)}
          </section>
        ))}
      </div>
      <div className="bj-home-tier">
        {more.map((g) => (
          <section key={g.name} className="bj-home-card bj-home-card-quiet">
            <span className="bj-home-icon" aria-hidden="true"><Icon icon={g.icon} size={16} /></span>
            <h3 className="bj-home-title">{g.name}</h3>
            {rows(g.links)}
          </section>
        ))}
      </div>
    </div>
  );
};
