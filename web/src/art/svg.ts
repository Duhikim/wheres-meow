// 고양이·들풀·발자국 SVG 를 문자열로 만든다. 시안의 그리기 코드를 그대로 옮겼다.
// 입력은 스킨 ID·칸 번호·숫자뿐이고 사용자 문자열이 섞이지 않으므로 innerHTML 로 넣어도 안전하다.

import { skinConfig, type Coat, type SkinConfig } from "./skins";

const OUT = "#3a2c25";

interface CoatStyle {
  base: string;
  mark?: string;
  inner: string;
  pattern: "stripes" | "none" | "patches" | "mask" | "muzzle";
  iris?: string;
  dark?: boolean;
}

const COATS: Record<Coat, CoatStyle> = {
  orange: { base: "#f6a45a", mark: "#e07b2a", inner: "#ffc2b8", pattern: "stripes" },
  cheese: { base: "#ffd585", mark: "#f2ac45", inner: "#ffc2b8", pattern: "stripes" },
  gray: { base: "#aab5c3", mark: "#7d8a9c", inner: "#f7b6c2", pattern: "stripes" },
  brown: { base: "#c09068", mark: "#7a5537", inner: "#f2b8a8", pattern: "stripes" },
  black: { base: "#36323c", inner: "#7a6478", pattern: "none", iris: "#f9d64a", dark: true },
  white: { base: "#fffdf8", inner: "#ffc7d1", pattern: "none" },
  calico: { base: "#fffdf8", inner: "#ffc7d1", pattern: "patches" },
  siamese: { base: "#f3e6cf", mark: "#5e4838", inner: "#c9a28a", pattern: "mask", iris: "#6fb7ff" },
  tuxedo: { base: "#2f2c33", inner: "#7a6478", pattern: "muzzle", iris: "#9ee26b", dark: true },
  russian: { base: "#8e9db3", inner: "#c9a8b8", pattern: "none", iris: "#7fd38a" },
};

function ears(cfg: SkinConfig, c: CoatStyle, outline: boolean): string {
  const st = outline ? ` stroke="${OUT}" stroke-width="3" stroke-linejoin="round"` : "";
  const earFill = c.pattern === "mask" ? c.mark : c.base;
  let left: string;
  let inner: string | null;
  if (cfg.ears === "round") {
    left = "M20 46 Q16 16 34 20 Q44 24 47 36 Z";
    inner = "M26 40 Q25 25 34 27 Q40 30 41 36 Z";
  } else if (cfg.ears === "fold") {
    left = "M22 40 Q24 26 38 27 Q42 33 38 39 Z";
    inner = null;
  } else {
    left = "M21 46 L25 14 Q27 9 32 12 L47 33 Z";
    inner = "M27 39 L29 21 L40 33 Z";
  }
  const one = `<path d="${left}" fill="${earFill}"${st}/>` + (inner ? `<path d="${inner}" fill="${c.inner}"/>` : "");
  return one + `<g transform="translate(100,0) scale(-1,1)">${one}</g>`;
}

function eye(kind: SkinConfig["eyes"], cx: number, cy: number, c: CoatStyle): string {
  const ink = c.dark ? "#f4e9dc" : "#2b211c";
  const line = (d: string) => `<path d="${d}" fill="none" stroke="${ink}" stroke-width="3.2" stroke-linecap="round"/>`;
  if (kind === "happy") return line(`M${cx - 6} ${cy + 2} Q${cx} ${cy - 6} ${cx + 6} ${cy + 2}`);
  if (kind === "sleepy") return line(`M${cx - 6} ${cy} Q${cx} ${cy + 5} ${cx + 6} ${cy}`);
  if (kind === "slit") {
    return (
      `<ellipse cx="${cx}" cy="${cy}" rx="6.5" ry="7.2" fill="${c.iris ?? "#c6e86b"}" stroke="#2b211c" stroke-width="1.2"/>` +
      `<ellipse cx="${cx}" cy="${cy}" rx="1.7" ry="5.6" fill="#1b1512"/>` +
      `<circle cx="${cx + 2.2}" cy="${cy - 3}" r="1.5" fill="#fff"/>`
    );
  }
  if (kind === "big" || kind === "sparkle") {
    let s =
      `<ellipse cx="${cx}" cy="${cy}" rx="7.5" ry="8.6" fill="#2b211c"/>` +
      (c.iris ? `<ellipse cx="${cx}" cy="${cy + 2}" rx="5" ry="4.5" fill="${c.iris}" opacity=".55"/>` : "") +
      `<circle cx="${cx + 2.4}" cy="${cy - 3.2}" r="3" fill="#fff"/>` +
      `<circle cx="${cx - 2.6}" cy="${cy + 3.2}" r="1.4" fill="#fff"/>`;
    if (kind === "sparkle") {
      s += `<path d="M${cx + 9} ${cy - 12} l1.2 3 3 1.2 -3 1.2 -1.2 3 -1.2 -3 -3 -1.2 3 -1.2z" fill="#fff3a6" stroke="#e8b800" stroke-width=".6"/>`;
    }
    return s;
  }
  if (kind === "wink") return eye("big", cx, cy, c);
  // dot
  if (c.iris) {
    return (
      `<circle cx="${cx}" cy="${cy}" r="6" fill="${c.iris}" stroke="#1b1512" stroke-width="1"/>` +
      `<ellipse cx="${cx}" cy="${cy}" rx="2.2" ry="4.6" fill="#1b1512"/>` +
      `<circle cx="${cx + 1.8}" cy="${cy - 2.4}" r="1.6" fill="#fff"/>`
    );
  }
  return `<circle cx="${cx}" cy="${cy}" r="5.4" fill="#2b211c"/><circle cx="${cx + 1.8}" cy="${cy - 2}" r="1.8" fill="#fff"/>`;
}

