# Demo script: Hey Siri, Welcome to the Agentic Era

Engineering Proactive Mobile Experiences with Agentic AI and Native iOS.
Internal technical knowledge-sharing session at BUsoft Tech, Tuesday
17 November 2026, for developers, QA engineers, BAs and managers.

This script is the source of truth for the deck redesign. Each slide has:

- **Badge**: where the work in that step ran (definitions below).
- **DO**: what I demonstrate on the iPhone or the Mac, with exact phrases and expected responses.
- **SAY**: what I explain, in my own words.
- **IF IT FAILS**: how to recover, and what to say.
- **NEXT**: a bridge to the following slide, where one is useful.
- **Time**: estimated speaking time; **[60-MIN CUT]** marks what to shorten or skip if the session must fit into 60 minutes.
- **Deck**: which current slide it reuses (for the redesign).

Story pattern for every capability: **user experience → what happened →
how it works → engineering decision → next experience.**

## The three badges

Used on every "under the hood" slide, always with these exact names:

- **No AI**: deterministic code only. Swift on the phone, Python services
  and Postgres on the Mac. Same input, same output, every time.
- **On-device AI**: Apple's models running on the iPhone: Foundation Models
  (the on-device language model), Vision text recognition, and speech
  recognition. Nothing goes to a cloud model.
- **Cloud AI**: Gemini, called by the LangGraph agent on my Mac. On slide 26
  the cloud AI is Claude Desktop, an external client; Clear Path's own side
  of that step is No AI.

Siri's own request routing is Apple's and not part of Clear Path. When a
slide says No AI, it means my app ran no model for that step.

(The current deck labels the middle badge "On device"; rename it to
"On-device AI" in the redesign.)

## Demo data and booking state

Setup and prep commands are in [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md). This
script assumes a Tuesday demo after `python -m scripts.reset_demo_db`, run in
the same week as the demo (the ride history is placed relative to the
current week), and **next Tuesday booked beforehand** (the schedule import
cancels it).

Learned usuals after the reset (from `app/db/ride_history.py` and
`HabitService`):

| Day | Usual | Reason the app gives |
|---|---|---|
| Monday | 7:15 | you took it on 4 of your last 5 Mondays |
| Tuesday | 7:30 | you took it on each of your last 5 Tuesdays |
| Wednesday | 7:30 | you took it on 6 of your last 10 rides (only one past Wednesday ride, so the overall pattern is used) |
| Thursday | 8:00 | you took it on 4 of your last 5 Thursdays |
| Friday | 7:30 | you took it on each of your last 5 Fridays |

| Step | Change |
|---|---|
| Slide 1 | Tomorrow (Wed) 7:30 booked by Siri; Earlier → 7:15, Later → back to 7:30 |
| Slide 10 | Next Monday 7:15 booked by Siri |
| Slide 11 | Pin the 8:00, then unpin: no bookings change (see note on slide 11) |
| Slide 12 | Control Center / Action button: tomorrow already booked, nothing changes |
| Slide 13 | This Thursday 8:00 booked from the reminder |
| Slide 14 | Import: next Mon keep, next Tue cancelled, next Wed booked |
| Slide 15 | `demo_trip` replays tomorrow's 7:30 as "now" (the trip clock starts) |
| Slide 18 | Delay → tomorrow moved 7:30 → 7:45; the simulation follows the 7:45 |
| Slide 19 | "Should I leave now?" answered for the 7:45 |
| Slide 23 | Next Monday moved 7:15 → 7:00 on device |
| Slide 25 | Tomorrow moved 7:45 → 7:15 (goal); Friday "by 7:30" books nothing |
| Slide 26 | Friday 7:30 booked from Claude Desktop |
| Slide 29 | Friday cancelled on device during the outage, then booked again by Siri |

## The trip clock (slides 15–19)

`demo_trip` (defaults: start 11 simulated minutes before the 7:30 departs,
2× speed, 4-minute walk) runs one continuous clock. Let **r** = real
minutes since `demo_trip` started. Calculated from the code
(`scripts/demo_trip.py`, `tracking_service.py`, `trip_planner.py`); confirm
every value in rehearsal:

| r (real minutes) | What happens |
|---|---|
| 0 | Start the command, then open Where's my shuttle and tap Start trip mode straight away |
| ~1 | "Time to leave" notification (pickup minus 4-minute walk minus 5-minute buffer) |
| 1–6 | Siri "Track my shuttle"; the Live Activity counts down |
| **before 8.5** | **Run `--delay 20`.** The 7:45 is only offered while it's still catchable (more than walk + 5 minutes before it departs). Aim for r ≈ 5–6 |
| after the delay | Within ~15 seconds (trip mode polls every 15 s) the delay notification arrives → Rebook. The simulation now follows the 7:45 |
| r < 8.5 | "Should I leave now?" → **No**, leave in about (17 − 2r) minutes, e.g. r = 6 → about 5 minutes; r = 7 → about 3 minutes |
| 8.5 ≤ r < 13 | "Should I leave now?" → **Yes** |
| ~13 | The 7:45 reaches the stop in the simulation; after that the question no longer makes sense |

Recommended rhythm: delay at r ≈ 5, Rebook at r ≈ 5.5, ask Siri at r ≈ 6–7;
the calculated answer is "No, leave in about 3–5 minutes" (not yet
observed; record the real answer in rehearsal). Both "No" and "Yes" are
correct answers; the script covers either.

## Time budget

Estimated full run: about 75 minutes plus questions. Section totals:

| Section | Slides | Full | 60-minute version |
|---|---|---|---|
| Opening | 1–4 | 6 | 5 |
| Understanding User Intent | 5–8 | 6 | 4 |
| Learning User Habits | 9–11 | 4.5 | 3.5 |
| One Backend, Multiple Entry Points | 12 | 2 | 1 |
| Proactive Mobile Experiences | 13 | 2 | 2 |
| Handling Schedule Changes | 14 | 3 | 3 |
| Real-Time Assistance | 15–18 | 8 | 6 |
| When AI Needs to Think | 19–25 | 13 | 11 |
| Connecting External AI Systems | 26 | 3 | 2.5 |
| Engineering for Failure | 27–31 | 7.5 | 6.5 |
| Testing AI Behaviour | 32–36 | 6 | 5 |
| Platform Limitations | 37–38 | 3 | 1.5 |
| Architecture Overview | 39–41 | 3 | 2 |
| From Prototype to Production | 42–51 | 9 | 5.5 |
| **Total** | | **~75** | **~58** |

---

# Opening

## 1. Hey Siri, Welcome to the Agentic Era

Deck: `cover` · Badge: No AI · Time: 2 min

DO (before any slide; phone on the Lock Screen, mirrored over the cable):
“Hey Siri, book my usual shuttle with Clear Path.”
Expected: “Done. You’re on the 7:30 AM shuttle tomorrow, arriving at Office
by 8:15 AM. That’s your usual: you took it on 6 of your last 10 rides.”
plus a card with Earlier and Later.
Tap **Earlier** (moves to the 7:15), then **Later** (back to the 7:30; the
delay demo later needs the 7:30).
Then show the title slide.

SAY: “Good morning, everyone. I just booked tomorrow’s shuttle with one
sentence to Siri, and moved it with two taps, without opening an app.
That’s the whole idea of this session: an app you mostly use without
opening it.

Over the next hour I’ll walk you through Clear Path, a shuttle app I built.
Every step is live, on my iPhone and my laptop, on this Wi-Fi. After each
thing you see, I’ll explain what happened, how it works, and why I built it
that way.”

IF IT FAILS (Siri answers itself or says the app can’t do that): “And
that’s our first live failure. Siri on iOS 27 decides for itself which app
should handle a request; I’ll come back to exactly why later.” Use Type to
Siri with the same phrase and continue.

