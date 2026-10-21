export const DownloadFile = ({ href, filename, children }) => {
  // The download attribute is ignored for another origin, so fetch the file and save it as a blob.
  const save = async (event) => {
    event.preventDefault();
    try {
      const response = await fetch(href);
      if (!response.ok) throw new Error(String(response.status));
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch {
      window.open(href, "_blank", "noopener");
    }
  };
  return (
    <a className="bj-download not-prose" href={href} download={filename} onClick={save}>
      <svg className="bj-download-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3v12m0 0-5-5m5 5 5-5M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
      </svg>
      <span className="bj-download-label">{children}</span>
      <code className="bj-download-file">{filename}</code>
    </a>
  );
};