function face(cfg: SkinConfig, c: CoatStyle, idPrefix: string): string {
  const outline = cfg.outline !== false;
  const clipId = `${idPrefix}-head`;
  let s = ears(cfg, c, outline);
  s += `<clipPath id="${clipId}"><ellipse cx="50" cy="58" rx="34" ry="28"/></clipPath>`;
  s += `<ellipse cx="50" cy="58" rx="34" ry="28" fill="${c.base}"/>`;
  s += `<g clip-path="url(#${clipId})">`;
  if (c.pattern === "stripes") {
    s += `<path d="M43 31 L45.5 40 M50 30 L50 40 M57 31 L54.5 40 M16 55 L25 56.5 M16 61 L25 60.5 M84 55 L75 56.5 M84 61 L75 60.5" stroke="${c.mark}" stroke-width="3.4" stroke-linecap="round"/>`;
  } else if (c.pattern === "patches") {
    s += `<ellipse cx="28" cy="40" rx="20" ry="17" fill="#f19a4b"/><ellipse cx="74" cy="42" rx="17" ry="15" fill="#3a3434"/>`;
  } else if (c.pattern === "mask") {
    s += `<ellipse cx="50" cy="65" rx="19" ry="15" fill="${c.mark}" opacity=".85"/>`;
  } else if (c.pattern === "muzzle") {
    s += `<path d="M50 44 Q38 58 34 70 Q42 84 50 84 Q58 84 66 70 Q62 58 50 44 Z" fill="#fff"/>`;
  }
  s += "</g>";
  if (outline) s += `<ellipse cx="50" cy="58" rx="34" ry="28" fill="none" stroke="${OUT}" stroke-width="3"/>`;
  if (cfg.blush) {
    s += `<ellipse cx="27" cy="67" rx="6" ry="3.5" fill="#ff8fa3" opacity=".5"/><ellipse cx="73" cy="67" rx="6" ry="3.5" fill="#ff8fa3" opacity=".5"/>`;
  }
  s += cfg.eyes === "wink" ? eye("big", 37, 58, c) + eye("happy", 63, 58, c) : eye(cfg.eyes, 37, 58, c) + eye(cfg.eyes, 63, 58, c);
  const mouthInk = c.dark && c.pattern !== "muzzle" ? "#f4e9dc" : "#2b211c";
  s += `<path d="M46.5 63.5 Q50 61.5 53.5 63.5 Q50 67.5 46.5 63.5 Z" fill="#ff8fa3"/>`;
  const ms = ` fill="none" stroke="${mouthInk}" stroke-width="2.2" stroke-linecap="round"`;
  if (cfg.mouth === "flat") s += `<path d="M46 69 L54 69"${ms}/>`;
  else if (cfg.mouth === "o") s += `<ellipse cx="50" cy="70" rx="2.6" ry="3.2" fill="${mouthInk}"/>`;
  else {
    if (cfg.mouth === "open") s += `<path d="M46.5 68.5 Q50 77 53.5 68.5 Z" fill="#ff7b93"/>`;
    s += `<path d="M43 66.5 Q46.5 71.5 50 67 Q53.5 71.5 57 66.5"${ms}/>`;
  }
  if (cfg.whiskers) {
    s += `<path d="M17 62 L4 59 M17 66 L4 68 M83 62 L96 59 M83 66 L96 68" stroke="${c.dark ? "#d9cfc6" : OUT}" stroke-width="1.4" opacity=".7" stroke-linecap="round"/>`;
  }
  return s;
}

