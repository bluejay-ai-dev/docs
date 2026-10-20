export const Related = ({ links }) => {
  const glyph = (icon, size) =>
    icon.includes("bluejay-flywheel") ? (
      <span className="bj-card-icon-flywheel" style={{ width: size, height: size }} />
    ) : icon.startsWith("/") ? (
      <img src={icon} alt="" width={size} height={size} className="bj-related-img" />
    ) : (
      <Icon icon={icon} size={size} />
    );
  const kind = (href) =>
    href.startsWith("/api-reference/") ? "code" : href.startsWith("/mcp/") ? "plug-circle-bolt" : null;
  return (
    <CardGroup cols={2}>
      {links.map(([title, href, icon, text]) => {
        const main = kind(href);
        return (
          <Card
            key={href}
            title={title}
            href={href}
            icon={
              <span className="bj-related-icon">
                {glyph(main || icon, 20)}
                {main && icon !== main ? (
                  <span className="bj-related-sub">
                    {glyph(icon, 14)}
                  </span>
                ) : null}
              </span>
            }
          >
            {text}
          </Card>
        );
      })}
    </CardGroup>
  );
};
