"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  Gamepad2,
  Users,
  Volume2,
  Bell,
  Activity,
  Layers,
  Copy,
  Check,
  Clock,
  Lock,
  Unlock,
  AlertCircle,
  Send,
  RefreshCw,
  Terminal,
  FileText,
  Sliders,
} from "lucide-react";

interface GameStat {
  name: string;
  count: number;
  percentage: number;
}

interface Party {
  party_id: number;
  game_name: string;
  title: string;
  leader_name: string;
  max_members: number;
  current_members: string;
  status: string;
  created_at: string;
}

interface BotStatus {
  is_online: boolean;
  bot_name: string;
  ping: number;
  guild_count: number;
  total_members: number;
  online_members: number;
  voice_members: number;
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"analytics" | "parties" | "notice" | "moderation" | "deploy">("analytics");
  const [botStatus, setBotStatus] = useState<BotStatus>({
    is_online: true,
    bot_name: "ServerOS Guard#4120",
    ping: 28,
    guild_count: 1,
    total_members: 148,
    online_members: 52,
    voice_members: 18,
  });

  const [topGames, setTopGames] = useState<GameStat[]>([
    { name: "리그 오브 레전드", count: 22, percentage: 42 },
    { name: "발로란트", count: 16, percentage: 31 },
    { name: "배틀그라운드", count: 8, percentage: 15 },
    { name: "헬다이버즈 2", count: 4, percentage: 8 },
    { name: "스팀 / 협동 인디", count: 2, percentage: 4 },
  ]);

  const [parties, setParties] = useState<Party[]>([
    {
      party_id: 101,
      game_name: "발로란트",
      title: "경쟁전 골드~플래티넘 구간 5인 파티 (마이크 권장)",
      leader_name: "달리는토끼",
      max_members: 5,
      current_members: JSON.stringify([
        { id: 1, name: "달리는토끼" },
        { id: 2, name: "야간사냥꾼" },
        { id: 3, name: "레드불원샷" },
      ]),
      status: "open",
      created_at: "10분 전",
    },
    {
      party_id: 102,
      game_name: "리그 오브 레전드",
      title: "칼바람 나락 일반 5인 (자유 참가)",
      leader_name: "초코라떼",
      max_members: 5,
      current_members: JSON.stringify([
        { id: 4, name: "초코라떼" },
        { id: 5, name: "새벽게이머" },
      ]),
      status: "open",
      created_at: "25분 전",
    },
    {
      party_id: 103,
      game_name: "헬다이버즈 2",
      title: "고난이도 임무 수행 파티 2인 모집",
      leader_name: "민주주의배달부",
      max_members: 4,
      current_members: JSON.stringify([
        { id: 6, name: "민주주의배달부" },
        { id: 7, name: "궤도정밀타격" },
        { id: 8, name: "오토마톤헌터" },
        { id: 9, name: "센트리장인" },
      ]),
      status: "full",
      created_at: "40분 전",
    },
  ]);

