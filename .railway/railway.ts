import { defineRailway, github, preserve, project, service } from "railway/iac";

// Where's Meow 운영 구성. railway.toml(Config as Code, 2026-12-01 폐기 예정)을 대체한다.
// 환경 변수는 값을 코드에 두지 않고 preserve() 로 Railway 에 이미 있는 값을 유지한다.
export default defineRailway(() => {
  const web = service("web", {
    source: github("Duhikim/wheres-meow", { branch: "main" }),
    build: {
      builder: "DOCKERFILE", // 서비스 기본값(RAILPACK)이 아니라 저장소의 Dockerfile 로 빌드한다
      dockerfilePath: "Dockerfile",
    },
    deploy: {
      healthcheckPath: "/api/health",
      healthcheckTimeout: 60,
      // restartPolicyType 은 Railway 기본값 ON_FAILURE 를 쓴다. 명시하면 Railway 가 기본값을 비워서
      // 돌려주기 때문에 plan 에 차이가 계속 남는다(2026-10-12 확인, 실제 값은 ON_FAILURE)
      restartPolicyMaxRetries: 3,
    },
    // 진행 중 대국이 프로세스 메모리에 있으므로 반드시 1개만 띄운다
    replicas: { sfo: 1 },
    env: {
      WHERESMEOW_ASYNC_MODE: preserve(),
      WHERESMEOW_ENV: preserve(),
      WHERESMEOW_SECRET_KEY: preserve(),
    },
  });

  return project("wheres-meow", {
    resources: [web],
  });
});
