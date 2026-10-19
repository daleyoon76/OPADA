# reviewer r1: 커밋 2e2ad9a 화면 머리 코드 판 표시

<sub>팀장 기록: reviewer 반환물의 판정·지적 표·고정 질문 답·생존 변이·종료 조건을 옮겼다(2026-10-19 · 읽기 전용 역할이라 팀장이 파일화). 원문 전문은 세션 기록에 있다.</sub>

- 대상 2e2ad9a(기준 2f0d0b4) · diff sha256 앞 16자 4af55461d4b1464c · 착수 17:15:42 KST
- 판정: 조건부 GO · 반드시 고칠 문제 0건 · 고려 4건 · 사소 5건
- GO 조건: (1) 고려-1(라이브 노출)을 동원님이 결정 (2) 고려-3(h5c 동치 주장) 커밋 본문 정정

| 등급 | 위치 | 내용 | 처방 |
|---|---|---|---|
| 고려-1 | server.py /api/version · 커밋 본문 | 끄는 수단이 코드에 없다. 상시 서버가 로컬 8975 와 ngrok 공개 주소를 함께 받아 결선 시연 화면에도 브랜치·해시·빨간 경고가 뜰 수 있다 | (a) Host 가 127.0.0.1·localhost 가 아니면 404 · 화면 숨김 (b) 환경변수 HOMETEST_SHOW_REVISION=1 일 때만 켬 |
| 고려-2 | server.py code_revision | 다른 저장소 안에 풀어 둔 .git 없는 사본은 바깥 저장소 판을 정상 판처럼 보인다 [관측 probe.py] | rev-parse --show-toplevel 을 resolve 해 base 와 다르면 빈 값 |
| 고려-3 | 커밋 본문 h5c 줄 | 커밋 없는 저장소에서 rev-parse --abbrev-ref HEAD 는 stdout HEAD · rc=128 이다. returncode 검사를 지우면 branch 가 "HEAD" 가 된다. 화면은 같다 | 본문 정정 · 커밋 없는 저장소 갈래 단정(branch == "") |
| 고려-4 | 단위·E2E | --abbrev-ref HEAD → HEAD 변이가 산다(bool(branch) · \\S+) | branch 기대값을 git 에서 직접 얻어 비교 |
| 사소-1 | app.js innerHTML | branch·commit 을 이스케이프하지 않는다 | textContent 사용 |
| 사소-2 | app.js current.commit && | 요청 때 git 읽기가 실패하면 경고 없이 정상 판처럼 보인다 | 「지금 판을 확인하지 못했습니다」 · E2E 갈래 |
| 사소-3 | server.py committedAt | 읽기만 하고 쓰지 않는다 | 화면에 넣거나 뺀다 |
| 사소-4 | server.py git status | 페이지를 열 때 index.lock 경합 가능 | --no-optional-locks |
| 사소-5 | app.js catch | 옛 서버면 404 HTML 로 「확인하지 못했습니다」만 나온다 | 「서버를 다시 시작해 보세요」 덧붙임 |

- 생존 변이: --abbrev-ref 제거 · current.commit && 제거 · --date 형식 · catch 문구 · h5c
- 실측: /api/version 1회(git 5회) 평균 0.123초 · ThreadingHTTPServer 라 다른 요청을 막지 않음
- 종료 조건: 최종 커밋 사본에서 server.py 의 ` if result.returncode == 0 else ""` 를 지우고 단위 테스트를 돌리면 pass < total 로 붉어야 한다(지금 2e2ad9a 는 408/408 초록).
