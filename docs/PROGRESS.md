# Progress

Last updated 2026-11-05. All work so far is merged into `main`.

## Done (verified on the user's iPhone unless noted)

| Phase | Commits (newest first within phase) | Notes |
|---|---|---|
| F1 Siri booking, single-user backend | 6ad1210 | booking rules, duplicate protection, natural confirmations, Siri card Earlier/Later |
| F2 widgets, Control Center, Action button | 6ad1210 | widget extension added by editing project.pbxproj |
| Test DB isolation | 586cf41, 80ad919 | second fix after a regression (see Known issues history) |
| Agent + memory | 8dc1423 | LangGraph tool agent, PostgresSaver, fallback, partial-failure honesty |
| Ask Clear Path chat, voice, Siri ask | 7e9c997 | SpeechAnalyzer, shared conversation |
| F8 RAG | 2b1f9dd, bbda162 | rules + pgvector + citations |
| F6 tracking | d88f268, 5dc6603 | simulator, Live Activity, map, Siri "Track my shuttle" |
| F4/F5 trip mode | bc9fb5f, 44736dd, 0b3da67, 891db65, 027418e | background location, local notifications, Rebook, walk time, model latency fix |
| F11/E MCP | 569efb9, 7fd6d81, 6125dec | verified in Claude Desktop 2026-11-04 |
| F12 evals + Langfuse | 4045638, 2ffc947, 52116d8 | baseline 22/24; self-hosted Langfuse |
| Config | c4363e3 | backend address 172.20.1.13 |
| F3 schedule import | 1d7fe8f | share extension + in-app import, on-device OCR + Foundation Models, `/schedule/plan` + `/apply`, injection screening, extraction eval; verified on iPhone 2026-11-05 (share sheet, injection sample, in-app import) |

## Next (agreed order)

1. **F3 leftover**: run `AIShuttle/ScheduleImportEvals/run.sh` once Apple
   Intelligence is on (on the Mac) and record the on-device model's numbers
   in AI.md.
2. **F7 — goal-based planning**: "Get me to the office by 8:30" with a
   planner + specialised agents (schedule / transport / booking) where it
   genuinely helps; reuse for F4's alternative choice. Add eval cases first.
3. **F10 — habit suggestions**: donate booking intents
   (`IntentDonationManager`), learn "usual" from history.
4. **F13 — reliability demo**: script for "Gemini key off → Siri booking
   still works" (document injection screening is done in F3).
5. **Demo runbook polish and rehearsal**; update the original planning docs
   if wanted (they live outside the repo).
6. Optional: on-device Foundation Models routing.

## Known issues / caveats

- Xcode 26.4.1 build hang on the clang probe (workaround in CLAUDE.md).
- Siri on iOS 27 sometimes answers itself instead of running the intent;
  chained Siri bookings can lose the day. Use the documented phrases.
- Eval known failures: `delay-offers-alternative` (agent misstates delayed
  pickup time), `book-sunday-refused` (judge miscount).
- Free-tier Gemini: 429s and slow responses under bursts; 3.5-flash only
  20 requests/day. Evals pace themselves (`--pause`).
- Live Activity can't update while the app is suspended unless trip mode is
  running (no APNs).
- The demo route geometry is approximate (not road-snapped).
- A simulated trip replays a *future* booking now; the Lock Screen widget
  still shows its scheduled date (user accepted this).
- `tests/manual_gemini_*.py` hit the live API (not in the pytest run).
- Apple Intelligence is **off on the Mac**, so the schedule extraction eval
  has only measured the keyword-rules baseline so far (11/15). Turning it on
  (System Settings → Apple Intelligence & Siri; free, downloads the model)
  lets `run.sh` measure the on-device model too.
- The share extension adds a third bundle id
  (`com.yourcompany.AIShuttle.ClearPathShare`); free accounts may register
  only 10 App IDs per 7 days.

## Decision log

| Date | Decision |
|---|---|
| 2026-11-02 | Single user (no Emma); app named Clear Path kept, alternative names added |
| 2026-11-02 | Chat is secondary; OS surfaces first |
| 2026-11-02 | One booking intent with optional day (two intents confused Siri) |
| 2026-11-02 | No paid developer account → trip mode with background location instead of APNs |
| 2026-11-02 | Agent primary model gemini-3.5-flash-lite (measured), 8s deadline, fallback chain |
| 2026-11-02 | MCP 2.x SDK with own client adapter; weather server as the external example |
| 2026-11-03 | Nothing that costs money without discussing first (standing rule) |
| 2026-11-03 | No CI; Langfuse self-hosted in Docker |
| 2026-11-04 | Eval baseline saved (22/24) |
| 2026-11-05 | F3 uses a share extension: iOS 26 can't put an App Intent in the share sheet without the user building a Shortcut |
| 2026-11-05 | F3 planning is deterministic on the server, not the cloud agent: days→bookings is a rule; only typed `{date, kind}` days leave the phone, so document text can't reach Gemini or any tool |
| 2026-11-05 | F3 falls back to keyword rules when Apple Intelligence is unavailable; the same rules are the eval baseline |