NEXT: “Before I explain what just happened, thirty seconds on who I am.”

## 2. Bridging mobile development and AI

Deck: `who` (keep the card as edited: “Making technologies work together”,
columns iOS and AI) · Time: 1.5 min

SAY: “I’m a mobile app developer. I’ve been learning AI engineering, and
the way I chose to learn it was to build one real app end to end.

The left column is what I brought: SwiftUI and Swift concurrency, App
Intents for Siri and Shortcuts, widgets, controls and Live Activities,
notifications, location and maps, share extensions.

The right column is what I had to learn: agents that call tools, built with
LangGraph; RAG, which is searching your own documents, using pgvector; MCP
in both directions; Apple’s on-device Foundation Models; and evaluation and
tracing with Langfuse.

Neither column was the hard part on its own. Making them work together was.
I’m still learning, and I’ll show you where I hit limits.”

NEXT: “So what kind of app did I want to build?”

## 3. Not a chat box inside an app

Deck: `idea` · Time: 1.5 min

SAY: “Most AI apps today are a chat box bolted onto an existing app. You
open the app, find the chat, and type.

I wanted the opposite. The intelligence should show up in the places iOS
users already are: Siri, widgets, Control Center, the Action button, Live
Activities on the Lock Screen, notifications and the share sheet. There is
a chat, but it’s for the moments when a conversation genuinely helps, like
asking why something isn’t allowed.

Clear Path is a commuter shuttle app with one rider, me, going from Home to
the Office. Simple domain on purpose, so we can focus on the engineering.”

NEXT: “One ground rule before we look under the hood.”

## 4. Live demo, live failures

Deck: `ground` · Time: 1 min

SAY: “Everything today is live: Siri, Apple’s on-device model, a free-tier
cloud model, and my laptop on this Wi-Fi. Siri and AI are not 100% reliable
yet. If something fails, I’ll explain how and why, and later I’ll break
things on purpose to show how the app handles it. Keep a rough count of
what fails today; we’ll use that number near the end.

After each experience you’ll see one of three badges. No AI means plain
code: same input, same output, every time. On-device AI means Apple’s
models running on the iPhone. Cloud AI means a language model in the
cloud, called by my backend. Keep an eye on how often it says No AI.”

NEXT: “So, back to that first Siri request. What actually happened?”

---

# Understanding User Intent

## 5. What just happened?

Deck: new slide (a list of the questions below) · Time: 0.5 min ·
[60-MIN CUT: say the questions while showing slide 6]

SAY: “When I said ‘book my usual shuttle with Clear Path’, a few questions
had to be answered:

- How did Siri even know my app exists, and what it can do?
- How did it understand the request?
- How did it know which date to book?
- What does ‘my usual shuttle’ mean, and where does that come from?
- And did any of this need an LLM?

Let’s answer them in order.”

NEXT: “First: how Siri knows about my app.”

## 6. How Siri knows what my app can do

Deck: `siri-card`, with content from `siri-habit` · Badge: No AI · Time: 2.5 min

SAY: “Siri knows about my app through App Intents. An App Intent is a
Swift type that describes one action the app can perform, with typed
parameters. My booking intent has one optional parameter: the day.

The app also declares App Shortcuts: nine booking phrases such as ‘Book my
usual shuttle with Clear Path’ and ‘Book my usual shuttle for {day} with
Clear Path’. iOS registers them when the app is installed, so the user
doesn’t set anything up, and the same actions appear in the Shortcuts app.
The app also registers alternative names Siri should accept for it; more
on why later.

The day is an enum: today, tomorrow, or a weekday. That’s how Siri fills
in ‘Monday’ when I say it. I didn’t say a day, so the intent uses tomorrow,
and the reply always says the day back so I can check it.

When Siri matches the phrase, iOS runs the intent’s code without bringing
the app to the screen. That code sends a booking request with the date to
my backend, then refreshes the widgets.

The card you saw is a snippet: an interactive view inside Siri. Its Earlier
and Later buttons are App Intents too. They call a reschedule endpoint and
the backend moves me to the nearest shuttle I can still book; if there
isn’t one, that button is disabled.

Did this need an LLM? No. The request was already structured: an action
plus a date. Nothing to interpret, so no model was called: No AI. That’s my
first design rule: structured requests skip the AI. Faster, free, and it
can’t hallucinate.”

IF IT FAILS: “Siri matching is a hint, not a guarantee. Two similar intents
confused it in testing, which is why there’s one booking intent with an
optional day.”

NEXT: “So the intent produced a date. Where does it send it?”

## 7. From the phone to the backend

Deck: `runs` · Badge: No AI (this booking request; the slide also shows
where On-device AI and Cloud AI run) · Time: 1.5 min · [60-MIN CUT: first
and last paragraph only]

SAY: “The intent sends a plain HTTP request over this Wi-Fi to my Mac:
‘book user 1 on this date’.

On the Mac runs a Python backend built with FastAPI. Behind it, PostgreSQL
runs in Docker, with the pgvector extension we’ll need later. Six more
Docker containers run Langfuse, a tracing tool, self-hosted.

The iPhone app is really three parts: the app, a widget extension for the
widgets, the Control Center button and the Live Activity, and a share
extension for importing documents. The phone also runs Apple’s on-device
models: the Foundation Model, Vision and speech recognition.

The only cloud services are Gemini Flash-Lite on the free tier and a free
weather API. Total spend so far: nothing. No paid APIs, no hosting, no paid
Apple developer account. Remember that last one.”

NEXT: “The backend received a date. What decides whether I get a seat?”

## 8. One booking service for every surface

Deck: `rider` (timetable and rules), plus rules 1 and 2 from `rules` ·
Badge: No AI · Time: 1.5 min

SAY: “Every booking, whatever it comes from, goes through one service in
the backend, BookingService.

There are five morning shuttles, every fifteen minutes from 7:00, each a
45-minute ride with ten seats. The service checks five rules in order: no
past dates, no weekends, at most 14 days ahead, booking closes 30 minutes
before departure, and no full shuttles. A refusal comes back as a plain
sentence such as ‘Shuttles don’t run on Saturdays.’

If you ask for a day you’ve already booked, it isn’t an error: you get the
booking you already have.

Two more design rules come from here. Facts stay deterministic: bookings,
times and seats come from the database, never from a model. And the rules
live in one place, so Siri, widgets, the chat, and even another company’s
AI later on, all get exactly the same answer.

For this demo the database also holds six weeks of my past rides. That’s
where the answer to the next question comes from.”

NEXT: “Which brings us to the last question: what does ‘my usual shuttle’
actually mean?”

---

# Learning User Habits

## 9. What does “my usual” mean?

Deck: `habit` · Badge: No AI · Time: 2 min

DO: Open the app → Home → **Your commute** card.
Expected: “Thu isn’t booked yet”, “8:00 AM → arrives 8:45 AM”, “You took it
on 4 of your last 5 Thursdays”, and a **Book Thursday 8:00 AM** button (don’t
tap it; the reminder books Thursday on slide 13). Expand **Your usual
week**: sparkles = learned, pin = pinned, circle = default.

SAY: “This card is the app’s idea of my usual commute. Thursday isn’t
booked yet; my usual Thursday shuttle is the 8:00, and here’s why: I took
it on four of my last five Thursdays. It doesn’t just recommend, it
explains. And tomorrow’s 7:30 from the opening? Wednesday has only one past
ride, so the app used my overall pattern instead: 6 of my last 10 rides
were the 7:30. That’s what Siri said.

