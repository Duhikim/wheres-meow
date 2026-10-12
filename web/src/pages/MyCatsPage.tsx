import { useState } from "react";
import { Link, Navigate } from "react-router";
import { ApiError } from "../api/http";
import { CatArt } from "../art/Art";
import { SKIN_ORDER, SKINS } from "../art/skins";
import { errorMessage } from "../errorMessages";
import { saveSkins, useSession } from "../session/sessionStore";

export interface SkinPair {
  skin1p: number;
  skin2p: number;
}
type Slot = "1p" | "2p";

/** 슬롯에 고양이를 넣는다. 다른 슬롯에 있는 고양이를 고르면 맞바꿔서 1P·2P 가 항상 다르게 유지된다. */
export function chooseSkin(current: SkinPair, slot: Slot, skin: number): SkinPair {
  const other = slot === "1p" ? current.skin2p : current.skin1p;
  const mine = slot === "1p" ? current.skin1p : current.skin2p;
  const nextOther = other === skin ? mine : other;
  return slot === "1p" ? { skin1p: skin, skin2p: nextOther } : { skin1p: nextOther, skin2p: skin };
}

export function MyCatsPage() {
  const player = useSession((s) => s.player);
  const [pair, setPair] = useState<SkinPair>(() => ({ skin1p: player?.skin1p ?? 16, skin2p: player?.skin2p ?? 17 }));
  const [slot, setSlot] = useState<Slot>("1p");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  if (!player) return <Navigate to="/" replace />;

  const changed = pair.skin1p !== player.skin1p || pair.skin2p !== player.skin2p;

  async function save() {
    setSaving(true);
    setMessage(null);
    try {
      await saveSkins(pair.skin1p, pair.skin2p);
      setMessage("저장했습니다.");
    } catch (e) {
      setMessage(errorMessage(e instanceof ApiError ? e.code : "INTERNAL"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="page">
      <Link to="/">← 로비</Link>
      <h2>내 고양이</h2>
      <p className="muted">평소엔 1P 를 쓰고, 상대와 겹치면 2P 로 바뀝니다. 슬롯을 고른 뒤 고양이를 누르세요.</p>

      <div className="slots">
        {(["1p", "2p"] as const).map((s) => {
          const skin = s === "1p" ? pair.skin1p : pair.skin2p;
          return (
            <button key={s} type="button" className={`slot${slot === s ? " editing" : ""}`} onClick={() => setSlot(s)}>
              <span>{s.toUpperCase()}</span>
              <CatArt skin={skin} size={72} />
              <small className="skin-name">{SKINS[skin].name}</small>
            </button>
          );
        })}
      </div>

      <div className="skin-grid">
        {SKIN_ORDER.map((skin) => {
          const tag = skin === pair.skin1p ? "1P" : skin === pair.skin2p ? "2P" : null;
          return (
            <button
              key={skin}
              type="button"
              aria-label={SKINS[skin].name}
              className={`skin${tag ? " chosen" : ""}`}
              onClick={() => setPair((p) => chooseSkin(p, slot, skin))}
            >
              <CatArt skin={skin} />
              {tag && <i className="tag">{tag}</i>}
            </button>
          );
        })}
      </div>

      <button className="btn primary block" type="button" disabled={!changed || saving} onClick={save}>
        저장
      </button>
      {message && <p className={message === "저장했습니다." ? "muted" : "error"}>{message}</p>}
    </main>
  );
}