/** 시안과 같은 의사 난수. 같은 시드면 항상 같은 수열을 낸다. */
function rng(seed: number): () => number {
  let r = seed;
  return () => {
    r = (r * 9301 + 49297) % 233280;
    return r / 233280;
  };
}

function grassFront(seed: number): string {
  const rnd = rng(seed);
  let s = "";
  for (let x = -4; x < 104; x += 7) {
    const tip = 66 + rnd() * 12;
    const lean = (rnd() - 0.5) * 10;
    const col = rnd() > 0.5 ? "#5fa233" : "#86c94f";
    s += `<path d="M${x} 101 Q${x + 3 + lean / 2} ${tip + 14} ${x + 4 + lean} ${tip} Q${x + 6 + lean / 2} ${tip + 14} ${x + 9} 101 Z" fill="${col}" stroke="#3f7a1f" stroke-width="1"/>`;
  }
  return s;
}

/**
 * 고양이 SVG. peek = 풀숲에서 빼꼼(판·설정 화면), face = 얼굴만(점수판·결과).
 * idPrefix 는 clipPath ID 가 화면 안에서 겹치지 않게 하는 고유 문자열이다.
 */
export function catSvg(skin: number, pose: "peek" | "face", idPrefix: string): string {
  const cfg = skinConfig(skin);
  const c = COATS[cfg.coat];
  const body = pose === "peek" ? `<g transform="translate(0,16)">${face(cfg, c, idPrefix)}</g>${grassFront(skin * 37)}` : face(cfg, c, idPrefix);
  return `<svg viewBox="0 0 100 100">${body}</svg>`;
}

/** 닫힌 칸의 키 큰 들풀. 칸 번호를 시드로 써서 모든 화면에서 같은 모양이 나온다. */
export function grassSvg(cellIndex: number): string {
  const rnd = rng(cellIndex * 13 + 3 + 11);
  let s = '<svg viewBox="0 0 40 40"><rect width="40" height="40" fill="#5c9a35"/><rect y="26" width="40" height="14" fill="#4a8228"/>';
  for (let x = 0; x < 40; x += 3.4) {
    const tip = 4 + rnd() * 14;
    const lean = (rnd() - 0.5) * 8;
    s += `<path d="M${x} 40 Q${x + lean / 2} ${tip + 14} ${x + lean} ${tip}" stroke="${rnd() > 0.5 ? "#8fd05a" : "#6db23c"}" stroke-width="2.2" fill="none" stroke-linecap="round"/>`;
  }
  if (rnd() > 0.6) {
    const fx = 8 + rnd() * 24;
    const fy = 8 + rnd() * 10;
    const fc = rnd() > 0.5 ? "#fff" : "#ffe066";
    s += `<circle cx="${fx}" cy="${fy}" r="2.6" fill="${fc}"/><circle cx="${fx}" cy="${fy}" r="1" fill="#f59f00"/>`;
  }
  return s + "</svg>";
}

/** 열린 숫자 칸: 흙바닥 위 고양이 발자국에 주변 고양이 수를 쓴다. */
export function pawSvg(n: number): string {
  if (!Number.isInteger(n) || n < 1 || n > 8) throw new Error(`발자국 숫자는 1~8 이어야 합니다: ${n}`);
  const f = "#c9b28a";
  return (
    '<svg viewBox="0 0 40 40">' +
    `<ellipse cx="10" cy="15" rx="3.6" ry="4.6" fill="${f}" transform="rotate(-20 10 15)"/>` +
    `<ellipse cx="16.5" cy="9" rx="3.6" ry="4.8" fill="${f}"/><ellipse cx="23.5" cy="9" rx="3.6" ry="4.8" fill="${f}"/>` +
    `<ellipse cx="30" cy="15" rx="3.6" ry="4.6" fill="${f}" transform="rotate(20 30 15)"/>` +
    `<path d="M20 18 C 28 18, 32 25, 30 30 C 28 35, 23 33, 20 33 C 17 33, 12 35, 10 30 C 8 25, 12 18, 20 18 Z" fill="${f}"/>` +
    `<text x="20" y="30.5" text-anchor="middle" font-size="13" font-weight="800" font-family="system-ui,sans-serif" fill="#3e2f1c">${n}</text></svg>`
  );
}