How it works: the SwiftUI card calls one endpoint, GET /habits. On the
backend, HabitService looks at my past rides in Postgres and decides the
usual for each weekday, in order: a shuttle I pinned wins; otherwise the
one I took most in my last five rides on that weekday; otherwise my last
ten rides overall; otherwise the saved default. A habit needs at least
three rides and more than half of the sample, and only the last eight
weeks count.

Badge: No AI. This is counting. I could have asked a model to ‘guess my
usual’, but counting is cheaper, faster, repeatable, and above all it can
always say why.”

IF IT FAILS: “When there’s no clear pattern, it falls back to the saved
default and gives no reason, rather than making one up.”

NEXT: “That explanation isn’t only on this card.”

## 10. The explanation travels with the booking

Deck: `siri-habit` · Badge: No AI · Time: 1.5 min

DO: “Hey Siri, book my usual shuttle for Monday with Clear Path.”
Expected: “Done. You’re on the 7:15 AM shuttle on Monday, arriving at
Office by 8:00 AM. That’s your usual: you took it on 4 of your last 5
Mondays.” (the 7:15, not the saved 7:30).

SAY: “Same intent as before, this time with a day. Siri filled in ‘Monday’
using the day enum, and the backend asked HabitService for Monday’s usual:
the 7:15, because that’s what I actually take on Mondays. The reason comes
back with the booking, so Siri can say it.

The app also donates my bookings to iOS. Whenever it loads my rides, any
booking it hasn’t donated yet, from any surface, is donated as a ‘Book my
usual shuttle’ intent for that weekday. That’s what lets iOS start
suggesting it in Siri Suggestions and Spotlight over time.”

IF IT FAILS: Retry once; then Type to Siri. “Another one for the count.”

NEXT: “Learning is useful, but a learned habit can be wrong. So I have to
be able to overrule it.”

## 11. You stay in control

Deck: `habit` (pin part); new slide in the redesign · Badge: No AI ·
Time: 1 min · [60-MIN CUT: show the pin and unpin without the second
paragraph]

DO: Card menu → **Always use the 8:00 AM** → a pin appears in “Your usual
week”. Then card menu → **Learn from my rides again** → back to learned.
(Unpin before moving on: while pinned, every weekday’s usual is the 8:00.)

SAY: “If I start a new routine, I don’t want to wait weeks for the app to
notice. ‘Always use the 8:00’ pins it; a pin beats anything learned. ‘Learn
from my rides again’ hands control back.

That’s a principle I followed everywhere: learned behaviour must be
visible, explainable and overridable. The pin is a POST to /habits/pin; it
changes no bookings.”

NOTE: Pinning also makes the 8:00 the saved default, and unpinning doesn’t
restore the 7:30. No later step depends on the default (every demo day has
a learned habit), but don’t claim “the saved 7:30” after this slide.

NEXT: “So the app knows my habits, and I can overrule them. Siri isn’t the
only way to use them.”

---

# One Backend, Multiple Entry Points

## 12. One backend, multiple iOS entry points

Deck: `one-tap` · Badge: No AI · Time: 2 min · [60-MIN CUT: Control Center
press only]

DO: Show the Home Screen widget: tomorrow’s ride, and no **Book tomorrow**
button (tomorrow is already booked). Show the Lock Screen widget. Then
press the Control Center control, or the Action button.
Expected: notification “Already booked”.

SAY: “The widget shows my next ride. Normally it has a ‘Book tomorrow’
button; it’s hidden because tomorrow is booked. The Lock Screen shows the
same.

The Control Center button, which I’ve also placed on the Action button,
runs the same kind of intent. Press: ‘Already booked’. That’s the server’s
duplicate check answering, so pressing twice can never double-book.

Under the hood: the widgets use WidgetKit, in four sizes for the Home
Screen and Lock Screen. They refresh on a schedule, and every booking path
in the app reloads them immediately. The button is a Control Widget, which
iOS lets users put in Control Center, on the Lock Screen or on the Action
button. Both run a small intent inside the widget extension that calls the
same API and confirms with a local notification. Same backend, same rules,
No AI.”

IF IT FAILS: “On a Friday or Saturday this control would say ‘Booking
failed: Shuttles don’t run on Saturdays’, because tomorrow is a weekend.
That’s why this demo is on a Tuesday.”

NEXT: “All of these still wait for me to act. The next step is for the app
to act before I ask.”

---

# Proactive Mobile Experiences

## 13. A reminder that suggests, never books

Deck: `reminder` · Badge: No AI · Time: 2 min

DO: Card menu → **Preview reminder** (Debug build only; fires in 5 seconds)
→ lock the phone.
Expected: “Book Thursday’s shuttle?” / “Your usual Thursday shuttle is the
8:00 AM, arriving 8:45 AM — you took it on 4 of your last 5 Thursdays. You
haven’t booked it yet.” Long-press → **Book** → “Shuttle booked”.

SAY: “In normal use this arrives at 7 PM the evening before any usual day I
haven’t booked. I triggered it early. The text is the same habit and the
same reason we just saw. Long-press, Book, done, and the app never opened.

How it knows when: after the app loads my habits and bookings, it schedules
a local notification for each usual day that isn’t booked. If I book that
day from Siri, the widget, the card or the on-device chat, the reminder is
withdrawn.

How it books without opening the app: the notification has an action, and
iOS runs that action in the background. It calls the same booking endpoint
with the same rules.

Why it only suggests: it would be easy to auto-book my usual days. But a
wrong automatic booking costs the user more than a tap saves. Proactive,
not presumptuous.”

IF IT FAILS: If it doesn’t appear, check notifications are on for Clear
Path, say so, and move on. If the booking is refused: “You’d get a
‘Couldn’t book’ notification with the reason.”

NEXT: “Habits handle the normal week. But my weeks aren’t always normal.
What happens when my schedule changes?”

---

# Handling Schedule Changes

## 14. When the week doesn’t follow the routine

Deck: `import` · Badge: On-device AI · Time: 3 min

DO: Photos → next week’s schedule image → Share → **Clear Path**.
Expected review: Monday office **keep** (booked by Siri on slide 10),
Tuesday WFH **cancel** (the booking made before the demo), Wednesday office
**book**, Thursday offsite and Friday leave **nothing needed**. Switch one
row off and on. Point at “Read on this iPhone with Apple Intelligence” and
“Text read from your document”. Tap **Apply 2 Changes**.

SAY: “Next week I’m working from home on Tuesday, offsite on Thursday and
on leave Friday. The schedule came as an image, so I share it to Clear
Path. It proposes: keep Monday, cancel Tuesday, book Wednesday, nothing for
Thursday and Friday. Every change has a switch, and nothing happens until I
tap Apply.

How it works, all inside the share sheet, on the phone. Vision reads the
text from the image. A safety step removes any line that looks like an
instruction to an AI; I’ll attack that later. Then Apple’s on-device
Foundation Model turns the text into days, using guided generation: the
model is only allowed to output a list of weekday, date and kind. It can’t
write free text and it has no tools. Code then checks every day: real
dates, the weekday matches the date, no duplicates, nothing in the past or
more than four weeks out.

Only those typed days go to the server, which plans them with the same
booking rules; an office day on a weekend, for example, comes back as
blocked. The document itself never leaves the phone: private, free, and no
cloud model involved. That’s On-device AI.

It also accepts PDFs and text files, from Home → Import work schedule.

So the app now handles both sides: the routine it learned, and the changes
I tell it about.”

IF IT FAILS: “If Apple Intelligence is off, still downloading, or the
model fails, keyword rules take over and the screen says ‘Read on this
iPhone with text rules’ and why.”

NEXT: “The week is planned. Now it’s the morning of the commute.”

---

# Real-Time Assistance

## 15. Where’s my shuttle?

