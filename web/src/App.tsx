import { useEffect } from "react";
import { ResumeCurrentGame } from "./game/resume";
import { BrowserRouter, Route, Routes } from "react-router";
import { AuthCallbackPage } from "./pages/AuthCallbackPage";
import { BotSelectPage } from "./pages/BotSelectPage";
import { JoinRoomPage } from "./pages/JoinRoomPage";
import { LobbyPage } from "./pages/LobbyPage";
import { LoginPage } from "./pages/LoginPage";
import { MyCatsPage } from "./pages/MyCatsPage";
import { NicknamePage } from "./pages/NicknamePage";
import { PlayPage } from "./pages/PlayPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RankingPage } from "./pages/RankingPage";
import { SignupPage } from "./pages/SignupPage";
import { SinglePlayPage } from "./pages/SinglePlayPage";
import { SingleSelectPage } from "./pages/SingleSelectPage";
import { verifySession } from "./session/sessionStore";

export function App() {
  useEffect(() => {
    verifySession().catch((error) => console.error("세션 확인 실패", error));
  }, []);

  return (
    <BrowserRouter>
      <ResumeCurrentGame />
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/r/:code" element={<JoinRoomPage />} />
        <Route path="/play/:gameId" element={<PlayPage />} />
        <Route path="/me/cats" element={<MyCatsPage />} />
        <Route path="/bot" element={<BotSelectPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/me/nickname" element={<NicknamePage />} />
        <Route path="/ranking" element={<RankingPage />} />
        <Route path="/single" element={<SingleSelectPage />} />
        <Route path="/single/:difficulty" element={<SinglePlayPage />} />
        <Route path="/players/:id" element={<ProfilePage />} />
      </Routes>
    </BrowserRouter>
  );
}