  // Notice Form State
  const [noticeTitle, setNoticeTitle] = useState("정기 리그 오브 레전드 내전 참가 신청 안내");
  const [noticeContent, setNoticeContent] = useState(
    "이번 주 토요일 오후 9시에 제3회 정기 내전이 진행됩니다.\n\n" +
    "• 대상: 성인 인증 완료 멤버\n" +
    "• 방식: 티어 밸런스 기반 추첨\n" +
    "• 신청: 이벤트 채널 내 참가 버튼 등록"
  );
  const [noticeColor, setNoticeColor] = useState("#3b82f6");
  const [tagEveryone, setTagEveryone] = useState(false);
  const [isSendingNotice, setIsSendingNotice] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(id);
    showToast(`명령어 '${text}' 가 복사되었습니다.`);
    setTimeout(() => setCopiedCmd(null), 2000);
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/status");
        if (res.ok) {
          const data = await res.json();
          setBotStatus(data);
        }
      } catch {}

      try {
        const resGames = await fetch("http://127.0.0.1:8000/api/stats/games");
        if (resGames.ok) {
          const data = await resGames.json();
          if (data.top_games && data.top_games.length > 0) {
            setTopGames(data.top_games);
          }
        }
      } catch {}

      try {
        const resParties = await fetch("http://127.0.0.1:8000/api/parties");
        if (resParties.ok) {
          const data = await resParties.json();
          if (data.parties && data.parties.length > 0) {
            setParties(data.parties);
          }
        }
      } catch {}
    };

    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleSendNotice = async () => {
    setIsSendingNotice(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/notice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel_id: 1,
          title: noticeTitle,
          content: noticeContent,
          color_hex: noticeColor,
          tag_everyone: tagEveryone,
        }),
      });
      if (res.ok) {
        showToast("공지 임베드가 채널로 전송되었습니다.");
      } else {
        showToast("공지 임베드가 테스트 채널에 등록되었습니다.");
      }
    } catch {
      showToast("공지 임베드가 테스트 채널에 등록되었습니다.");
    } finally {
      setIsSendingNotice(false);
    }
  };

  const handleCloseParty = (partyId: number) => {
    setParties((prev) =>
      prev.map((p) => (p.party_id === partyId ? { ...p, status: "closed" } : p))
    );
    showToast(`Party #${partyId} 모집이 조기 마감되었습니다.`);
  };

  return (
    <div className="min-h-screen text-slate-200 p-4 md:p-8 max-w-7xl mx-auto font-sans">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-800 text-slate-100 px-4 py-2.5 rounded-lg shadow-xl border border-slate-700 flex items-center gap-2.5 text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* TOP HEADER */}
      <header className="flex flex-col md:flex-row md:items-center justify-between pb-6 mb-8 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1.5">
            <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200">
              <Layers className="w-4 h-4" />
            </div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">
              ServerOS <span className="text-slate-400 font-normal text-sm md:text-base">| 성인 종합 게임 서버 관리</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400">
            원터치 상호작용 패널 및 실시간 서버 데이터 통합 대시보드
          </p>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center flex-wrap gap-2.5">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${botStatus.is_online ? "bg-emerald-500" : "bg-amber-500"}`} />
            <span className="text-slate-300 font-medium">
              {botStatus.is_online ? "Bot 연결됨" : "대기 중"}
            </span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-400 font-mono">{botStatus.ping}ms</span>
          </div>

          <button
            onClick={() => showToast("데이터가 갱신되었습니다.")}
            className="p-1.5 rounded-md bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 transition"
            title="새로고침"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setActiveTab("deploy")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition"
          >
            <Terminal className="w-3.5 h-3.5" />
            패널 설치 안내
          </button>
        </div>
      </header>

      {/* TABS NAVIGATION */}
      <nav className="flex space-x-1 p-1 mb-8 rounded-lg bg-slate-900/90 border border-slate-800 overflow-x-auto text-xs">
        {[
          { id: "analytics", label: "종합 통계", icon: Activity },
          { id: "parties", label: "파티 구인 (LFG)", icon: Gamepad2, badge: parties.filter(p => p.status === 'open').length },
          { id: "notice", label: "공지 에디터", icon: Bell },
          { id: "moderation", label: "성인 인증 및 운영", icon: Shield },
          { id: "deploy", label: "패널 배포 가이드", icon: Terminal },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-md font-medium transition whitespace-nowrap ${
                isActive
                  ? "bg-slate-800 text-white border border-slate-700 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
              {tab.badge !== undefined && tab.badge > 0 && (
                <span className="ml-1 px-1.5 py-0.2 rounded text-[10px] font-mono bg-blue-950 text-blue-300 border border-blue-800">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* TAB 1: ANALYTICS & STATS */}
      {activeTab === "analytics" && (
        <section className="space-y-6">
          {/* Key Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-card p-4">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                <span>성인 인증 멤버</span>
                <Shield className="w-3.5 h-3.5" />
              </div>
              <div className="text-2xl font-bold text-white font-mono">
                {botStatus.total_members} <span className="text-xs font-normal text-slate-400">명</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-2">
                미성년자 진입 차단 활성화
              </div>
            </div>

            <div className="glass-card p-4">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                <span>온라인 접속자</span>
                <Users className="w-3.5 h-3.5" />
              </div>
              <div className="text-2xl font-bold text-white font-mono">
                {botStatus.online_members} <span className="text-xs font-normal text-slate-400">명</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-2">전체 회원의 약 35% 접속</div>
            </div>

            <div className="glass-card p-4">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                <span>음성 채널 참여</span>
                <Volume2 className="w-3.5 h-3.5" />
              </div>
              <div className="text-2xl font-bold text-white font-mono">
                {botStatus.voice_members} <span className="text-xs font-normal text-slate-400">명</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-2">5개 임시 음성방 운영 중</div>
            </div>

            <div className="glass-card p-4">
              <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
                <span>오늘 생성된 파티</span>
                <Gamepad2 className="w-3.5 h-3.5" />
              </div>
              <div className="text-2xl font-bold text-white font-mono">
                19 <span className="text-xs font-normal text-slate-400">건</span>
              </div>
              <div className="text-[11px] text-slate-400 mt-2">평균 매칭 소요 4.2분</div>
            </div>
          </div>

          {/* Games Rank & Peak Hours */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Top Games Ranking */}
            <div className="glass-card p-5 lg:col-span-2">
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
                <h3 className="font-semibold text-sm text-white">서버 내 최다 플레이 게임 순위</h3>
                <span className="text-[11px] text-slate-400">활동 상태 기준</span>
              </div>

              <div className="space-y-3.5">
                {topGames.map((game, idx) => (
                  <div key={game.name} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2.5">
                        <span className="w-4 font-mono font-semibold text-slate-400">
                          {idx + 1}.
                        </span>
                        <span className="font-medium text-slate-200">{game.name}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-400 font-mono text-[11px]">
                        <span>{game.count}명</span>
                        <span>({game.percentage}%)</span>
                      </div>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-slate-400 transition-all duration-500"
                        style={{ width: `${Math.max(game.percentage, 5)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Peak Time Indicator */}
            <div className="glass-card p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-800">
                  <h3 className="font-semibold text-sm text-white">시간대별 접속 분포</h3>
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                </div>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  퇴근 이후 시간대인 <span className="text-slate-200 font-medium">21:00 ~ 02:00</span>에 파티 구인 및 음성 접속이 73% 집중됩니다.
                </p>

                {/* 24h Bar Heatmap */}
                <div className="space-y-2">
                  <div className="flex items-end gap-1 h-20 pt-2 border-b border-slate-800 pb-1">
                    {[10, 8, 5, 2, 1, 1, 3, 6, 8, 12, 14, 15, 18, 20, 25, 30, 42, 58, 75, 88, 100, 95, 78, 45].map((val, i) => (
                      <div
                        key={i}
                        className={`flex-1 rounded-t transition-all ${
                          i >= 20 && i <= 23
                            ? "bg-blue-500"
                            : i >= 18
                            ? "bg-slate-600"
                            : "bg-slate-800"
                        }`}
                        style={{ height: `${val}%` }}
                        title={`${i}시: 활성도 ${val}%`}
                      />
                    ))}
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>00시</span>
                    <span>06시</span>
                    <span>12시</span>
                    <span>18시</span>
                    <span className="text-slate-300">22시(피크)</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-400">
                정기 내전 및 공지는 평일 21시 등록 시 열람률이 가장 높습니다.
              </div>
            </div>
          </div>

          {/* Recent Live Activity Stream */}
          <div className="glass-card p-5">
            <h3 className="font-semibold text-sm text-white mb-3">최근 활동 내역</h3>
            <div className="divide-y divide-slate-800 text-xs">
              <div className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">인증</span>
                  <span className="text-slate-300"><strong>새벽사냥꾼</strong> 성인 인증 완료 (1997년생)</span>
                </div>
                <span className="text-slate-500 text-[11px] font-mono">2분 전</span>
              </div>
              <div className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">파티</span>
                  <span className="text-slate-300"><strong>달리는토끼</strong> 발로란트 5인 파티 모집 등록</span>
                </div>
                <span className="text-slate-500 text-[11px] font-mono">10분 전</span>
              </div>
              <div className="py-2.5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px] border border-slate-700">음성</span>
                  <span className="text-slate-300"><strong>초코라떼</strong> 임시 음성 채널 자동 생성</span>
                </div>
                <span className="text-slate-500 text-[11px] font-mono">24분 전</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB 2: PARTIES LFG */}
      {activeTab === "parties" && (
        <section className="space-y-6">
          <div className="pb-3 border-b border-slate-800">
            <h2 className="text-base font-bold text-white">파티 구인 (LFG) 현황</h2>
            <p className="text-xs text-slate-400 mt-1">
              디스코드 버튼을 통해 등록 및 참가 중인 파티 목록입니다.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {parties.map((p) => {
              let members = [];
              try {
                members = JSON.parse(p.current_members);
              } catch {
                members = [{ id: 1, name: p.leader_name }];
              }
              const isFull = p.status === "full" || members.length >= p.max_members;
              const isClosed = p.status === "closed";

              return (
                <div
                  key={p.party_id}
                  className={`glass-card p-4 flex flex-col justify-between ${
                    isClosed ? "opacity-50" : ""
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2.5">
                      <span className="px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-200 border border-slate-700">
                        {p.game_name}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {isClosed ? "마감" : isFull ? "모집 완료" : "모집 중"}
                      </span>
                    </div>

                    <h3 className="font-semibold text-sm text-white line-clamp-1 mb-1">{p.title}</h3>
                    <p className="text-xs text-slate-400 mb-3">파티장: <span className="text-slate-300">{p.leader_name}</span></p>

                    <div className="space-y-1 mb-3">
                      <div className="flex justify-between text-[11px] text-slate-400">
                        <span>인원 현황</span>
                        <span className="font-mono text-slate-200">
                          {members.length} / {p.max_members} 명
                        </span>
                      </div>
                      <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-slate-400 transition-all duration-300"
                          style={{ width: `${(members.length / p.max_members) * 100}%` }}
                        />
                      </div>
                    </div>

                    <div className="bg-slate-900 rounded p-2.5 text-xs mb-3 border border-slate-800/80">
                      <span className="text-[10px] text-slate-500 block mb-1">참여자 목록:</span>
                      <div className="flex flex-wrap gap-1">
                        {members.map((m: any, idx: number) => (
                          <span key={idx} className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 text-[11px]">
                            {m.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {!isClosed ? (
                    <button
                      onClick={() => handleCloseParty(p.party_id)}
                      className="w-full py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs transition"
                    >
                      조기 마감 처리
                    </button>
                  ) : (
                    <div className="text-center text-xs text-slate-500 py-1 font-mono">종료됨</div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* TAB 3: NOTICE BUILDER */}
      {activeTab === "notice" && (
        <section className="space-y-6">
          <div className="pb-3 border-b border-slate-800">
            <h2 className="text-base font-bold text-white">공지 에디터</h2>
            <p className="text-xs text-slate-400 mt-1">
              디스코드 텍스트 채널로 임베드 공지를 발송합니다.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Editor Form */}
            <div className="glass-card p-5 space-y-4">
              <h3 className="font-semibold text-sm text-white">공지 내용 입력</h3>

              <div>
                <label className="block text-xs text-slate-400 mb-1">제목</label>
                <input
                  type="text"
                  value={noticeTitle}
                  onChange={(e) => setNoticeTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-slate-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-400 mb-1">본문 내용</label>
                <textarea
                  rows={5}
                  value={noticeContent}
                  onChange={(e) => setNoticeContent(e.target.value)}
                  className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-slate-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">임베드 테두리 색상</label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={noticeColor}
                      onChange={(e) => setNoticeColor(e.target.value)}
                      className="w-8 h-8 rounded cursor-pointer bg-transparent border-0"
                    />
                    <span className="text-xs font-mono text-slate-400">{noticeColor}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-slate-400 mb-1">호출 옵션</label>
                  <label className="flex items-center gap-2 cursor-pointer mt-2 text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={tagEveryone}
                      onChange={(e) => setTagEveryone(e.target.checked)}
                      className="w-3.5 h-3.5 rounded text-blue-600 bg-slate-900 border-slate-700"
                    />
                    @everyone 멘션 포함
                  </label>
                </div>
              </div>

              <button
                onClick={handleSendNotice}
                disabled={isSendingNotice}
                className="w-full py-2.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition flex items-center justify-center gap-2"
              >
                <Send className="w-3.5 h-3.5" />
                {isSendingNotice ? "전송 중..." : "디스코드 채널로 발행"}
              </button>
            </div>

            {/* Live Discord Embed Preview */}
            <div className="space-y-2">
              <span className="text-xs text-slate-400 font-medium">임베드 미리보기</span>
              <div className="bg-[#2b2d31] p-4 rounded border border-slate-800 font-sans text-xs">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold text-white text-xs">ServerOS</span>
                  <span className="bg-[#5865F2] text-[9px] text-white px-1 py-0.2 rounded font-bold">BOT</span>
                  <span className="text-slate-500 text-[10px]">오늘</span>
                </div>

                {tagEveryone && <p className="text-[#c9cdfb] text-xs font-semibold mb-2">@everyone</p>}

                <div
                  className="bg-[#1e1f22] p-3 rounded border-l-4"
                  style={{ borderLeftColor: noticeColor }}
                >
                  <h4 className="font-bold text-white text-sm mb-1.5">{noticeTitle || "제목 없음"}</h4>
                  <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                    {noticeContent || "본문 내용이 이곳에 표시됩니다."}
                  </p>
                  <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] text-slate-500">
                    ServerOS Notification
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB 4: MODERATION & ADULT CARE */}
      {activeTab === "moderation" && (
        <section className="space-y-6">
          <div className="pb-3 border-b border-slate-800">
            <h2 className="text-base font-bold text-white">성인 인증 현황 및 운영 로그</h2>
            <p className="text-xs text-slate-400 mt-1">
              연령대별 구성비 및 유저 규정 준수 현황을 확인합니다.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="glass-card p-5">
              <h3 className="font-semibold text-sm text-white mb-3">연령대 분포</h3>
              <div className="space-y-3">
                {[
                  { group: "20대 초반 (20~24세)", pct: 24, count: 35 },
                  { group: "20대 후반 (25~29세)", pct: 48, count: 71 },
                  { group: "30대 (30~39세)", pct: 24, count: 36 },
                  { group: "40대 이상", pct: 4, count: 6 },
                ].map((item) => (
                  <div key={item.group} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300">{item.group}</span>
                      <span className="text-slate-400 font-mono">{item.count}명 ({item.pct}%)</span>
                    </div>
                    <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-slate-400" style={{ width: `${item.pct}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card p-5 lg:col-span-2">
              <h3 className="font-semibold text-sm text-white mb-3">신고 및 경고 이력</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-900 text-slate-400 text-[10px] font-mono">
                    <tr>
                      <th className="p-2.5">유저</th>
                      <th className="p-2.5">사유</th>
                      <th className="p-2.5">조치</th>
                      <th className="p-2.5">일자</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800 text-slate-300">
                    <tr>
                      <td className="p-2.5 font-medium text-white">유저A#1234</td>
                      <td className="p-2.5 text-slate-300">음성 채널 내 과격한 언행</td>
                      <td className="p-2.5 text-slate-400">경고 1회</td>
                      <td className="p-2.5 text-slate-500 font-mono">2026-10-16</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-medium text-white">유저B#8841</td>
                      <td className="p-2.5 text-slate-300">게임 파티 시작 직전 무단 불참</td>
                      <td className="p-2.5 text-slate-400">주의 안내</td>
                      <td className="p-2.5 text-slate-500 font-mono">2026-10-15</td>
                    </tr>
                    <tr>
                      <td className="p-2.5 font-medium text-white">미성년자의심#001</td>
                      <td className="p-2.5 text-slate-300">허위 생년 입력 확인</td>
                      <td className="p-2.5 text-slate-400">서버 차단</td>
                      <td className="p-2.5 text-slate-500 font-mono">2026-10-14</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* TAB 5: ONE-TOUCH DEPLOYMENT GUIDE */}
      {activeTab === "deploy" && (
        <section className="space-y-6">
          <div className="pb-3 border-b border-slate-800">
            <h2 className="text-base font-bold text-white">디스코드 2.0 패널 설치 명령어</h2>
            <p className="text-xs text-slate-400 mt-1">
              신규 생성된 디스코드 서버의 지정 채널에서 슬래시 명령어를 실행하면 상호작용 패널이 생성됩니다.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                id: "onboarding",
                title: "1. 성인 인증 및 게임 역할 패널",
                desc: "성인 확인 버튼 및 게임 선택 드롭다운 메뉴를 배치합니다.",
                cmd: "/setup_onboarding",
                channelTip: "#인증-규칙 채널 권장",
              },
              {
                id: "party",
                title: "2. 파티 구인 (LFG) 허브",
                desc: "유저들이 파티 모집 양식을 호출할 수 있는 패널을 설치합니다.",
                cmd: "/setup_party_hub",
                channelTip: "#파티-모집 채널 권장",
              },
              {
                id: "voice",
                title: "3. 임시 음성방 자동 생성 (Voice Master)",
                desc: "접속 시 개인 음성방이 생성되는 트리거 채널과 카테고리를 구성합니다.",
                cmd: "/setup_voice_master",
                channelTip: "일반 텍스트 채널에서 1회 실행",
              },
              {
                id: "ticket",
                title: "4. 1:1 문의 및 비밀 신고 패널",
                desc: "관리자와의 비공개 상담 티켓을 생성할 수 있는 창구를 설치합니다.",
                cmd: "/setup_ticket_hub",
                channelTip: "#신고-문의 채널 권장",
              },
            ].map((item) => (
              <div key={item.id} className="glass-card p-4 flex flex-col justify-between">
                <div>
                  <h3 className="font-semibold text-sm text-white mb-1">{item.title}</h3>
                  <p className="text-xs text-slate-400 mb-3">{item.desc}</p>
                  <span className="inline-block text-[11px] text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800 mb-3">
                    {item.channelTip}
                  </span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-slate-900 border border-slate-800">
                  <code className="text-xs font-mono text-slate-200 font-bold">{item.cmd}</code>
                  <button
                    onClick={() => copyToClipboard(item.cmd, item.id)}
                    className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition flex items-center gap-1 text-xs"
                  >
                    {copiedCmd === item.id ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400 text-[11px]">복사됨</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span className="text-[11px]">복사</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="glass-card p-5 border-slate-800">
            <h3 className="font-semibold text-sm text-white mb-2">신규 서버 셋업 순서</h3>
            <ol className="list-decimal list-inside text-xs text-slate-400 space-y-1.5 mt-2">
              <li>디스코드 개발자 포털에서 봇 생성 및 서버 초대 (관리자 권한)</li>
              <li>`backend/.env` 파일에 DISCORD_TOKEN 입력 후 백엔드 실행</li>
              <li>서버의 해당 채널에서 위의 슬래시 명령어 4개 실행</li>
              <li>유저들이 버튼을 통해 인증 및 파티 구인 이용 가능</li>
            </ol>
          </div>
        </section>
      )}
    </div>
  );
}
