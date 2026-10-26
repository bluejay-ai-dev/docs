export const TryIt = ({ operations = [] }) => {
  const BASE = "https://api.getbluejay.ai";
  const [index, setIndex] = useState(0);
  const [apiKey, setApiKey] = useState("");
  const [values, setValues] = useState({});
  const [body, setBody] = useState(operations[0]?.body || "");
  const [result, setResult] = useState(null);
  const [sending, setSending] = useState(false);
  const [copied, setCopied] = useState(false);

  const op = operations[index] || { params: [] };
  const groups = [];
  operations.forEach((o, i) => {
    const last = groups[groups.length - 1];
    if (!last || last.label !== o.group) groups.push({ label: o.group, items: [] });
    groups[groups.length - 1].items.push({ o, i });
  });

  const choose = (i) => {
    setIndex(i);
    setValues({});
    setBody(operations[i]?.body || "");
    setResult(null);
  };

  const url = (() => {
    let path = op.path || "";
    const query = [];
    op.params.forEach((p) => {
      const v = values[p.name];
      if (p.in === "path") path = path.replace(`{${p.name}}`, v ? encodeURIComponent(v) : `{${p.name}}`);
      else if (v) query.push(`${encodeURIComponent(p.name)}=${encodeURIComponent(v)}`);
    });
    return BASE + path + (query.length ? `?${query.join("&")}` : "");
  })();

  const hasJsonBody = op.bodyType === "application/json";
  const curl = [
    `curl --request ${op.method} \\`,
    `  --url '${url}' \\`,
    `  --header 'X-API-Key: ${apiKey ? "<your key>" : "<api-key>"}'${hasJsonBody ? " \\" : ""}`,
    ...(hasJsonBody
      ? ["  --header 'Content-Type: application/json' \\", `  --data '${body.replace(/'/g, "'\\''")}'`]
      : []),
  ].join("\n");

  const copy = () => {
    const text = apiKey ? curl.replace("<your key>", apiKey) : curl;
    navigator.clipboard?.writeText(text).then(
      () => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      },
      (err) => console.warn("try-it: copy failed", err),
    );
  };

  const missing = op.params.filter((p) => p.required && !values[p.name]).map((p) => p.name);

  const send = async () => {
    if (!apiKey || missing.length) return;
    let parsed;
    if (hasJsonBody) {
      try {
        parsed = JSON.stringify(JSON.parse(body));
      } catch (e) {
        setResult({ error: `The request body is not valid JSON: ${e.message}` });
        return;
      }
    }
    setSending(true);
    setResult(null);
    const started = performance.now();
    try {
      const res = await fetch(url, {
        method: op.method,
        headers: { "X-API-Key": apiKey, ...(hasJsonBody ? { "Content-Type": "application/json" } : {}) },
        body: hasJsonBody ? parsed : undefined,
      });
      const text = await res.text();
      let pretty = text;
      try {
        pretty = JSON.stringify(JSON.parse(text), null, 2);
      } catch (e) {
        pretty = text;
      }
      setResult({ status: res.status, ms: Math.round(performance.now() - started), body: pretty });
    } catch (e) {
      console.warn("try-it: request failed", e);
      setResult({
        error:
          "The browser could not send this request. The API may not accept requests from this page yet. Copy the curl command and run it in a terminal.",
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bj-tryit not-prose">
      <label className="bj-tryit-field">
        <span>Endpoint</span>
        <select value={index} onChange={(e) => choose(Number(e.target.value))}>
          {groups.map((g, gi) => (
            <optgroup key={`${g.label}-${gi}`} label={g.label}>
              {g.items.map(({ o, i }) => (
                <option key={o.slug} value={i}>
                  {o.method} {o.path}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>
      {op.summary ? (
        <p className="bj-tryit-summary">
          {op.summary}. <a href={`/${op.slug}`}>Open the endpoint page</a>
        </p>
      ) : null}

      <label className="bj-tryit-field">
        <span>API key</span>
        <input
          type="password"
          autoComplete="off"
          placeholder="Paste your API key"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
        />
      </label>

      {op.params.map((p) => (
        <label key={`${p.in}-${p.name}`} className="bj-tryit-field">
          <span>
            {p.name}
            <em>{p.in === "path" ? "path" : "query"}{p.required ? ", required" : ""}</em>
          </span>
          <input value={values[p.name] || ""} onChange={(e) => setValues({ ...values, [p.name]: e.target.value })} />
        </label>
      ))}

      {hasJsonBody ? (
        <label className="bj-tryit-field">
          <span>Request body</span>
          <textarea rows={Math.min(16, Math.max(4, body.split("\n").length))} value={body} onChange={(e) => setBody(e.target.value)} spellCheck={false} />
        </label>
      ) : op.bodyType ? (
        <p className="bj-tryit-summary">This endpoint takes a file upload. Use the curl command from its endpoint page.</p>
      ) : null}

      <div className="bj-tryit-actions">
        <button type="button" onClick={send} disabled={!apiKey || missing.length > 0 || sending || (op.bodyType && !hasJsonBody)}>
          {sending ? "Sending..." : "Send request"}
        </button>
        <button type="button" className="bj-tryit-secondary" onClick={copy}>
          {copied ? "Copied" : "Copy curl"}
        </button>
        {!apiKey ? <span className="bj-tryit-hint">Enter your API key to send the request.</span> : null}
        {apiKey && missing.length ? <span className="bj-tryit-hint">Fill in {missing.join(", ")}.</span> : null}
      </div>

      <pre className="bj-tryit-code">{curl}</pre>

      {result ? (
        result.error ? (
          <p className="bj-tryit-error">{result.error}</p>
        ) : (
          <div>
            <p className="bj-tryit-summary">
              Status <code>{result.status}</code>, {result.ms} ms
            </p>
            <pre className="bj-tryit-code">{result.body}</pre>
          </div>
        )
      ) : null}
    </div>
  );
};
