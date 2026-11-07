# Mobile (iOS)

Xcode 26.4.1, iOS SDK 26.4, deployment target 26.4, tested on an iPhone 17
(iPhone18,1) running iOS 27.0.1. Swift 5 language mode with
`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` and approachable concurrency;
Swift Testing for unit tests. Signing: automatic, team `5RXXN24YC5`
(**free account: no push notifications / APNs**). Display name "Clear Path".

## Targets

| Target | Bundle id | Contents |
|---|---|---|
| AIShuttle (app) | `com.yourcompany.AIShuttle` | `AIShuttle/` + `Shared/` + `ScheduleImport/` |
| ClearPathWidgets (widget extension) | `com.yourcompany.AIShuttle.ClearPathWidgets` | `ClearPathWidgets/` + `Shared/` |
| ClearPathShare (share extension) | `com.yourcompany.AIShuttle.ClearPathShare` | `ClearPathShare/` + `ScheduleImport/` + `Shared/` minus `BookTomorrowIntent`, `BookingConfirmation`, `ShuttleActivityAttributes` (membership exception set) |
| AIShuttleTests | `com.yourcompany.AIShuttleTests` | `AIShuttleTests/` |

Folders are file-system-synchronized groups (new files are picked up
automatically). Info.plist = generated + `AIShuttle-Info.plist` /
`ClearPathWidgets-Info.plist` / `ClearPathShare-Info.plist`:

- `BookingAPIBaseURL = $(BOOKING_API_BASE_URL)` — project build setting,
  currently `http://192.168.1.6:8000` (the Mac's Wi-Fi IP; update when it
  changes). Fallback constant in `Shared/BookingAPIClient.swift`.
- `INAlternativeAppNames` (max 3, install fails with 4): ClearPath,
  Clear Path Shuttle, Clear Footpath (from a dictation test).
- `UIBackgroundModes = [location]` (trip mode).
- Build-setting keys: microphone, speech recognition, location-when-in-use
  usage strings; `NSSupportsLiveActivities = YES`.

## Code map

```
AIShuttle/AppIntent/   BookMyUsualShuttleIntent (+ ShuttleBooking helper), BookingDay (AppEnum),
                       BookingSnippet (SnippetIntent + RescheduleBookingIntent + card view),
                       WhereIsMyShuttleIntent (LiveActivityIntent), AskClearPathIntent,
                       AIShuttleShortcuts (phrases)
AIShuttle/Assistant/   AssistantAPI (DTOs, ConversationStore), AssistantViewModel, AssistantView, VoiceInput
AIShuttle/Tracking/    TrackingAPI (TripStatusDTO), TrackingView (MapKit), ShuttleActivityController,
                       TripMonitor (trip mode), TripNotifications (+ NotificationResponder, AppDelegate)
AIShuttle/Views/       AppShellView (tabs, refresh on foreground), HomeView, RidesView, RideDetailsView, UpcomingRideCard
AIShuttle/ViewModels/  RidesViewModel (joins in-flight loads; survives cancelled .task callers; after each
                       load syncs habits: donations + reminders; bookUsual / pinUsual)
AIShuttle/Habits/      HabitSurfaces (HabitDonations, HabitReminders), HabitCard (Home → Your commute)
Shared/                BookingAPIClient (+ withTimeouts/forAssistant, ISO8601 decoder, NoContent),
                       BookingDTOs, BookingConfirmation (spoken text, BookingIntentError, notifier),
                       BookTomorrowIntent (widget/control), ShuttleActivityAttributes,
                       HabitDTOs (GET /habits, pin, HabitReminderID — any booking path withdraws that day's reminder)
ClearPathWidgets/      NextRideWidget, BookShuttleControl, ShuttleLiveActivity, bundle
ScheduleImport/        (app + share extension) ScheduleModels (WorkdayKind, ScheduleCalendar), ScheduleTextReader
                       (Vision/PDFKit), DocumentSafety, RuleBasedScheduleParser, ScheduleExtractor (Foundation
                       Models), ScheduleAPI, ScheduleImportModel, ScheduleImportView
ClearPathShare/        ShareViewController (hosts ScheduleImportView, loads PDF > image > text attachments)
ScheduleImportEvals/   macOS eval + sample generator (not an Xcode target): run.sh, main.swift, cases.json
```

## Siri / App Intents

| Intent | Phrases (`AIShuttleShortcuts.swift`) | Behaviour |
|---|---|---|
| `BookMyUsualShuttleIntent` (optional `day: BookingDay`) | "Book my usual shuttle (for {day}) with Clear Path", "Book my shuttle for {day} with…", "Clear Path book my…" | structured `POST /bookings`; dialog + interactive snippet (Earlier/Later buttons → `RescheduleBookingIntent`) |
| `WhereIsMyShuttleIntent` | **"Track my shuttle with Clear Path"**, "Clear Path, where's my shuttle", … | speaks status, starts Live Activity |
| `AskClearPathIntent` (`request: String`) | "Ask Clear Path", "Talk to Clear Path" | Siri prompts for the request → agent; shares chat conversation |

