export const FieldTable = ({ rows = [] }) => {
  const [open, setOpen] = useState({});
  const toggle = (key) => setOpen((prev) => ({ ...prev, [key]: !prev[key] }));

  const renderRows = (items, depth, prefix) =>
    items.flatMap((row, i) => {
      const key = `${prefix}${i}`;
      const hasChildren = Array.isArray(row.children) && row.children.length > 0;
      const isOpen = !!open[key];
      const onKey = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          toggle(key);
        }
      };
      const out = [
        <tr
          key={key}
          className={hasChildren ? "bj-field-row bj-field-row-toggle" : "bj-field-row"}
          onClick={hasChildren ? () => toggle(key) : undefined}
          onKeyDown={hasChildren ? onKey : undefined}
          tabIndex={hasChildren ? 0 : undefined}
          aria-expanded={hasChildren ? isOpen : undefined}
        >
          <td>
            <span className="bj-field-name" style={{ paddingLeft: `${depth * 1.25}rem` }}>
              {hasChildren ? (
                <span className={isOpen ? "bj-field-chevron bj-field-chevron-open" : "bj-field-chevron"} aria-hidden="true">
                  ›
                </span>
              ) : (
                <span className="bj-field-chevron-space" aria-hidden="true" />
              )}
              <code>{row.name}</code>
            </span>
          </td>
          <td>
            <code>{row.type}</code>
          </td>
          <td>{row.required ? "Required" : "Optional"}</td>
          <td>
            {row.description ? <div>{row.description}</div> : null}
            {row.default !== undefined ? (
              <div className="bj-field-meta">
                Default: <code>{String(row.default)}</code>
              </div>
            ) : null}
            {row.values && row.values.length ? (
              <div className="bj-field-meta">
                Allowed values:
                {row.values.map((v) => (
                  <div key={v}>
                    <code>{v}</code>
                  </div>
                ))}
              </div>
            ) : null}
          </td>
        </tr>,
      ];
      if (hasChildren && isOpen) out.push(...renderRows(row.children, depth + 1, `${key}.`));
      return out;
    });

  return (
    <div data-table-wrapper="true" className="bj-field-table">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Required</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>{renderRows(rows, 0, "")}</tbody>
      </table>
    </div>
  );
};
