import { useEffect } from "react";
import { BrowserRouter, Route, Routes } from "react-router";
import { JoinRoomPage } from "./pages/JoinRoomPage";
import { LobbyPage } from "./pages/LobbyPage";
import { PlayPage } from "./pages/PlayPage";
import { verifySession } from "./session/sessionStore";

export function App() {
  useEffect(() => {
    verifySession().catch((error) => console.error("세션 확인 실패", error));
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/r/:code" element={<JoinRoomPage />} />
        <Route path="/play/:gameId" element={<PlayPage />} />
      </Routes>
    </BrowserRouter>
  );
}
