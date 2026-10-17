import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ServerOS — 성인 종합 게임 서버 올인원 관리 대시보드",
  description: "디스코드 2.0 기반 원터치 파티 구인, 성인 인증, 스마트 음성 채널 및 실시간 게임 생태계 분석 대시보드",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+KR:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased selection:bg-purple-500/30 selection:text-purple-200">
        {children}
      </body>
    </html>
  );
}
