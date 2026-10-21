export const HomeAreas = () => {
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
        ["Uptime", "/monitor/uptime/overview", "heart-pulse"],
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

export const HomeLinks = () => {
  const cards = [
    ["Test", "/test/simulations/create", "flask-vial", "Test your agent with realistic customers before you ship a change."],
    ["Monitor", "/monitor/logs", "list", "Find the production conversations where your agent failed, and see why."],
    ["Improve", "/improve/bluejay-ai", null, "Ask Bluejay AI why calls fail and what to fix first."],
    ["Cookbook", "/cookbook/ab-test-agents", "book-open", "Step-by-step recipes for common jobs."],
    ["Developers guide", "/api-reference/introduction", "code", "API, MCP server, webhooks, and Bluejay as Code."],
    ["Integrations", "/integrations/phone-number", "plug", "Connect your agent's voice, text, or email platform."],
  ];
  return (
    <div className="bj-home-links not-prose">
      <div className="bj-home-links-grid">
        {cards.map(([title, href, icon, text]) => (
          <a key={href} className="bj-home-card" href={href}>
            <span className="bj-home-card-head">
              <span className="bj-card-icon" aria-hidden="true">
                {icon ? <Icon icon={icon} size={16} /> : <span className="bj-card-icon-flywheel" />}
              </span>
              <span className="bj-card-title">{title}</span>
            </span>
            <span className="bj-home-card-text">{text}</span>
          </a>
        ))}
      </div>
    </div>
  );
};
