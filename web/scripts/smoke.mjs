// Vite 프록시(5173)를 거쳐 게스트 두 명이 초대 방으로 대국을 시작하고 한 수 두는지 확인한다.
import { io } from "socket.io-client";

const BASE = "http://127.0.0.1:5173";
const post = async (path, body, token) => {
  const res = await fetch(BASE + path, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
};
const once = (socket, name) => new Promise((resolve) => socket.once(name, resolve));

const a = await post("/api/guests", { nickname: "방장냥" });
const b = await post("/api/guests", { nickname: "손님냥" });
const room = await post("/api/rooms", null, a.token);
const sa = io(BASE, { auth: { token: a.token } });
const sb = io(BASE, { auth: { token: b.token } });
await Promise.all([once(sa, "connect"), once(sb, "connect")]);

const waiting = once(sa, "room:waiting");
sa.emit("room:join", { code: room.code });
console.log("waiting:", (await waiting).code === room.code);

const startedA = once(sa, "game:started");
const startedB = once(sb, "game:started");
sb.emit("room:join", { code: room.code });
const [ga, gb] = await Promise.all([startedA, startedB]);
console.log("started:", ga.gameId === gb.gameId, "seats:", ga.mySeat, gb.mySeat, "first:", ga.currentSeat);

const mover = ga.currentSeat === ga.mySeat ? sa : sb;
const revealed = once(sa, "game:revealed");
mover.emit("game:reveal", { gameId: ga.gameId, x: 5, y: 5 });
const r = await revealed;
console.log("revealed version:", r.version, "cells:", r.cells.length);

const ended = once(sb, "game:ended");
sa.emit("game:forfeit", { gameId: ga.gameId });
const e = await ended;
console.log("ended:", e.reason, "winner:", e.winner, "cats:", e.cats.length);
sa.close();
sb.close();