Deck: `trip` (map part); new slide in the redesign · Badge: No AI ·
Time: 1.5 min · [60-MIN CUT: merge into slide 16]

DO: Terminal (backend/): `python -m scripts.demo_trip`. **The trip clock
starts now (see “The trip clock” above): the delay on slide 18 must be
triggered before r = 8.5, ideally at r ≈ 5.** Phone: **Where’s my shuttle**
→ map with the route, the bus, the “Simulated” tag and the walking advice.
Move straight on to slide 16.

SAY: “On a commute morning the first question is: where is my shuttle? This
screen shows the route, the bus and my walk to the stop. There’s no real
shuttle, so I’ve started a simulation: the backend replays tomorrow’s 7:30
as if it’s happening now, at double speed, along an illustrative Bengaluru
route. The screen asks the backend for the trip status every five seconds
and draws it with MapKit. In the simulation my walk is fixed at four
minutes; normally it comes from my phone’s location.”

NEXT: “But I won’t keep this screen open while I get ready.”

## 16. Trip mode and the Live Activity

Deck: `trip` · Badge: No AI · Time: 2 min

DO: Tap **Start trip mode** → lock the phone. Show the Live Activity on the
Lock Screen and in the Dynamic Island (countdown, progress bar).

SAY: “There’s the Live Activity: a countdown to pickup and a progress bar,
on the Lock Screen and in the Dynamic Island.

The usual way to keep a Live Activity updated is push notifications from a
server. Push needs a paid Apple developer account, which I don’t have. So
trip mode keeps the app running with background location sessions. Every
15 seconds it asks the backend for the status and updates the Live
Activity itself. It also sends my location after I move 50 metres, or every
two minutes, so the server can work out my walking time.

That’s a deliberate trade-off for a prototype; push is on the production
list at the end.”

NEXT: “Now the phone knows where the shuttle is and how far I have to
walk. It can tell me when to leave.”

## 17. Time to leave, and asking Siri

Deck: `leave-track` · Badge: No AI · Time: 2 min ·
[60-MIN CUT: skip the Siri tracking demo, keep the lesson]

DO: At r ≈ 1 (calculated; confirm in rehearsal) the notification arrives: “Your shuttle reaches … in N
minutes. It’s about a 4-minute walk to …”. Then (r ≈ 2–4): “Hey Siri, track
my shuttle with Clear Path.” Siri speaks the status.

SAY: “Time to leave. The backend takes the minutes until the shuttle
reaches my stop, subtracts my walk and a five-minute buffer; when that
reaches zero, trip mode posts a time-sensitive notification, once per
trip.

And if I’d rather ask: ‘track my shuttle’. This intent is a Live Activity
intent, a kind of App Intent that can start a Live Activity straight from
Siri. It asks the backend for the status, and Siri reads it.

A lesson from testing: my first phrase was ‘Where’s my shuttle’. On iOS 27
Siri often answered that itself, without calling my app. So the phrase
leads with ‘Track my shuttle’.”

IF IT FAILS (Siri answers itself): “That’s exactly the problem I just
described. One more for the count.” Use Type to Siri, but watch the clock:
don’t let it push the delay past r ≈ 7.

NEXT: “So far the commute is going to plan. Now let’s make it go wrong.”

## 18. A delay, and a better shuttle

Deck: `delay` · Badge: No AI · Time: 2.5 min

DO (at r ≈ 5, **never later than r = 8.5**):
`python -m scripts.demo_trip --delay 20`.
Expected within about 15 seconds (calculated from the 15-second trip-mode
poll; confirm in rehearsal): Lock Screen badge “20 min late”, orange
bar. Notification: “…running 20 minutes late. The 7:45 AM shuttle still
gets you to Office by 8:30 AM, 5 minutes sooner. Rebook?” → long-press →
**Rebook** → “Rebooked”.

SAY: “My shuttle is now 20 minutes late. The Live Activity turns orange, and
a notification offers the 7:45 instead, which gets me there five minutes
sooner. Rebook, from the notification, without opening the app.

How it chose: trip mode noticed the delay grow by five minutes or more. The
backend’s trip planner looked for a shuttle I can still catch, more than my
walk plus five minutes away, that arrives sooner than the delayed one. The
delayed 7:30 now arrives 8:35; the 7:45 arrives 8:30. Rebook moves the
booking, and the live trip follows the new shuttle. Keep just dismisses
the notification.

No AI here either. It’s arithmetic over a timetable, and arithmetic belongs
in code.”

IF IT FAILS (no Rebook button): “No faster shuttle could still be caught,
because I started the delay too late. That’s correct behaviour.” Then say
slide 19’s answer will be about the 7:30 instead.

NEXT: “Everything so far was a predefined action: book, move, track,
rebook. None of it needed reasoning. But what happens when I ask something
that isn’t a predefined action?”

---

# When AI Needs to Think

## 19. A question, not a command

Deck: `ask-siri` · Badge: Cloud AI · Time: 1.5 min

DO (straight after the Rebook, ideally at r ≈ 6–7):
“Hey Siri, ask Clear Path.” Siri: “What would you like Clear Path to do?”
→ “Should I leave now?”
Expected (confirm in rehearsal): before r = 8.5, **“No”** with about
(17 − 2r) minutes until I should leave, e.g. about 3–5 minutes; from
r = 8.5 to about 13, **“Yes”**. The reply may add an umbrella tip if rain
is likely.

SAY: “‘Should I leave now?’ isn’t an action with a parameter. It’s a
question that needs several facts combined: where the new shuttle is, how
long my walk is, and the weather. That’s the first interaction today that
needs cloud-based reasoning. The schedule import already used Apple’s
on-device model, but only to turn text into typed days.

This intent first offers the request to the on-device assistant on the
phone; I’ll show you that one shortly. It only handles simple commands, so
this question goes to the cloud agent on my Mac.”

IF IT FAILS (slow or no answer): “Free-tier Gemini can be slow or
rate-limited. Each attempt gets 8 seconds before the next model is tried;
if all fail, it says honestly that the assistant is unavailable and that
bookings still work.” Count it.

NEXT: “So what is the cloud agent actually doing?”

## 20. How the agent works

Deck: `agent` · Badge: Cloud AI · Time: 2 min

SAY: “The agent is built with LangGraph. My question goes to Gemini along
with a list of tools. The model either answers, or asks to call a tool.
LangGraph runs the tool, which is an ordinary Python function, gives the
result back to the model, and loops, up to 12 steps, until it can answer.
The reply comes back with a record of what was actually done.

There are twelve tools: bookings, shuttle options, booking, moving and
cancelling, shuttle status, eligibility, policy search, trip planning, and
habits. The model brings general language understanding, but every
application fact, my bookings, the timetable, the rules, the trip status,
comes from a tool, never from the model’s own knowledge. That’s design rule
two: tools act, the model only chooses.

The model is Gemini 3.5 Flash-Lite with minimal thinking, then a fresh
retry, then 3.1 Flash-Lite, each with an 8-second deadline. I chose
Flash-Lite by measuring: 3.1 Flash-Lite took 20 to 47 seconds under load,
3.5 Flash-Lite takes one to two. That’s rule four: the cheapest model that
measurably works.”

OPTIONAL (only if asked): there’s also an older natural-language booking
endpoint, where a single Gemini call extracts the booking from a sentence;
the agent replaced it for conversation, and Siri uses the structured path.

NEXT: “Let’s look at the two tools this question used.”

## 21. Calculations in code, data from tools

Deck: `ask-siri` (Backend & AI column), `mcp` (MCP out) · Badge: Cloud AI
(the tools themselves are No AI) · Time: 1.5 min · [60-MIN CUT: one
sentence per tool]

