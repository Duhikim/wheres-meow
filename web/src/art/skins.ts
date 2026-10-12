// 확정한 고양이 스킨 10종 (시안 docs/superpowers/specs/2026-10-12-wheres-meow-mockups/skins-and-grass.html).
// 서버 account·game 도메인의 허용 목록과 같아야 한다.

export type Coat =
  | "orange" | "cheese" | "gray" | "brown" | "black"
  | "white" | "calico" | "siamese" | "tuxedo" | "russian";
export type Eyes = "dot" | "big" | "happy" | "slit" | "sleepy" | "wink" | "sparkle";
export type Mouth = "w" | "open" | "flat" | "o";
export type Ears = "pointy" | "round" | "fold";

export interface SkinConfig {
  name: string;
  coat: Coat;
  eyes: Eyes;
  mouth: Mouth;
  ears?: Ears;
  blush?: boolean;
  whiskers?: boolean;
  outline?: boolean; // 기본 true
}

export const SKINS: Record<number, SkinConfig> = {
  16: { name: "치즈 태비", coat: "orange", eyes: "big", mouth: "w" },
  17: { name: "까망이", coat: "black", eyes: "slit", mouth: "flat" },
  18: { name: "삼색이", coat: "calico", eyes: "dot", mouth: "w", blush: true },
  19: { name: "회색 태비", coat: "gray", eyes: "happy", mouth: "w" },
  20: { name: "샴", coat: "siamese", eyes: "big", mouth: "w", outline: false },
  21: { name: "흰둥이", coat: "white", eyes: "sleepy", mouth: "w", blush: true },
  9: { name: "턱시도", coat: "tuxedo", eyes: "dot", mouth: "w", whiskers: true },
  10: { name: "러시안블루", coat: "russian", eyes: "slit", mouth: "w", outline: false },
  11: { name: "고등어", coat: "brown", eyes: "sleepy", mouth: "w" },
  12: { name: "접힌 귀 회색 태비", coat: "gray", eyes: "big", mouth: "w", blush: true, ears: "fold" },
};

/** 화면에 늘어놓는 순서. 시안 카탈로그 순서를 따른다. */
export const SKIN_ORDER = [16, 17, 18, 19, 20, 21, 9, 10, 11, 12] as const;
export const ALLOWED_SKINS: ReadonlySet<number> = new Set(SKIN_ORDER);
export const DEFAULT_SKIN_1P = 16;
export const DEFAULT_SKIN_2P = 17;

/** 스킨의 대표 색. 점수와 타이머 막대 같은 강조색에 쓴다. */
export const SKIN_ACCENT: Record<Coat, string> = {
  orange: "#e07b2a", cheese: "#e0a43a", gray: "#6f7d8f", brown: "#8a5f3f", black: "#36323c",
  white: "#a89f92", calico: "#d9822b", siamese: "#5e4838", tuxedo: "#2f2c33", russian: "#5f7393",
};

export function skinConfig(skin: number): SkinConfig {
  const config = SKINS[skin];
  if (!config) throw new Error(`허용하지 않는 스킨입니다: ${skin}`);
  return config;
}