Lessons (iOS 27 Siri routes with its own model):
- A failed match is answered by Siri itself ("Clear Path doesn't support
  that…", "couldn't find in your messages") — the intent never ran.
- Two intents with overlapping phrases made Siri pick the wrong one, so
  booking is one intent with an *optional* day (no default; nil = tomorrow,
  always spoken back).
- Spoken "Where's my shuttle with Clear Path" was intercepted; "Track my
  shuttle…" and app-name-first phrasings work. Typed requests always work.
- Chained requests (tomorrow then Friday) can lose the day; demo one Siri
  booking per step. Fallbacks: personal Shortcut name, Type to Siri.
- Avoid "ride" (Siri's ride-booking domain).

## Widgets, controls, Live Activity

- `NextRideWidget` (small, medium, accessoryRectangular/Inline): next ride
  and a **Book tomorrow** button (`BookTomorrowIntent`, runs in the
  extension, confirms via local notification). Timeline refresh 15 min;
  every booking path calls `WidgetCenter.reloadAllTimelines()`.
- `BookShuttleControl` (Control Center / Lock Screen / Action button).
- `ShuttleLiveActivity`: Lock Screen + Dynamic Island; countdown
  (`Text(timerInterval:)`) to pickup then arrival, self-advancing progress
  bar from `windowStart…arrivalETA`, orange delay badge. Updated by the app
  (no push).
- Debugging the widget scheme directly needs `_XCWidgetKind` /
  `_XCWidgetFamily` env vars; normally run the AIShuttle scheme and add the
  widget by hand.

## Learned habits (F10)

- **Donations**: after every rides load, `HabitDonations` donates
  `BookMyUsualShuttleIntent(day: <weekday>)` via `IntentDonationManager`
  for each booking not donated before (ids kept in UserDefaults). The rides
  list is the one place that sees bookings from every surface (widget
  extension, chat, schedule import, Claude Desktop), so iOS can surface
  "Book My Usual Shuttle" in Siri Suggestions / Spotlight / Lock Screen.
  Siri runs donate themselves.
- **Reminders**: `HabitReminders.schedule` replaces pending
  `habit-reminder-<date>` notifications with one at 19:00 the evening
  before each upcoming day that is `regular` and not booked: "Book
  Monday's shuttle? Your usual Monday shuttle is the 7:15 AM, arriving
  8:00 AM — you took it on 4 of your last 5 Mondays." **Book** (category
  `HABIT_BOOK_REMINDER`) books in the background via `NotificationResponder`
  and confirms with a notification. Booking that day from Siri, the widget
  or the card withdraws its reminder. Debug builds: card menu → **Preview
  reminder** fires it in 5 s.
- **Home → Your commute** (`HabitCard`): next usual day not booked, why,
  **Book**; "Your usual week" (sparkles = learned, pin = pinned); menu
  pins the shown shuttle or unpins.
- Siri/widget confirmations append the backend's `usual_reason`.

## Trip mode (F4/F5) — replaces push

`TripMonitor.shared.start()` (must be called in the foreground, from the
tracking screen): `CLServiceSession(.whenInUse)` +
`CLBackgroundActivitySession` + `CLLocationUpdate.liveUpdates(.otherNavigation)`
keep the app running; every 15s it posts location (when moved > 50 m or
2 min), fetches `/tracking/next`, updates the Live Activity, and posts local
notifications: "Time to leave" (once, when `leave_in_minutes ≤ 0`) and
"Shuttle delayed" (when delay ≥ 5 and grew by ≥ 5) with **Rebook / Keep**
actions. Rebook → `TripMonitor.switchToAlternative` → `POST /bookings/{id}/move`.
Stops on arrival. `NotificationResponder` uses completion-handler delegate
methods completed on the main actor (async variants crashed SwiftUI).

## Schedule import (F3)

Entry points: **share sheet** (Photos, Files, Mail, Notes… → Clear Path;
activation rule: one PDF, image or plain text) and Home → **Import work
schedule** (photo picker or file importer). Both show `ScheduleImportView`:

1. `ScheduleTextReader`: images downscaled to 2400 px (extension memory
   limit) → Vision `RecognizeTextRequest` (accurate) → cells regrouped into
   rows by vertical position ("Mon 9 Nov | Office"); PDFs use the text layer,
   or render ≤3 pages and OCR them; text as is. Capped at 3000 characters.
2. `ScheduleExtractor`: `DocumentSafety` removes instruction-like lines →
   Foundation Models (`@Generable GeneratedSchedule`, greedy) or, when
   Apple Intelligence is unavailable or fails, `RuleBasedScheduleParser` →
   validation (today…+28 days, weekday cross-check, duplicates, past days
   counted and skipped). See AI.md.
3. `POST /schedule/plan` → review list: per-day kind chip, planned action,
   toggles for book/cancel rows, ignored lines warning, "text read from your
   document" disclosure, method label (Apple Intelligence or text rules +
   reason).
