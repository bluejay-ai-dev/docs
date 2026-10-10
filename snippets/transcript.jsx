export const Transcript = ({ turns = [], verdict }) => {
  const label = { agent: "Agent", human: "Digital Human" };
  return (
    <figure className="bj-transcript not-prose" aria-label="Call transcript">
      <div className="bj-transcript-head">
        <span className="bj-transcript-dot" aria-hidden="true" />
        <span>Transcript</span>
        <span className="bj-transcript-count">{turns.length} turns</span>
      </div>
      <ol className="bj-transcript-turns">
        {turns.map((turn, i) => (
          <li key={i} className={`bj-turn bj-turn-${turn.role === "agent" ? "agent" : "human"}`}>
            <div className="bj-turn-meta">
              <span className="bj-turn-role">{label[turn.role] || turn.role}</span>
              {turn.t ? <time className="bj-turn-time">{turn.t}</time> : null}
            </div>
            <p className="bj-turn-text">{turn.text}</p>
          </li>
        ))}
      </ol>
      {verdict ? (
        <figcaption className={`bj-verdict ${verdict.pass ? "bj-verdict-pass" : "bj-verdict-fail"}`}>
          <span className="bj-verdict-chip">{verdict.pass ? "Pass" : "Fail"}</span>
          <span className="bj-verdict-metric">{verdict.metric}</span>
          {verdict.reason ? <span className="bj-verdict-reason">{verdict.reason}</span> : null}
        </figcaption>
      ) : null}
    </figure>
  );
};
