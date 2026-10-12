/**
 * 칸을 열 때 나는 효과음. 고양이 울음은 CC0 녹음 6개 중 하나를 무작위로 틀고(출처는 CREDITS.md),
 * 발자국 "뾱"(푹신)과 흙 "삭"(삭삭삭)은 Web Audio 로 그 자리에서 합성한다.
 * 브라우저는 사용자가 화면을 한 번 누르기 전에는 소리를 막으므로, 첫 입력 때 오디오를 깨운다.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CellPayload } from "../game/types";

export type SoundKind = "cat" | "paw" | "dirt";

export const MEOW_FILES = [
  "/sounds/meow-kitten-imitation.mp3",
  "/sounds/meow-cute-kitten.mp3",
  "/sounds/meow-kitty.mp3",
  "/sounds/meow-2.mp3",
  "/sounds/meow-mew.mp3",
  "/sounds/meow-long.mp3",
] as const;

interface SoundSettings {
  enabled: boolean;
  toggle: () => void;
}

/** 소리 켜기·끄기. 처음에는 켜 두고, 고른 값은 이 기기에 남긴다. */
export const useSoundSettings = create<SoundSettings>()(
  persist((set) => ({ enabled: true, toggle: () => set((s) => ({ enabled: !s.enabled })) }), {
    name: "wheresmeow-sound",
  }),
);

/** 열린 칸들로 낼 소리를 정한다. 고양이 > 발자국(숫자) > 빈 흙 순서다. */
export function soundKindOfCells(cells: CellPayload[]): SoundKind | null {
  if (cells.length === 0) return null;
  if (cells.some((c) => c.kind === "cat")) return "cat";
  if (cells.some((c) => c.kind === "number" && c.n > 0)) return "paw";
  return "dirt";
}

export function pickMeow(random: () => number = Math.random): string {
  return MEOW_FILES[Math.min(MEOW_FILES.length - 1, Math.floor(random() * MEOW_FILES.length))];
}

let context: AudioContext | null = null;
const meowBuffers = new Map<string, Promise<AudioBuffer>>();

function audio(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  context ??= new Ctor();
  return context;
}

/** 첫 사용자 입력에서 부른다. 휴대폰 브라우저가 막아 둔 오디오를 깨우고 울음 파일을 미리 받아 둔다. */
export function unlockAudio(): void {
  const ctx = audio();
  if (!ctx) return;
  if (ctx.state === "suspended") ctx.resume().catch(() => {});
  for (const file of MEOW_FILES) loadMeow(ctx, file);
}

function loadMeow(ctx: AudioContext, file: string): Promise<AudioBuffer> {
  let buffer = meowBuffers.get(file);
  if (!buffer) {
    buffer = fetch(file)
      .then((response) => {
        if (!response.ok) throw new Error(`울음 파일을 받지 못했습니다: ${file} (${response.status})`);
        return response.arrayBuffer();
      })
      .then((data) => ctx.decodeAudioData(data));
    buffer.catch(() => meowBuffers.delete(file)); // 실패하면 다음에 다시 받는다
    meowBuffers.set(file, buffer);
  }
  return buffer;
}

function envelope(gain: GainNode, t: number, attack: number, peak: number, decay: number): void {
  gain.gain.setValueAtTime(0.0001, t);
  gain.gain.exponentialRampToValueAtTime(peak, t + attack);
  gain.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
}

/** 발자국 "뾱" 20번(푹신): 아주 작고 낮게 올라가는 사인파. */
function playPaw(ctx: AudioContext): void {
  const t = ctx.currentTime + 0.01;
  const osc = ctx.createOscillator();
  osc.type = "sine";
  osc.frequency.setValueAtTime(220, t);
  osc.frequency.exponentialRampToValueAtTime(420, t + 0.084);
  const gain = ctx.createGain();
  envelope(gain, t, 0.005, 0.55, 0.14);
  osc.connect(gain).connect(ctx.destination);
  osc.start(t);
  osc.stop(t + 0.2);
}

let noise: AudioBuffer | null = null;

/** 흙 "삭" 10번(삭삭삭): 거른 잡음을 짧게 세 번. */
function playDirt(ctx: AudioContext): void {
  if (!noise || noise.sampleRate !== ctx.sampleRate) {
    noise = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
    const data = noise.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  }
  const start = ctx.currentTime + 0.01;
  const dur = 0.07;
  for (let k = 0; k < 3; k++) {
    const t = start + k * dur * 0.7;
    const source = ctx.createBufferSource();
    source.buffer = noise;
    const highpass = ctx.createBiquadFilter();
    highpass.type = "highpass";
    highpass.frequency.value = 1200;
    const lowpass = ctx.createBiquadFilter();
    lowpass.type = "lowpass";
    lowpass.frequency.setValueAtTime(6000, t);
    lowpass.frequency.exponentialRampToValueAtTime(2100, t + dur);
    const gain = ctx.createGain();
    envelope(gain, t, 0.008, 0.28, dur * 0.85);
    source.connect(highpass).connect(lowpass).connect(gain).connect(ctx.destination);
    source.start(t, Math.random() * 0.5);
    source.stop(t + dur + 0.02);
  }
}

async function playCat(ctx: AudioContext): Promise<void> {
  const buffer = await loadMeow(ctx, pickMeow());
  const source = ctx.createBufferSource();
  source.buffer = buffer;
  const gain = ctx.createGain();
  gain.gain.value = 0.9;
  source.connect(gain).connect(ctx.destination);
  source.start();
}

export function playSound(kind: SoundKind): void {
  if (!useSoundSettings.getState().enabled) return;
  const ctx = audio();
  if (!ctx || ctx.state !== "running") return; // 아직 사용자 입력 전이면 조용히 넘어간다(브라우저 정책)
  if (kind === "paw") playPaw(ctx);
  else if (kind === "dirt") playDirt(ctx);
  else playCat(ctx).catch((error) => console.warn("고양이 소리를 내지 못했습니다", error));
}
