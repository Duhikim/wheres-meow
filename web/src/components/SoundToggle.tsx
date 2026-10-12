import { useSoundSettings } from "../sound/sound";

/** 효과음 켜기·끄기. 고른 값은 이 기기에 남는다. */
export function SoundToggle() {
  const { enabled, toggle } = useSoundSettings();
  return (
    <button
      className="btn ghost small sound-toggle"
      type="button"
      aria-pressed={enabled}
      aria-label={enabled ? "효과음 끄기" : "효과음 켜기"}
      onClick={toggle}
    >
      {enabled ? "🔊" : "🔇"}
    </button>
  );
}
