// A tag used in changelog.mdx but missing here gets no filter button.
export const ChangelogFilters = () => {
  const tags = ["New", "Improvement", "Integration", "Simulations", "API", "Observability", "Metrics", "Platform", "Digital Humans", "Docs", "Dashboard", "Alerts", "Workflows"];
  const [picked, setPicked] = useState([]);

  useEffect(() => {
    document.querySelectorAll(".update-container").forEach((entry) => {
      const own = [...entry.querySelectorAll('[data-component-part="update-tag"]')].map((t) => t.textContent.trim());
      entry.style.display = picked.length === 0 || own.some((t) => picked.includes(t)) ? "" : "none";
    });
  }, [picked]);

  const toggle = (tag) => setPicked((p) => (p.includes(tag) ? p.filter((t) => t !== tag) : [...p, tag]));

  return (
    <div className="bj-cl-filters not-prose" role="group" aria-label="Filter by tag">
      {tags.map((tag) => (
        <button key={tag} type="button" className="bj-cl-filter" aria-pressed={picked.includes(tag)} onClick={() => toggle(tag)}>
          {tag}
        </button>
      ))}
    </div>
  );
};
