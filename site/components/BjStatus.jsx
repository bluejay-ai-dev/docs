export const BjStatus = ({ status, icon, children }) => (
  <span className={`bj-status bj-status-${status}`}>
    <span className="bj-icon" data-icon={icon} aria-hidden="true" />
    {children}
  </span>
);

export const toMarkdown = ({ children }) => children;
