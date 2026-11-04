# Mobile (iOS)

Xcode 26.4.1, iOS SDK 26.4, deployment target 26.4, tested on an iPhone 17
(iPhone18,1) running iOS 27.0.1. Swift 5 language mode with
`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` and approachable concurrency;
Swift Testing for unit tests. Signing: automatic, team `5RXXN24YC5`
(**free account: no push notifications / APNs**). Display name "Clear Path".

## Targets

| Target | Bundle id | Contents |
|---|---|---|
| AIShuttle (app) | `com.yourcompany.AIShuttle` | `AIShuttle/` + `Shared/` |
| ClearPathWidgets (widget extension) | `com.yourcompany.AIShuttle.ClearPathWidgets` | `ClearPathWidgets/` + `Shared/` |
| AIShuttleTests | `com.yourcompany.AIShuttleTests` | `AIShuttleTests/` |

Folders are file-system-synchronized groups (new files are picked up
automatically). Info.plist = generated + `AIShuttle-Info.plist` /
`ClearPathWidgets-Info.plist`:

- `BookingAPIBaseURL = $(BOOKING_API_BASE_URL)` — project build setting,
  currently `http://172.20.1.13:8000` (the Mac's Wi-Fi IP; update when it
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
AIShuttle/ViewModels/  RidesViewModel (joins in-flight loads; survives cancelled .task callers)
Shared/                BookingAPIClient (+ withTimeouts/forAssistant, ISO8601 decoder, NoContent),
                       BookingDTOs, BookingConfirmation (spoken text, BookingIntentError, notifier),
                       BookTomorrowIntent (widget/control), ShuttleActivityAttributes
ClearPathWidgets/      NextRideWidget, BookShuttleControl, ShuttleLiveActivity, bundle
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

## Chat and voice

`AssistantView` (sheet from Home "Ask Clear Path"): suggestions, replies
with action rows (✓/✗, labels incl. "· via weather MCP server") and cited
sources, new-conversation button. `VoiceInput` uses iOS 26 `SpeechAnalyzer`
+ `SpeechTranscriber` on-device with contextual strings ("Clear Path",
"shuttle"); tap mic to talk, tap again to stop and send. Shares the
conversation with Siri "Ask Clear Path" (30-minute expiry).

## Tests (33 Swift Testing tests)

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
- Quick check without the build system: `xcrun swiftc -typecheck` of
  `AIShuttle/**/*.swift + Shared/*.swift` (and `ClearPathWidgets/*.swift +
  Shared/*.swift` with `-application-extension`) with `-sdk
  iphonesimulator -target arm64-apple-ios26.4-simulator -swift-version 5
  -default-isolation MainActor` and the upcoming features
  MemberImportVisibility, InferSendableFromCaptures,
  NonisolatedNonsendingByDefault, InferIsolatedConformances,
  GlobalActorIsolatedTypesUsability.