SAY: “First tool: shuttle status. Whether I should leave now is computed in
code and returned as a yes or no. The model only phrases it. Why? An
evaluation caught the model saying ‘Yes, leave now’ with 11 minutes to
spare. Arithmetic belongs in code.

Second tool: weather. That tool comes from a small MCP server I wrote. MCP,
the Model Context Protocol, is a standard way for an AI to discover and
call tools from another program. When the backend starts, it launches the
weather server, lists its tools, and hands them to the agent. The server
calls the free Open-Meteo API with my pickup stop’s coordinates. If it
fails to start, the agent simply works without weather.”

NEXT: “I asked that through Siri. What if I continue in the app?”

## 22. One conversation across Siri and the app

Deck: `memory` · Badge: Cloud AI · Time: 1 min

DO: Open the app → **Ask Clear Path**.
Expected: the Siri question and answer are there, with the action row
“Checked the weather · via weather MCP server”.

SAY: “The question I asked Siri is already here, including what the agent
did: it checked the weather, via my MCP server. Every reply shows its
actions with a tick or a cross, and any sources it used; there are
suggestions to start from, and a button for a new conversation.

Siri and the chat share one conversation. The phone keeps a conversation
id that lasts 30 minutes after the last message. On the backend, LangGraph
saves every conversation in Postgres, keyed by user and conversation, so
one user can never read another’s. That’s what makes follow-ups like ‘make
it earlier’ work. After 30 idle minutes a new conversation starts, by
design.”

NEXT: “Now that I’m in the chat: does every message need the cloud?”

## 23. Not every message needs the cloud

Deck: `on-device` · Badge: On-device AI · Time: 2 min ·
[60-MIN CUT: one command only]

DO: Type “What do I have booked?” → reply labelled **On device · Apple
Intelligence**. Then “Move Monday earlier” → next Monday 7:15 → 7:00, also
on device.

SAY: “Look at the label: that answer never left the phone. ‘Move Monday
earlier’: 7:15 to 7:00, also on the phone.

Simple commands in the chat, and in Siri’s ‘Ask Clear Path’, are handled
by Apple’s on-device model, with three checks. First, a rules gate in plain
code: a short message, no digits, no question words, exactly one action
like book, earlier, later or cancel, and a named day for any change.
Second, the on-device model classifies the message into an action and a
day, within three seconds. Third, the model’s answer must match what the
rules read from the words. Any mismatch, error or timeout, and it goes to
the cloud. The model can decline, but it can never pick a different
action.

Then it calls the same endpoints Siri uses, and saves the turn into the
shared conversation so the cloud agent sees it later. Faster, free,
private, and it still works when the cloud is down. You’ll see that.”

IF IT FAILS (no label): “The on-device model declined or disagreed, so the
cloud answered instead. That’s the safety design working.”

NEXT: “Commands are easy. Explanations need knowledge the app has to look
up.”

## 24. Answers with sources

Deck: `rag` · Badge: On-device AI (speech) + Cloud AI (answer) · Time: 2.5 min

DO: Tap the mic → “Why can’t I book Saturday?” → tap stop.
Expected: the rule plus a cited Booking Policy passage.

SAY: “I asked by voice. Speech-to-text ran on the phone with Apple’s
SpeechAnalyzer, tuned for words like ‘Clear Path’ and ‘shuttle’. That part
is On-device AI.

The answer is Cloud AI. The agent first called an eligibility tool, which
returns the real rule from BookingService. Then it searched our policy
documents. That’s RAG, retrieval-augmented generation. The four policy
documents are split into 16 sections. Each section was turned into an
embedding, 384 numbers that capture its meaning, by a small model running
locally on my Mac, and stored in Postgres with pgvector. My question is
embedded the same way and compared.

Passages below 0.60 similarity are dropped before the model ever sees
them. Only the top passage of a search can become a citation, and only if
it scores 0.70 or more. Between 0.60 and 0.70 a passage is related enough
for the agent to read and use, but not strong enough to be shown as the
source. The prompt allows policy answers only from search results. So the rule comes from code, the explanation comes from our
documents, and the citation shows where.”

IF IT FAILS: “If nothing is close enough there’s no citation, and the agent
says it doesn’t know.” If the mic isn’t available, type the question.

NEXT: “One more kind of request: instead of a time, I give it a goal.”

## 25. Goals instead of times

Deck: `goal` · Badge: Cloud AI (understanding) + No AI (the planner) ·
Time: 2.5 min

DO 1: “I have a meeting at 8 tomorrow, get me there in time.”
Expected: action “Booked your trip plan”: tomorrow 7:45 → **7:15**,
arriving 8:00.
DO 2: “Get me to the office by 7:30 on Friday.”
Expected: “No shuttle gets you there by 7:30 AM. The soonest is the 7:00
AM, arriving 7:45 AM (15 minutes late).” Nothing booked.

SAY: “For the meeting at 8 it moved me from the 7:45 to the 7:15, which
arrives at 8:00. For 7:30 on Friday it says honestly that no shuttle gets
me there, offers the earliest, and books nothing.

Here the model only reads: it turns my sentence into a date and an
arrive-by time. A deterministic trip planner, plain Python over the
timetable and the rules, picks the shuttle: keep my current booking if it
already works, else my usual, else the latest one that still arrives in
time. It’s the same planner that found the 7:45 during the delay. A
statement like ‘get me there’ books; a question like ‘will I make it by
8:20?’ only plans and changes nothing. It handles several days at once too,
like ‘by 8 every day this week’.

This wasn’t my first design. Originally the agent did the time arithmetic
itself, and in evaluation it booked a shuttle for an impossible goal and
claimed it would arrive on time. Goal scenarios passed 4 out of 9. With the
planner: 9 out of 9. Let the model understand; let code decide.”

IF IT FAILS: “When no shuttle meets the goal, it offers the soonest one and
never books it without my OK.”

NEXT: “Everything so far happened in my app. But I also use other AI tools
at work. Can they use Clear Path too?”

---

# Connecting External AI Systems

## 26. Booking from Claude Desktop

Deck: `mcp` · Badge: Cloud AI (external client: Claude Desktop); Clear
Path’s side is No AI · Time: 3 min · [60-MIN CUT: skip the Thursday
question]

DO: Switch to Claude Desktop. “Book my usual shuttle for Friday” → allow
the tool → booked → refresh the iPhone app: Friday is there. “What’s my
usual Thursday?” → 8:00 with its reason. “Book Saturday too” → “Shuttles
don’t run on Saturdays.”

SAY: “Claude Desktop is a different AI, from a different company. It asked
my permission to use a Clear Path tool, booked Friday, and the booking is
already on my phone. It knows my usual Thursday and why. And Saturday is
refused, by my rules, not by Claude.

This is MCP again, in the other direction. Earlier my agent was the client
and the weather server was the tool provider. Here my backend is the
provider: it publishes an MCP server with 13 tools, the same 12 my agent
uses plus one for today’s date. Claude Desktop starts it locally; the same
server can also run over HTTP.

Because those tools call the same services, any AI client is held to
exactly the same business rules. Each tool is labelled read-only or
changing, and cancel is labelled destructive, so a client can ask before
using it.

My app is a tool any AI can use, and my agent can use any tool.”

IF IT FAILS: If Claude Desktop shows no tools, check the clear-path server
in Settings → Developer, then retry; explain it’s a local process started
by Claude Desktop.

NEXT: “That’s everything working as designed. Now let’s see what happens
when things go wrong, on purpose.”

---

# Engineering for Failure

## 27. Designing for failure

Deck: `act5` (retitle, without “Act”) · Time: 0.5 min

SAY: “A feature isn’t finished until you know how it fails. I’ll show two
failures: a document carrying hidden instructions for the AI, and the cloud
AI going completely down. Watch what keeps working.

