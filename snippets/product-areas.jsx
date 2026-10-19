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

export const HomeAreas = () => {
  const areas = [
    {
      name: "Test",
      text: "Find your agent's weak spots.",
      pages: [
        ["Simulations", "/test/simulations/create", "flask-vial"],
        ["Metrics", "/test/metrics", "gauge-high"],
        ["Red Teaming", "/test/red-teaming/overview", "shield-halved"],
      ],
    },
    {
      name: "Monitor",
      text: "Verify your agent runs smoothly in production.",
      pages: [
        ["Logs", "/monitor/logs", "list"],
        ["Uptime", "/monitor/uptime/overview", "heart-pulse"],
        ["Issues", "/monitor/issues", "triangle-exclamation"],
      ],
    },
    {
      name: "Improve",
      text: "Strengthen your agent, automatically.",
      pages: [
        ["Bluejay AI", "/improve/bluejay-ai", null],
        ["Self-Improve", "/improve/self-improve", "wand-magic-sparkles"],
      ],
    },
  ];
  return (
    <div className="bj-areas not-prose">
      {areas.map((a) => (
        <section key={a.name} className="bj-area" aria-label={a.name}>
          <span className="bj-area-glyph" aria-hidden="true">{AreaGlyph({ area: a.name })}</span>
          <span className="bj-area-name">{a.name}</span>
          <span className="bj-area-text">{a.text}</span>
          <div className="bj-area-links">
            {a.pages.map(([title, href, icon]) => (
              <a key={href} className="bj-area-link" href={href}>
                <span className="bj-card-icon" aria-hidden="true">
                  {icon ? <Icon icon={icon} size={14} /> : <span className="bj-card-icon-flywheel" />}
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

export const HomeMore = () => {
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
  return (
    <div className="bj-home-more not-prose">
      {more.map((g) => (
        <section key={g.name} className="bj-home-card">
          <span className="bj-card-icon" aria-hidden="true"><Icon icon={g.icon} size={16} /></span>
          <h3 className="bj-card-title">{g.name}</h3>
          <ul className="bj-home-rows">
            {g.links.map(([label, href]) => (
              <li key={href}>
                <a className="bj-home-row" href={href}>
                  <span>{label}</span>
                  <svg className="bj-home-chev" viewBox="0 0 16 16" aria-hidden="true">
                    <path d="M6 3.5 10.5 8 6 12.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </a>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
};
