import { useState } from "react";

export const render = "hydrate";

export const FieldTable = ({ rows = [] }) => {
  const [open, setOpen] = useState({});
  const toggle = (key) => setOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  const breakable = (text, at = /(?<=[_/])|(?<=[A-Za-z])(?=\.[A-Za-z])/) =>
    String(text)
      .split(at)
      .flatMap((part, i) => (i > 0 ? [<span className="bj-break" key={i} />, part] : [part]));

  const renderDescription = (text) => {
    const parts = [];
    const re = /\[([^\]]+)\]\(([^)]+)\)/g;
    let last = 0;
    let match;
    let i = 0;
    const source = String(text);
    while ((match = re.exec(source))) {
      if (match.index > last) {
        parts.push(<span key={i++}>{breakable(source.slice(last, match.index), /(?<=[_/])/)}</span>);
      }
      parts.push(
        <a key={i++} href={match[2]}>
          {match[1]}
        </a>
      );
      last = match.index + match[0].length;
    }
    if (last < source.length) {
      parts.push(<span key={i++}>{breakable(source.slice(last), /(?<=[_/])/)}</span>);
    }
    return parts;
  };

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
              <code>{breakable(row.name)}</code>
            </span>
          </td>
          <td>
            <code>{row.type}</code>
          </td>
          <td>{row.required ? "Required" : "Optional"}</td>
          <td>
            {row.description ? <div>{renderDescription(row.description)}</div> : null}
            {row.default !== undefined ? (
              <div className="bj-field-meta">
                Default: <code>{breakable(row.default)}</code>
              </div>
            ) : null}
            {row.values && row.values.length ? (
              <div className="bj-field-meta">
                Allowed values:
                {row.values.map((v) => (
                  <div key={v}>
                    <code>{breakable(v)}</code>
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

export function toMarkdown({ rows }) {
  const lines = [];
  function visit(row, parent) {
    const name = parent ? parent + "." + row.name : row.name;
    const parts = [name, row.type, row.required ? "Required" : "Optional"];
    if (row.description) parts.push(row.description);
    if (row.default !== undefined) parts.push("Default: " + JSON.stringify(row.default));
    if (row.values?.length) parts.push("Allowed values: " + row.values.map(value => JSON.stringify(value)).join(", "));
    lines.push("- " + parts.join(" · "));
    for (const child of row.children ?? []) visit(child, name);
  }
  for (const row of rows) visit(row, "");
  return lines.join("\n");
}