This is design rule five: be honest when something fails. Never hide a
change, never fake an answer.”

NEXT: “First, the malicious document.”

## 28. A document with hidden instructions

Deck: `injection` · Badge: On-device AI · Time: 2 min

DO: Photos → the **injection** version of the schedule → Share → **Clear
Path**. Expected: orange “Ignored 1 line that looked like instructions to
an AI”, the line shown, “Only the days below were read. Check them before
applying.” Only the real days are proposed. **Close without applying.**

SAY: “This schedule has fine print aimed at an AI, the kind of thing
someone could hide in a document to make an assistant do something you
never asked for. Clear Path ignored it, showed me the line, and proposed
only the real days.

Remember the import pipeline. There are five layers of defence. One: on
the phone, lines that look like instructions are removed before any model
sees the text. Two: the on-device model is told the document is data, and
it has no tools to call. Three: its output can only be typed days. Four:
the server accepts only a date and a kind, nothing else; document text
never reaches Gemini, the agent or any tool. Five: nothing changes until I
tap Apply.

The honest limit: a quiet line like ‘make Wednesday leave’ looks like data,
so layer one can’t catch it. Layers three to five still limit the damage
to a visible change I can review. That’s defence in depth.”

NEXT: “Second failure: the cloud AI disappears.”

## 29. The cloud AI goes down

Deck: `outage` · Badge: Cloud AI (unavailable) + No AI + On-device AI ·
Time: 3 min

DO: Second terminal in backend/: `python -m scripts.llm_outage on` (no
restart). Optional: `curl localhost:8000/health` → `"llm": "outage"`.
Chat: “Why can’t I book Saturday?” → “Clear Path’s assistant is unavailable
right now. Bookings still work: say “Book my usual shuttle with Clear
Path”, or use the widget.”
Same chat: “Cancel Friday” → **On device**, Friday (booked from Claude
Desktop) cancelled.
“Hey Siri, book my usual shuttle for Friday with Clear Path” → booked
again. Optionally press the Control Center button.

SAY: “I’ve just simulated the model provider going down, without
restarting anything. A question that needs the cloud gets an honest
answer: the assistant is unavailable, and here’s what still works. Nothing
is made up.

‘Cancel Friday’ still works: that’s On-device AI. Siri booking still works:
that was always No AI. The widgets and the Control Center button still work
too.

How the switch works: a flag file makes the backend hand out stand-in
models that fail immediately, like an unreachable provider. The real
fallback chain still runs all three attempts and then returns an honest
error. Nothing is faked on the phone. The health endpoint reports the
outage, and the evaluation runner refuses to start while it’s on, so a run
can’t be wasted.

Why most of the app survives: every iOS surface sends structured requests
to deterministic services, and simple chat runs on the phone. The AI is an
enhancement, not a single point of failure.”

NEXT: “When something like that happens in real life, how do I find out
what went wrong?”

## 30. Tracing every turn

Deck: `trace` · Badge: No AI (tracing itself; it records the Cloud AI and
On-device AI turns) · Time: 2 min

