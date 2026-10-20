export const Related = ({ links }) => (
  <div className="bj-related not-prose">
    {links.map(([title, href, icon, text]) => (
      <a key={href} className="bj-home-card" href={href}>
        <span className="bj-home-card-head">
          <span className="bj-card-icon" aria-hidden="true">
            <Icon icon={icon} size={16} />
          </span>
          <span className="bj-card-title">{title}</span>
        </span>
        {text ? <span className="bj-home-card-text">{text}</span> : null}
      </a>
    ))}
  </div>
);
