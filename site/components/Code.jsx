export const Code = ({ children, value }) => {
  const parts = (children ?? value).split(/(?<=[_/])|(?<=[A-Za-z])(?=\.[A-Za-z])/);
  return <code>{parts.flatMap((part, i) => (i > 0 ? [<span className="bj-break" key={`w${i}`} />, part] : [part]))}</code>;
};