DO: Langfuse (http://localhost:3000) → the failed turn: an ERROR trace with
every attempt. Then a normal turn: model calls, tool spans, timings. Then an
on-device turn tagged `on-device`. Then terminal:
`python -m scripts.llm_outage off`, and ask the chat once more to show it’s
back.

SAY: “This is Langfuse, self-hosted in Docker, so nothing leaves my
laptop. Here’s the turn that just failed: marked as an error, with every
fallback attempt and the reason. Here’s a normal turn: each model call and
each tool call, with inputs, outputs and timings. On-device turns are
recorded too, and so is every evaluation run, with its scores.

One more rule that tracing protects: never hide a real change. If the model
fails after a booking has already changed, the reply still says ‘I made
changes to your bookings but couldn’t finish replying. Check your rides to
see the latest.’ The worst thing an assistant can do is change your
booking and then tell you it failed.

I’m switching the cloud back on.”

NEXT (if nothing failed naturally): skip slide 31. “Those were planned
failures. So how do I know the normal behaviour is reliable?”

## 31. If something failed earlier (optional)

Deck: `natural` · Time: 1 min, only if used

USE ONLY IF something failed by itself during the demo.

SAY: “Earlier, [what failed]. Here’s what was going on.” Point at the
matching row:
- Siri answered by itself: iOS 27 Siri routes requests with its own model;
  App Shortcut phrases are a strong hint, not a guarantee.
- Slow or rate-limited Gemini: free-tier limits; 8 seconds per attempt,
  three attempts, then an honest error.
- No On-device label: the on-device model must agree with the rules gate,
  otherwise the cloud answers.
- “I couldn’t reach Clear Path”: the phone and the laptop must share the
  Wi-Fi.
- No Rebook: no faster shuttle could still be caught.

“In every case the failure was visible and honest.”

NEXT: “So how do I know the normal behaviour is reliable?”

---

# Testing AI Behaviour

## 32. How do I know this actually works?

Deck: `act6` (retitle) · Time: 0.5 min

SAY: “Everything you’ve seen worked today. But how do I know it works
tomorrow, after I change a prompt or swap a model?

Testing and evaluation were as much work as the features. With an LLM you
can’t assert an exact sentence. But you can assert which tools it called,
what the bookings look like afterwards, and which sources it cited, and
then have a judge grade the wording. QA folks, this part is for you.”

NEXT: “There are three layers.”

## 33. Three layers of checking

Deck: `tests` · Badge: No AI (backend, Swift and UI tests; the
keyword-rules extraction baseline) + Cloud AI (agent evaluations with real
Gemini and an AI judge) · Time: 1.5 min

SAY: “First, about 150 backend tests that run in seconds. They use a
separate test database, a frozen clock and no network, and the suite
refuses to start unless it’s on the test database. They cover the booking
rules from slide 8, the habits, the trip planner, the MCP server and the
outage switch you just saw.

Second, 76 Swift tests on the iOS side, about 107 cases with their
arguments, plus 2 UI tests: the API client, the on-device routing gate,
schedule import, habits and tracking.

Third, evaluations. 36 scenarios run the real agent with real Gemini on
their own isolated database at a fixed date. There’s also a separate
evaluation for schedule extraction: 15 documents, including photos and
four injection attempts. The keyword-rules fallback gets 11 of 15 exactly
right and handles all four injections safely. The on-device model itself I
couldn’t measure, because Apple Intelligence won’t run on my Mac; I’ve only
verified it by hand on the iPhone.”

NEXT: “Here’s what one of those agent evaluations looks like.”

## 34. How an evaluation works

Deck: `evals-how` · Badge: Cloud AI (the agent under test and the AI
judge) + No AI (the hard checks) · Time: 1.5 min · [60-MIN CUT: skip the
last paragraph]

SAY: “Each scenario has a setup: for example, I already have a booking on
Tuesday, a trip is running, or shuttles are full. Then one or more
messages to the real agent.

Then hard checks, like unit-test assertions: did it call the right tools,
did it avoid the wrong ones (for example, never cancelling unasked), are
the final bookings exactly what we expect, did it cite the right policy.

Only then does an AI judge score the reply from 1 to 5 against a rubric
and the actual tool results; a 2 or less counts as a hallucination.

The scenarios cover what you saw today: goals like ‘meeting at 8’, rules
and policies like ‘why not Saturday’, bookings, tracking, follow-ups,
habits and safety. A check mode fails the run if success drops more than 5
points from the saved baseline, and runs are paced to stay inside the free
tier.”

NEXT: “And this is where the numbers stand.”

## 35. Measured results

Deck: `baseline` · Badge: Cloud AI (measured agent results) · Time: 1 min

SAY: “The saved baseline is a full run of all 36 scenarios on Gemini 3.5
Flash-Lite, from 8 November. 33 of 36 passed, and the right tools were
chosen every time. Average judge score 4.67 out of 5. Median reply 8
seconds; the slowest 5% took about 29 seconds, which is the free tier.
About $0.002 per task at list price; on the free tier, nothing.

I read all three failures. Two were the judge’s mistakes: on a simulated
trip the tool reports timetable times, and the judge compared them with
the evaluation’s own clock and called them wrong. One was real: the model
added a ‘leave by 7:25’ time that no tool gave it. I fixed both prompts,
and the affected tracking scenarios then passed 6 of 6 with a judge score
of 5.”

NOTE: These are the 2026-11-08 baseline (saved before the two prompt
fixes) plus the 6-scenario re-run after them. If a new full baseline is
saved later, replace the numbers.

NEXT: “The numbers matter less than what the evaluations found.”

## 36. What evaluations caught

Deck: `caught` · Badge: Cloud AI (the bugs) → No AI (most fixes moved
the decision into code) · Time: 1.5 min

SAY: “Four real bugs, each found by an evaluation, and each connected to
something you saw today.

The goal booking on slide 25: the agent did time arithmetic itself and
booked impossible trips. Fixed by the trip planner, 4 of 9 to 9 of 9.

The habit reason on slide 10: the agent once said ‘4 of your last 5’ with
no data behind it, because it copied an example from a tool description.
Now it may only use the reason the tool returns.

The policy answers on slide 24: a question about a colleague using my
booking didn’t find the FAQ. I reworded the FAQ and re-indexed it.

‘Should I leave now’ on slide 19: the model said yes with 11 minutes to
spare. Now that’s computed in code.

The latest run added two more lessons: the model invented a leave-by clock
time, so leave timing is now minutes only; and the judge itself misread
simulated times, so its instructions now explain them. That’s why hard
checks come first and I read every failure myself.”

NEXT: “So if this can be engineered, why don’t we see many apps like this
yet?”

---

# Platform Limitations

## 37. Platform limitations I encountered

Deck: `act7` + `limits-siri` · Time: 1.5 min · [60-MIN CUT: merge slides
37 and 38 into one minute: the count, Siri, and “making AI trustworthy is
most of the work”]

SAY: “Let’s start with today’s count. How many things failed live?” (Count
with the room; recap each in one line.)

“Siri is the first reason these apps are rare. On iOS 27 Siri uses its own
model to decide which app should handle a request, so an App Shortcut
phrase is a strong hint, not a guarantee. Sometimes it misses or answers by
itself. I tested phrases, kept one booking intent with an optional day, and
Type to Siri is the fallback.

It misheard my app’s name in a dictation test as ‘Clear Footpath’, so
that’s now literally one of the app’s alternative names. It can drop the
day from a request, so when no day arrives and tomorrow is a weekend, the
app asks ‘Which day should I book?’. And ‘Where’s my shuttle’ was
intercepted, so tracking leads with ‘Track my shuttle’.

None of these are bugs in my code, but a user would blame the app.”

NEXT: “And it isn’t only Siri.”

## 38. Model and platform limits

Deck: `limits-platform` · Time: 1.5 min

SAY: “Apple’s on-device AI isn’t available on every iPhone, so there’s
always a fallback, and the screen says which one ran. Push needs a paid
developer account, hence trip mode. Free-tier limits mean the slowest
replies take up to about 29 seconds, so every call has an 8-second deadline
and a fallback chain.

Once, the model replied with just the name of a tool instead of a
sentence, and Siri read it out loud. Now that kind of reply is rejected and
the next model is tried. The AI judge miscounts sometimes, so hard checks
come first. And a pure UX one: the first tap on the chat box froze for
seconds while iOS loaded the keyboard, so the app warms the keyboard up in
the background on Home.

That’s the honest answer: the AI calls are a small part of this app.
Making them trustworthy is most of the work.”

NEXT: “Let me put everything we’ve seen into one picture.”

---

# Architecture Overview

## 39. One backend, many surfaces

Deck: `arch` · Time: 1.5 min

SAY: “At the top, the iPhone surfaces we used: Siri, widgets, Control
Center, the Action button, the Live Activity, notifications, the share
sheet and the chat. On-device AI does the private work locally: reading the
schedule, routing simple chat, speech.

Two paths into the backend. Structured requests, Siri phrases, buttons,
notification actions and on-device chat, go straight to REST endpoints with
no AI. Open-ended requests go to the LangGraph agent, which uses Gemini to
choose among 12 tools.

Both paths end in the same services: booking, trip planning, habits and
tracking. Underneath, Postgres with pgvector holds the bookings, the
agent’s memory and the policy embeddings.

On the side: MCP in, where Claude Desktop uses the same 13 tools; MCP out,
the weather server; and Langfuse and the evaluations watching every turn.
The rules exist once, and every surface, human or AI, goes through them.”

NEXT: “Here are all the badges from today in one place.”

## 40. Where the AI runs

Deck: `where-ai` · Time: 1 min

SAY: “No AI: Siri booking, widgets and controls, habits, reminders, trip
mode, alerts and rebooking. On-device AI: schedule import, simple chat
commands, and voice input. Cloud AI: only the genuinely open-ended
questions, should I leave now, why can’t I, get me there by 8, and even
there deterministic tools make the decisions.

That’s what ‘AI only where it earns its place’ means in practice, and it’s
exactly why most of the app kept working when I switched the cloud off.”

NEXT: “Those choices came from five rules.”

## 41. The five design rules

Deck: `rules` (moved here as a recap) · Time: 0.5 min ·
[60-MIN CUT: skip]

SAY: “You’ve now seen all five in action. Facts stay deterministic: the
database and code own bookings and times. Tools act, the model only
chooses. Structured requests skip the AI: the very first Siri booking. The
cheapest model that measurably works, chosen with evaluations. And be
honest when something fails: the outage reply and ‘I made changes to your
bookings’.”

NEXT: “What did building this teach me?”

---

# From Prototype to Production

## 42. Lessons learned

Deck: `learned` · Time: 1 min

SAY: “Three lessons. First, the LLM does less than you think. Its best job
is turning language into a structured request; then code should decide.
Second, evaluations find what demos hide; the agent’s worst bugs came from
evaluations, not from clicking around. Third, honest failure is a feature.
Users forgive ‘unavailable’. They don’t forgive a wrong booking.

What carried over from mobile was thinking in surfaces and user moments,
designing failure states, and testing discipline. I’m still learning:
retrieval quality, evaluations in CI and running this at real scale are
next for me.”

NEXT: “Which brings us to: what would it take to make this a real product?”

## 43. Scaling up for the real world

Deck: `prod` (keep the edited title) · Time: 0.5 min

SAY: “This is a prototype, built deliberately for one rider, on a laptop,
with zero spend. Every shortcut was a choice, not an oversight, and I want
to show I know exactly what changes for production.

Four areas: users and security, platform and scale, mobile, and AI quality
and cost. For each: what it is today and why, what production needs, and
how I’d get there.”

NEXT: “Starting with who the user is.”

## 44. Users and security

Deck: `prod-users` · Time: 1 min · [60-MIN CUT: 60 to 90 seconds for
slides 44–47 together, one headline per slide]

SAY: “Today every request says ‘user 1’, on purpose, to keep the demo
about the AI. In production the user comes from a verified token, Sign in
with Apple or the company’s single sign-on, never from the request body,
with a tenant per company for its own routes and rules.

The phone talks plain HTTP to my laptop; production needs HTTPS, an API
gateway with rate limits, and secrets in a secrets manager. The MCP server
runs locally as user 1; for real users it becomes a remote server with
OAuth, per-user permissions and an audit log. And location and commute
habits are personal data: consent, retention limits, deletion on request,
and India’s Digital Personal Data Protection Act.”

NEXT: “Then where it runs.”

## 45. Platform and scale

Deck: `prod-platform` · Time: 1 min

SAY: “The backend runs on my laptop; production means containers on a
managed platform with autoscaling, and separate staging and production.
Tables are created at startup and I have demo reset scripts; production
needs versioned migrations, for example Alembic, backups, and managed
Postgres with pgvector.

The agent’s tools share one database session behind a lock: fine for one
rider. Many users need a session per request, async I/O, a job queue for
slow work, idempotency keys so a retried booking never doubles, and
caching. And the shuttle is simulated; a real fleet means vehicle GPS or a
transit feed, road-snapped routes and a proper arrival-time model.”

NEXT: “On the phone itself.”

## 46. Mobile

Deck: `prod-mobile` · Time: 1 min

SAY: “With a paid developer account, delay and time-to-leave alerts come
from the server through push, and Live Activities are started and updated
by push: far better for battery than keeping the app awake with location.
Trip mode stays as a fallback.

For Siri: more App Intents and App Entities so Siri understands more of the
app, Smart Stack relevance so the widget appears at the right moment, more
Shortcuts actions. On-device AI only runs where Apple Intelligence runs, so
the fallbacks stay, and I’d measure the on-device model on real iPhones,
which I couldn’t do on my Mac. And reach: Indian languages for speech and
search, an accessibility review, and Android on the same backend, which is
straightforward because the rules live on the server.”

NEXT: “And the AI itself.”

## 47. AI quality and cost

Deck: `prod-ai` · Time: 1 min

SAY: “Today: free-tier Flash-Lite with fallbacks inside one provider.
Production: a paid tier with a service-level agreement, fallback across
providers, say Gemini, Claude or OpenAI behind one interface, and every
model choice made by running the same evaluations.

Retrieval: 16 sections is fine for a prototype; a real knowledge base
needs an ingestion pipeline, hybrid keyword and vector search, a reranker,
and evaluations for retrieval itself. Evaluations run by hand today
because I chose no CI; in production they gate every prompt or model
change, run nightly, and real failing conversations from traces become new
scenarios. Plus dashboards and alerts for latency, cost and errors, crash
reporting in the app, and the injection defences applied to all outside
text, with confirmation for actions that change things.”

NEXT: “What would that cost to run?”

## 48. Cost at scale

Deck: `cost` · Time: 0.5 min · [60-MIN CUT: one sentence, or skip]

SAY: “An estimate, not a measurement. The evaluation baseline puts one AI
task at about $0.002 at list price. A thousand riders making four Cloud AI
requests a day comes to about $8 a day. And most of the app never calls the
cloud model: Siri phrases, widgets, notifications, trip mode and on-device
chat cost nothing per request. ‘AI only where it earns its place’ is a cost
decision as much as a reliability one.”

NEXT: “Here’s the order I’d do it in.”

## 49. Roadmap

Deck: `roadmap` · Time: 0.5 min · [60-MIN CUT: skip]

SAY: “Now: teach the on-device path more commands, like ‘book the 7:15 on
Friday’, and re-save the full 36-scenario baseline after the prompt fixes. Next: push
notifications and push-updated Live Activities, Smart Stack relevance, and
evaluations running automatically on every change. Later: sign-in and many
riders, real transit data, fallback across model providers, and proper
evaluations for the on-device model.”

NEXT: “And what this means for the work we do here.”

## 50. What this means for our projects

Deck: `busoft` · Time: 1 min

SAY: “This isn’t really about shuttles. The same four steps apply to the
client apps we build at BUsoft. Expose the app’s real actions as
structured things: App Intents, widgets, notifications. Add AI only where
it earns its place, On-device AI when it can, Cloud AI when it must. Make
evaluations part of QA from day one, hard checks first, then a judge. And
design how each AI feature fails before it ships.

Banking, retail, healthcare, logistics: the domain changes, the pattern
doesn’t. And every role here owns part of it: developers, QA, BAs and
managers.”

## 51. Closing

Deck: `close` · Time: 0.5 min

SAY (slowly, then pause): “The AI isn’t a chat box inside the app. It
works through the parts of iOS people already use. That’s the agentic era,
and it’s still being engineered.”
“Thank you.”

## 52. Questions

Deck: `qa`

SAY: “Happy to take questions, and I can show any part again live.”

Prepared answers:
- Why Gemini? Free tier and measured latency; in production the
  evaluations would decide between providers.
- Why not just a chatbot? Most commute actions are structured; a button or
  a Siri phrase is faster and can’t hallucinate.
- What did it cost? Nothing in money: free-tier Gemini, self-hosted tools,
  no paid accounts.
- Could it work on Android? Yes. The rules live on the backend; the OS
  surfaces would be rebuilt natively.
- How do you stop prompt injection? Five layers (slide 28).
- What if Siri doesn’t understand? Type to Siri, the widget, or the app;
  every surface reaches the same rules.
- How do you test something non-deterministic? Hard checks on tools,
  bookings and sources first, then a judge for wording (slide 34).

---

# Appendix

## A1. AI terms in plain English (backup)

Deck: `glossary` (no longer in the main flow; show only if asked)

SAY (only if needed): LLM: a model that reads and writes text. Agent: an
LLM in a loop that calls tools. Tool: a function the agent may call. RAG:
search your documents, then answer from them with a citation. MCP: a
standard plug for AI tools. On-device model: Apple’s model on the iPhone.
Evaluation: a test suite for AI behaviour. Trace: a recording of every AI
step.

## A2. Coverage checklist

Everything built (PRODUCT.md flows F1–F14 and the supporting work), and
where it appears:

| Built | Slides |
|---|---|
| F1 Siri booking, optional day, Earlier/Later card, “Which day?” | 1, 6, 10, 37 |
| F2 Home and Lock Screen widgets, Control Center, Action button, duplicate protection | 12 |
| F3 Schedule import (share sheet, in-app photo/file/PDF, Vision OCR, Foundation Models, validation, rules fallback, review and Apply) | 14 |
| F3/F13 Prompt-injection defences | 14, 28 |
| F4 Delay alert with Rebook / Keep | 18 |
| F5 Time to leave, “Should I leave now?”, weather | 17, 19, 21 |
| F6 Map, trip mode, Live Activity (Lock Screen, Dynamic Island), Siri tracking | 15, 16, 17 |
| F7 Goal planning (book, question-only, multi-day, honest no) | 25 |
| F8 Rules + RAG with citations | 24 |
| F9 Chat, voice input, Siri “Ask Clear Path”, shared memory, action rows and sources | 19, 22, 23, 24 |
| F10 Learned habits, reasons, pin, Your commute card, reminder with Book, donations to Siri Suggestions / Spotlight | 9, 10, 11, 13 |
| F11 Clear Path MCP server (13 tools, annotations, stdio and HTTP) | 26 |
| E Weather MCP server (agent as MCP client) | 21, 26 |
| F12 Evaluation harness, AI judge, baseline, Langfuse tracing | 30, 33–36 |
| F13 LLM outage switch, honest 503, /health, eval guard | 29 |
| F14 On-device routing (chat and Siri) | 19, 23 |
| Model choice, fallback chain, 8-second deadlines, unusable-reply rejection | 20, 38 |
| Partial-failure honesty | 30 |
| Backend tests (isolated database), Swift and UI tests, schedule extraction eval | 33 |
| Keyboard prewarm, alternative app names | 37, 38 |
| Demo data (ride history), simulator | 8, 15 |
| Legacy natural-language booking endpoint | 20 (optional) |
| Production gaps, cost, roadmap | 43–49 |
