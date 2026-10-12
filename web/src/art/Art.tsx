import { useId, useMemo, type CSSProperties } from "react";
import { catSvg, grassSvg, pawSvg } from "./svg";

interface ArtProps {
  size?: number | string;
  className?: string;
  style?: CSSProperties;
  label?: string;
}

function Svg({ html, size = "100%", className, style, label }: ArtProps & { html: string }) {
  return (
    <span
      className={`art ${className ?? ""}`}
      style={{ width: size, height: size, ...style }}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
      // 상수 설정으로만 만든 SVG 문자열이다(svg.ts 참고)
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

export function CatArt({ skin, pose = "peek", ...rest }: ArtProps & { skin: number; pose?: "peek" | "face" }) {
  const id = useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const html = useMemo(() => catSvg(skin, pose, `cat${id}`), [skin, pose, id]);
  return <Svg html={html} {...rest} />;
}

export function GrassArt({ index, ...rest }: ArtProps & { index: number }) {
  const html = useMemo(() => grassSvg(index), [index]);
  return <Svg html={html} {...rest} />;
}

export function PawArt({ n, ...rest }: ArtProps & { n: number }) {
  const html = useMemo(() => pawSvg(n), [n]);
  return <Svg html={html} {...rest} />;
}
