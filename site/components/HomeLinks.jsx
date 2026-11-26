const cards = [
  ["Test", "/test/simulations/create", "flask-vial", "Test your agent with realistic customers before you ship a change."],
  ["Monitor", "/monitor/logs", "list", "Find the production conversations where your agent failed, and see why."],
  ["Improve", "/improve/bluejay-ai", null, "Ask Bluejay AI why calls fail and what to fix first."],
  ["Cookbook", "/cookbook/ab-test-agents", "book-open", "Step-by-step recipes for common jobs."],
  ["Developers guide", "/sdk/overview", "code", "SDK, API, MCP server, webhooks, and Bluejay as Code."],
  ["Integrations", "/integrations/phone-number", "plug", "Connect your agent's voice, text, or email platform."],
];

export const HomeLinks = () => {
  return (
    <div className="bj-home-links not-prose">
      <div className="bj-home-links-grid">
        {cards.map(([title, href, icon, text]) => (
          <a key={href} className="bj-home-card" href={href}>
            <span className="bj-home-card-head">
              <span className="bj-card-icon" aria-hidden="true">
                {icon ? <span className="bj-icon" data-icon={icon} /> : <span className="bj-card-icon-flywheel" />}
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
