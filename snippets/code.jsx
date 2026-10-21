// Breaks only after "_" or "/" and before ".". <wbr> adds no character, so a copied value stays plain.
export const Code = ({ children }) => {
  if (typeof children !== "string") return <code>{children}</code>;
  const parts = children.split(/(?<=[_/])|(?<=[A-Za-z])(?=\.[A-Za-z])/);
  return <code>{parts.flatMap((part, i) => (i > 0 ? [<wbr key={`w${i}`} />, part] : [part]))}</code>;
};