4. **Apply** → `POST /schedule/apply` with only the approved days → result
   rows ✓/✗; reloads widget timelines; the app also reloads rides.

The share extension does everything inside the sheet (no App Group, no
opening the app); it reads `BookingAPIBaseURL` from its own Info.plist.

## Chat and voice

Action labels include the F7 planner tools: `plan_trip` → "Planned your
trip", `book_trip_plan` → "Booked your trip plan".

`AssistantView` (sheet from Home "Ask Clear Path"): suggestions, replies
with action rows (✓/✗, labels incl. "· via weather MCP server") and cited
sources, new-conversation button. `VoiceInput` uses iOS 26 `SpeechAnalyzer`
+ `SpeechTranscriber` on-device with contextual strings ("Clear Path",
"shuttle"); tap mic to talk, tap again to stop and send. Shares the
conversation with Siri "Ask Clear Path" (30-minute expiry).

## On-device routing (F14, `Assistant/OnDeviceAssistant.swift`)

The chat and Siri "Ask Clear Path" first try `OnDeviceAssistant.answer`;
nil means "send it to the cloud agent" (`/assistant/messages`), exactly
as before.
- **Gate** (`OnDeviceGate.screen`, rules): ≤100 chars / 14 words, no
  digits, none of the cloud words (why/how/can/should, weather, leave,
  plan, meeting, by/before/after, latest/earliest, it/that/this, and/also/
  then/too, next/week, minutes, policy, negations), at most one named day
  (today, tomorrow, Monday…Sunday → `BookingDay`, "Friday" on a Friday =
  next Friday, like Siri), exactly one action keyword: book / earlier /
  later / cancel / booked|bookings|rides|upcoming. Changing a booking
  needs a day ("make it earlier" depends on the conversation → cloud).
- **Model** (`FoundationModelsClassifier`): `SystemLanguageModel.default`,
  fresh `LanguageModelSession` per message, greedy, `@Generable
  GeneratedChatRequest {kind, day}`; 3s deadline; prewarmed when the chat
  opens. Unavailable (Apple Intelligence off / not ready / unsupported
  locale) → `OnDeviceAssistant.live()` is nil → cloud for everything.
- **Verify** (`OnDeviceGate.verify`): the model's kind and day must equal
  what the gate read from the words; any mismatch, error or timeout →
  cloud. So the model can only *decline*, never pick a different action.
- **Perform**: structured endpoints only — `POST /bookings
  {booking_date}` (reply = `spokenConfirmation`, with the habit reason),
  `GET /bookings` + `POST /bookings/{id}/reschedule` or `/cancel`,
  `GET /bookings` for listing. A booking-rule refusal (409) is the answer;
  a network error → cloud path.
- **Record**: `POST /assistant/on-device-turns` adds the turn to the shared
  conversation (best effort), so the chat history, Siri, and a later cloud
  follow-up all see it. Withdraws that day's habit reminder after a
  booking.
- UI: on-device replies show "On device · Apple Intelligence" (also after
  reloading the conversation: `on_device` in the replay).

Keyboard prewarm (`Views/KeyboardPrewarmer.swift`): Home's `.task`
focuses and unfocuses an off-screen `UITextField` once per launch, 0.5s
after the rides load, so iOS loads the keyboard system before the chat
opens (the first chat tap used to stall, for seconds under the debugger).
Skipped if something already has focus.

## Tests (76 Swift Testing tests)

All suites that use `MockURLProtocol.requestHandler` (a process-wide static)
are nested under `@Suite(.serialized) struct MockedNetworkTests` — suites
run in parallel otherwise and steal each other's mock responses.

## Building and testing

- Xcode: scheme **AIShuttle** → ⌘R / ⌘U. If it stalls on "Discovering
  version info for clang": `pkill -f "clang -v -E -dM"`.
- Command line (agent): run `xcodebuild … test -scheme AIShuttle
  -destination 'platform=iOS Simulator,id=<iPhone 17 Pro sim>'
  -only-testing:AIShuttleTests -parallel-testing-enabled NO` from a script
  that kills any `clang -v -E -dM` process seen twice 4s apart; takes
  ~90s.
- Schedule extraction eval (macOS, same sources):
  `AIShuttle/ScheduleImportEvals/run.sh [--rules-only] [--cases a,b]`;
  `run.sh extract FILE` reads any PNG/JPEG/PDF/text; `run.sh sample --out DIR
  [--injection]` draws next week's demo schedule.
- Quick check without the build system: `xcrun swiftc -typecheck` of
  `AIShuttle/**/*.swift + Shared/*.swift + ScheduleImport/*.swift` (and `ClearPathWidgets/*.swift +
  Shared/*.swift` with `-application-extension`) with `-sdk
  iphonesimulator -target arm64-apple-ios26.4-simulator -swift-version 5
  -default-isolation MainActor` and the upcoming features
  MemberImportVisibility, InferSendableFromCaptures,
  NonisolatedNonsendingByDefault, InferIsolatedConformances,
  GlobalActorIsolatedTypesUsability.
