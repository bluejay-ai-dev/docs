import { useEffect, useRef, useState } from "react";

export const render = "hydrate";

export function toMarkdown({ tags }) {
  return "Filter by tag: " + tags.join(", ");
}

export function ChangelogFilters({ tags }) {
  const group = useRef(null);
  const [picked, setPicked] = useState([]);

  useEffect(() => {
    const entries = group.current.closest(".gs-content").querySelectorAll(":scope > .gs-columns");
    for (const entry of entries) {
      const pills = entry.querySelectorAll(":scope > .gs-columns > p > em");
      entry.hidden = picked.length > 0 && !Array.from(pills).some(pill => picked.includes(pill.textContent));
    }
    return () => {
      for (const entry of entries) entry.hidden = false;
    };
  }, [picked]);

  function toggle(tag) {
    setPicked(current => current.includes(tag) ? current.filter(item => item !== tag) : [...current, tag]);
  }

  return (
    <div ref={group} className="bj-cl-filters" role="group" aria-label="Filter by tag">
      {tags.map(tag => (
        <button key={tag} type="button" className="bj-cl-filter" aria-pressed={picked.includes(tag)} onClick={() => toggle(tag)}>
          {tag}
        </button>
      ))}
    </div>
  );
}
