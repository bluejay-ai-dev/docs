export const MetricExamples = () => {
  const verdict = (pass) => (
    <span className={`bj-mx-chip ${pass ? "is-pass" : "is-fail"}`}>
      <i aria-hidden="true" />
      {pass ? "Pass" : "Fail"}
    </span>
  );
  const choice = (options, picked) => (
    <span className="bj-mx-seg">
      <span className="bj-mx-sr">{picked}</span>
      {options.map((o) => (
        <span key={o} className={o === picked ? "on" : ""} aria-hidden="true">
          {o}
        </span>
      ))}
    </span>
  );
  const scale = (value, max) => (
    <span className="bj-mx-meter">
      <span className="bj-mx-pips" aria-hidden="true">
        {Array.from({ length: max }, (_, i) => (
          <i key={i} className={i < value ? "on" : ""} />
        ))}
      </span>
      <span className="bj-mx-score">
        {value}
        <span aria-hidden="true"> / {max}</span>
        <span className="bj-mx-sr"> out of {max}</span>
      </span>
    </span>
  );
  const rows = [
    { name: "Identity Verified Before Disclosure", type: "Pass/Fail", result: verdict(true) },
    { name: "Booking Tool Called", type: "Tool Call", result: verdict(false) },
    { name: "Customer Asked for a Human", type: "Yes/No", result: choice(["Yes", "No"], "No") },
    { name: "Explanation Clarity", type: "Number", result: scale(4, 5) },
    {
      name: "Call Outcome",
      type: "Categorical",
      result: choice(["resolved", "escalated", "unresolved"], "escalated"),
    },
  ];
  return (
    <ul className="bj-mx not-prose" aria-label="Example metric results">
      {rows.map((r) => (
        <li key={r.name} className="bj-mx-row">
          <span className="bj-mx-name">{r.name}</span>
          <span className="bj-mx-type">{r.type}</span>
          <span className="bj-mx-result">{r.result}</span>
        </li>
      ))}
    </ul>
  );
};
