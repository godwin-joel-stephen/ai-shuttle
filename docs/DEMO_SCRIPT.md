# Demo script: Hey Siri, Welcome to the Agentic Era

Engineering Proactive Mobile Experiences with Agentic AI and Native iOS.
Internal technical knowledge-sharing session at BUsoft Tech, Thursday
3 December 2026, for developers, QA engineers, BAs and managers.

This script is the source of truth for the talk, and the deck's speaker
notes are the same text. There are 26 slides. Each
slide has:

- **Slide**: the deck slide id, the badge (definitions below) and the
  estimated speaking time.
- **DO**: what I demonstrate on the iPhone or the Mac, with exact phrases
  and expected responses.
- **SAY**: what I explain, in my own words.
- **IF IT FAILS**: how to recover, and what to say.
- **NEXT**: a bridge to the following slide.

Story pattern for every capability: **user experience → what happened →
how it works → engineering decision → next experience.**

How to operate the demo (prep, terminals, state checks, recovery) is in
[DEMO_RUNBOOK.md](DEMO_RUNBOOK.md); its run of show has 24 steps (the AI and iOS terms slides are part of step 2).

## The three badges

Shown on every demo slide, always with these exact names:

- **No AI**: deterministic code only. Swift on the phone, Python services
  and Postgres on the Mac. Same input, same output, every time.
- **On-device AI**: Apple's models running on the iPhone: Foundation Models
  (the on-device language model), Vision text recognition, and speech
  recognition. Nothing goes to a cloud model.
- **Cloud AI**: Gemini, called by the LangGraph agent on my Mac. On slide 16
  the cloud AI is Claude Desktop, an external client; Clear Path's own side
  of that step is No AI.

Siri's own request routing is Apple's and not part of Clear Path. When a
slide says No AI, it means my app ran no model for that step.

## Demo data and booking state

This script assumes a Thursday demo (3 December 2026, so tomorrow is
Friday) after `python -m scripts.reset_demo_db`, run in the same week as
the demo (the ride history is placed relative to the current week), and
**next Tuesday (8 December) booked beforehand** (the schedule import
cancels it). Weekday names said on a Thursday mean the next one: “Monday”
is 7 December, “Thursday” is 10 December (Siri, the on-device chat and the
reminder all resolve them that way).

Learned usuals after the reset (from `app/db/ride_history.py` and
`HabitService`):

| Day | Usual | Reason the app gives |
|---|---|---|
| Monday | 7:15 | you took it on 4 of your last 5 Mondays |
| Tuesday | 7:30 | you took it on each of your last 5 Tuesdays |
| Wednesday | 7:30 | you took it on 6 of your last 10 rides (only one past Wednesday ride, so the overall pattern is used) |
| Thursday | 8:00 | you took it on 4 of your last 5 Thursdays |
| Friday | 7:30 | you took it on each of your last 5 Fridays |

| Slide | Change |
|---|---|
| 1 | Tomorrow (Fri) 7:30 booked by Siri; Earlier → 7:15, Later → back to 7:30 |
| 7 | Next Monday 7:15 booked by Siri; pin the 8:00, then unpin (no bookings change) |
| 8 | Control Center: tomorrow already booked, nothing changes. Reminder: next Thursday (10 Dec) 8:00 booked |
| 9 | Import: next Mon keep, next Tue cancelled, next Wed booked, next Thu (offsite) cancelled |
| 10 | `demo_trip` replays tomorrow's 7:30 as "now" (the trip clock starts) |
| 11 | Delay → tomorrow moved 7:30 → 7:45; the simulation follows the 7:45 |
| 12 | "Should I leave now?" answered for the 7:45 |
| 13 | Next Monday moved 7:15 → 7:00 on device |
| 15 | Tomorrow moved 7:45 → 7:15 (goal); next Tuesday "by 7:30" books nothing |
| 16 | Next Thursday 8:00 booked from Claude Desktop |
| 17 | Next Thursday cancelled on device during the outage, then booked again by Siri |

## The trip clock (slides 10–12)

`demo_trip` (defaults: start 11 simulated minutes before the 7:30 departs,
2× speed, 4-minute walk) runs one continuous clock. Let **r** = real
minutes since `demo_trip` started. Calculated from the code
(`scripts/demo_trip.py`, `tracking_service.py`, `trip_planner.py`); confirm
every value in rehearsal:

| r (real minutes) | What happens |
|---|---|
| 0 | Start the command, then open Where's my shuttle and tap Start trip mode straight away |
| ~1 | "Time to leave" notification (pickup minus 4-minute walk minus 5-minute buffer) |
| 1–4 | Siri "Track my shuttle"; the Live Activity counts down |
| **before 8.5** | **Run `--delay 20`.** The 7:45 is only offered while it's still catchable (more than walk + 5 minutes before it departs). Aim for r ≈ 5 |
| after the delay | Within ~15 seconds (trip mode polls every 15 s) the delay notification arrives → Rebook. The simulation now follows the 7:45 |
| r < 8.5 | "Should I leave now?" → **No**, leave in about (17 − 2r) minutes, e.g. r = 6 → about 5 minutes; r = 7 → about 3 minutes |
| 8.5 ≤ r < 13 | "Should I leave now?" → **Yes** |
| ~13 | The 7:45 reaches the stop in the simulation; after that the question no longer makes sense |

Recommended rhythm: delay at r ≈ 5, Rebook at r ≈ 5.5, ask Siri at r ≈ 6–7;
the calculated answer is "No, leave in about 3–5 minutes". Both "No" and
"Yes" are correct answers; the script covers either.

## Time budget

About 57 minutes plus questions.

| Slides | Part | Minutes |
|---|---|---|
| 1–5 | Opening: the cold open, the idea, AI and iOS terms, what just happened | 9 |
| 6–8 | Habits and iOS entry points | 6.5 |
| 9 | Schedule import | 3 |
| 10–11 | Live commute, delay and rebook | 7 |
| 12–15 | When AI needs to think | 10.5 |
| 16 | Claude Desktop through MCP | 2.5 |
| 17–18 | Engineering for failure | 5 |
| 19–23 | Testing, limitations and what’s coming | 7.5 |
| 24–26 | Architecture, full scale, close | 5.5 |

---

## 1. Hey Siri, Welcome to the Agentic Era

Slide: `cover` · Badge: No AI · Time: 2 min

DO (before any slide; phone on the Lock Screen, mirrored over the cable):
“Hey Siri, book my usual shuttle with Clear Path.” Expected: “Done. You’re
on the 7:30 AM shuttle tomorrow, arriving at Office by 8:15 AM. That’s your
usual: you took it on each of your last 5 Fridays.” plus a card with
Earlier and Later. Tap **Earlier** (moves to the 7:15), then **Later**
(back to the 7:30; the delay demo later needs the 7:30). Then show the
title slide.

SAY: “Good morning, everyone. I just booked tomorrow’s shuttle with one
sentence to Siri, and moved it with two taps, without opening an app.
That’s the whole idea of this session: an app you mostly use without
opening it. Over the next hour I’ll walk you through Clear Path, a shuttle
app I built. Every step is live, on my iPhone and my laptop, on this Wi-Fi.
After each thing you see, I’ll explain what happened, how it works, and why
I built it that way.”

IF IT FAILS (Siri answers itself or says the app can’t do that): “And
that’s our first live failure. Siri on iOS 27 decides for itself which app
should handle a request; I’ll come back to exactly why later.” Use Type to
Siri with the same phrase and continue.

NEXT: “Before I explain what just happened, a minute on who I am and what
I set out to build.”

## 2. Not a chat box inside an app

Slide: `idea` · Time: 1.5 min

SAY: “I’m a mobile app developer. I’ve been learning AI engineering, and
the way I chose to learn it was to build one real app end to end. I
brought the iOS side: App Intents, widgets, Live Activities,
notifications, share extensions. I had to learn the AI side: agents that
call tools, RAG, MCP, Apple’s on-device models, and evaluation.

Most AI apps today are a chat box bolted onto an existing app. I wanted the
opposite: the intelligence shows up in the places iOS users already are,
Siri, widgets, Control Center, the Lock Screen, notifications and the share
sheet. There is a chat, but only for the moments a conversation helps.
Clear Path is a commuter shuttle app with one rider, me, going from Home to
the Office. A simple domain on purpose, so we can focus on the engineering.

Everything today is live. Siri and AI are not 100% reliable yet, so keep a
rough count of what fails; we’ll use that number near the end. After each
experience you’ll see one of three badges. No AI: plain code, same input,
same output. On-device AI: Apple’s models on the iPhone. Cloud AI: a
language model in the cloud, called by my backend. Keep an eye on how often
it says No AI.”

NEXT: “Before we look at what happened, eight words you’ll hear today.”

## 3. AI terms in plain English

Slide: `glossary` · Time: 1.5 min

SAY: “You don’t need to remember these; each one comes back with a demo.
An LLM is a model that reads and writes text; here, Gemini understands
‘get me there by 8’. An agent is an LLM in a loop that calls tools until
the job is done. A tool is a function the agent may call, like ‘book usual
shuttle’ or ‘plan trip’. RAG: search your own documents first, then answer
from them, with a citation. MCP is a standard plug for AI tools; Claude
Desktop books through it. An on-device model is Apple’s model on the
iPhone: no network, no cost, private. An evaluation is a test suite for AI
behaviour. And a trace is a recording of every AI step.”

NEXT: “And eight words from the iOS side.”

## 4. iOS terms in plain English

Slide: `ios-terms` · Time: 1.5 min

SAY: “An App Intent is an action my app gives to iOS, written once in
Swift; Siri, widgets, Control Center and Shortcuts all run that same code.
An App Shortcut is a set of ready-made Siri phrases for an App Intent; they
work right after install, with no setup. The Shortcuts app is where anyone
can chain App Intents from many apps into their own automations. A widget
is a small live view on the Home or Lock Screen, and its buttons run App
Intents without opening the app. A control is the same idea in Control
Center or on the Action button. A Live Activity is a live card on the Lock
Screen and Dynamic Island for something in progress, like my trip. A share
extension is my app’s entry in the share sheet; here it reads a schedule
image. And Foundation Models is Apple’s framework for the on-device
language model behind Apple Intelligence.”

NEXT: “So, back to that first Siri request. What actually happened?”

## 5. What just happened?

Slide: `what-happened` · Badge: No AI · Time: 2.5 min

SAY: “Four questions. How did Siri know my app? Through App Intents. An
App Intent is a Swift type that describes one action the app can perform,
with typed parameters. The app also declares App Shortcuts, nine booking
phrases like ‘Book my usual shuttle with Clear Path’, which iOS registers
at install, so the user sets nothing up.

Which date? The intent has one optional parameter, the day, an enum:
today, tomorrow or a weekday. I didn’t say a day, so it used tomorrow, and
the reply always says the day back. iOS ran the intent without opening the
app. It sends a plain HTTP request over this Wi-Fi to the backend on my
Mac. The Earlier and Later buttons on the card are App Intents too.

Who decides whether I get a seat? One service, BookingService. Five
morning shuttles, every 15 minutes from 7:00, and five rules in order: no
past dates, no weekends, at most 14 days ahead, booking closes 30 minutes
before departure, no full shuttles. Ask for a day you’ve already booked and
you get the booking you already have. Every surface, Siri, widgets, the
chat, even another company’s AI later, goes through these same rules.

And did it need an LLM? No. The request was already structured: an action
plus a date. Nothing to interpret, so no model was called. That’s a design
rule I followed everywhere: structured requests skip the AI. Faster, free,
and it can’t hallucinate.”

IF ASKED (Siri routing): “Siri matching is a hint, not a guarantee. Two
similar intents confused it in testing, which is why there’s one booking
intent with an optional day.”

NEXT: “One question left: what does ‘my usual shuttle’ mean?”

## 6. What “my usual” means

Slide: `habit` · Badge: No AI · Time: 1.5 min

DO: Open the app → Home → **Your commute** card. Expected: “Mon isn’t
booked yet”, “7:15 AM → arrives 8:00 AM”, “You took it on 4 of your last 5
Mondays”, and a **Book Monday 7:15 AM** button (**don’t tap it**; Siri
books Monday on the next slide). Expand **Your usual week**: sparkles =
learned, pin = pinned, circle = default.

SAY: “This card is the app’s idea of my usual commute. Tomorrow is booked,
so it looks at the next usual day: Monday isn’t booked; my usual Monday is
the 7:15, because I took it on four of my last five Mondays. Tomorrow’s
7:30 had a reason too: every one of my last five Fridays.

How it works: the card calls GET /habits. HabitService looks at my past
rides in Postgres and decides each weekday’s usual in order: a pinned
shuttle wins; otherwise the one I took most in my last five rides on that
weekday; otherwise my last ten rides overall; otherwise the saved default.
It needs at least three rides and more than half of the sample, from the
last eight weeks.

No AI. This is counting. Counting is cheaper, faster, repeatable, and
above all it can always say why.”

IF IT FAILS: “When there’s no clear pattern, it falls back to the saved
default and gives no reason, rather than making one up.”

NEXT: “That reason isn’t only on this card.”

## 7. Why the 7:15? It tells you, and you can change it

Slide: `siri-habit` · Badge: No AI · Time: 2 min

DO 1: Lock the phone or leave the app. “Hey Siri, book my usual shuttle for
Monday with Clear Path.” Expected: “Done. You’re on the 7:15 AM shuttle on
Monday, arriving at Office by 8:00 AM. That’s your usual: you took it on 4
of your last 5 Mondays.”
DO 2: App → Your commute → card menu → **Always use the 8:00 AM** (a pin
appears in Your usual week) → card menu → **Learn from my rides again**.
(Unpin before moving on: while pinned, every weekday’s usual is the 8:00.)

SAY: “Same intent as before, this time with a day. The backend asked
HabitService for Monday’s usual, the 7:15, and the reason came back with
the booking, so Siri says it. The same reason appears wherever ‘usual’ is
used: Siri, this card, the reminder, the chat and Claude Desktop.

But a learned habit can be wrong. If I start a new routine I don’t want to
wait weeks: ‘Always use the 8:00’ pins it, and a pin beats anything
learned. ‘Learn from my rides again’ hands control back. A pin changes no
bookings. Learned behaviour must be visible, explainable and overridable.”

IF IT FAILS: Retry once; then Type to Siri. “Another one for the count.”

NOTE: Pinning also makes the 8:00 the saved default, and unpinning doesn’t
restore the 7:30. No later step depends on the default, but don’t claim
“the saved 7:30” after this slide.

NEXT: “Siri isn’t the only way in. Most of the time I won’t even open the
app.”

## 8. Book without opening the app: widgets, Control Center and notifications

Slide: `one-tap` · Badge: No AI · Time: 3 min

DO 1: Show the Home Screen widget (tomorrow’s ride; no **Book tomorrow**
button, because tomorrow is booked) and the Lock Screen widget. Press
Control Center → **Book Usual Shuttle** (or the Action button). Expected:
notification “Already booked”.
DO 2: App → Your commute → card menu → **Preview reminder** (Debug build
only; fires in 5 seconds) → lock the phone. Expected: “Book Thursday’s
shuttle?” (next Thursday, 10 December: Friday, Monday and Tuesday are
booked and Wednesday isn’t a usual day) with the 8:00 and its reason →
long-press → **Book** → “Shuttle booked”.

SAY: “The widget shows my next ride. Its ‘Book tomorrow’ button is hidden
because tomorrow is booked. The Control Center button, which I’ve also put
on the Action button: ‘Already booked’. That’s the server’s duplicate check
answering, so pressing twice can never double-book.

Under the hood: WidgetKit widgets for the Home Screen and Lock Screen, and
a Control Widget, which iOS lets users place in Control Center, on the Lock
Screen or on the Action button. Both run a small intent inside the widget
extension that calls the same API.

Then the proactive part. Normally at 7 PM the evening before any usual day
I haven’t booked, the app suggests it; I triggered it early. Same habit,
same reason. Long-press, Book, done, and the app never opened: iOS runs the
notification’s action in the background. If I book that day another way,
the reminder is withdrawn. It would be easy to auto-book my usual days, but
a wrong automatic booking costs more than a tap saves. It suggests, never
books.”

IF IT FAILS: Control Center on a Friday or Saturday would say “Shuttles
don’t run on Saturdays” (that’s why the demo is on a Thursday). No
reminder: check notifications are on for Clear Path, or book Thursday from
the card’s Book button instead.

NEXT: “Habits handle the normal week. But my weeks aren’t always normal.”

## 9. When the week changes

Slide: `import` · Badge: On-device AI · Time: 3 min

DO: Photos → `clearpath-schedule.png` → Share → **Clear Path**. Expected
review: Monday office **keep** (booked by Siri on slide 7), Tuesday WFH
**cancel** (booked before the demo), Wednesday office **book**, Thursday
offsite **cancel** (booked from the reminder on slide 8), Friday leave
**nothing needed**. Switch one row off and on. Point at “Read on this
iPhone with Apple Intelligence” and “Text read from your document”. Tap
**Apply 3 Changes**.

SAY: “Next week I’m working from home on Tuesday, offsite on Thursday and
on leave on Friday. The schedule came as an image, so I share it to Clear
Path. It proposes: keep Monday, cancel Tuesday, book Wednesday, cancel
Thursday, the booking I made from the reminder a minute ago, and nothing
for Friday. Every change has a switch, and nothing happens until I tap
Apply.

How it works, all inside the share sheet, on the phone. Vision reads the
text from the image. Apple’s on-device Foundation Model turns it into
days, with guided generation: it may only output a list of weekday, date
and kind. It can’t write free text and it has no tools. Code then checks
every day: real dates, matching weekdays, no duplicates, nothing in the
past or too far ahead. Lines that look like instructions to an AI are
dropped before the model sees the text.

Only those typed days go to the server, which plans them with the same
booking rules. The document never leaves the phone: private, free, and no
cloud model involved. PDFs and text files work too, from Home → Import
work schedule.”

IF IT FAILS: “If Apple Intelligence is off or the model fails, keyword
rules take over and the screen says ‘Read on this iPhone with text rules’
and why.”

NEXT: “The week is planned. Now it’s the morning of the commute.”

## 10. Your commute, live

Slide: `where` · Badge: No AI · Time: 5 min

DO (the trip clock starts here: time-to-leave at ~1 min, Siri by ~4, delay at ~5, never after 8.5):
1. Mac, T2: `python -m scripts.demo_trip` (**r = 0**; note the time).
2. Phone: **Where’s my shuttle** → map, bus, “Simulated” tag, walking
   advice.
3. Tap **Start trip mode** → lock the phone → the Live Activity on the Lock
   Screen and in the Dynamic Island.
4. At r ≈ 1: the **Time to leave** notification.
5. By r ≈ 4: “Hey Siri, track my shuttle with Clear Path.” Siri speaks the
   status.

SAY: “On a commute morning the first question is: where is my shuttle?
There’s no real shuttle, so the backend replays tomorrow’s 7:30 as if it’s
happening now, at double speed, on an illustrative route. The screen asks
for the status every five seconds and draws it with MapKit.

Trip mode puts it on the Lock Screen and in the Dynamic Island: a Live
Activity with a countdown and a progress bar. The usual way to update a
Live Activity is push from a server, which needs a paid Apple developer
account. I don’t have one, so trip mode keeps the app running with
background location: every 15 seconds it asks the backend for the status
and updates the Live Activity itself.

Time to leave: the minutes until the shuttle reaches my stop, minus my
walk, four minutes in the demo, minus a five-minute buffer. At zero, a
time-sensitive notification, once per trip.

And ‘track my shuttle’ is a Live Activity intent, an App Intent that can
start a Live Activity straight from Siri. My first phrase was ‘Where’s my
shuttle’, but Siri on iOS 27 often answered that itself. So the phrase
leads with ‘Track’.”

IF IT FAILS (Siri answers itself): “That’s exactly the problem I just
described. One more for the count.” Use Type to Siri, but watch the clock:
don’t let it push the delay past r ≈ 7.

NEXT: “So far the commute is going to plan. Now let’s make it go wrong.”

## 11. A delay, and a better shuttle

Slide: `delay` · Badge: No AI · Time: 2 min

DO (at r ≈ 5, **never later than r = 8.5**): T2:
`python -m scripts.demo_trip --delay 20`. Expected within about 15
seconds: Lock Screen badge “20 min late”, orange bar, notification
“…running 20 minutes late. The 7:45 AM shuttle still gets you to Office by
8:30 AM, 5 minutes sooner. Rebook?” → long-press → **Rebook** →
“Rebooked”.

SAY: “My shuttle is now 20 minutes late. The Live Activity turns orange,
and a notification offers the 7:45, which gets me there five minutes
sooner. Rebook, from the notification, without opening the app.

How it chose: the backend’s trip planner looked for a shuttle I can still
catch, more than my walk plus five minutes away, that arrives sooner. The
delayed 7:30 now arrives 8:35; the 7:45 arrives 8:30. Rebook moves the
booking, and the live trip follows the new shuttle. No AI: arithmetic over
a timetable, and arithmetic belongs in code.”

IF IT FAILS (no Rebook button): “No faster shuttle could still be caught,
because I started the delay too late. That’s correct behaviour.” Slide
12’s answer will then be about the 7:30.

NEXT: “Everything so far was a predefined action: book, move, track,
rebook. What happens when I ask something that isn’t?”

## 12. When AI needs to think

Slide: `ask-siri` · Badge: Cloud AI · Time: 3.5 min

DO (straight after the Rebook, ideally at r ≈ 6–7): “Hey Siri, ask Clear
Path.” Siri: “What would you like Clear Path to do?” → “Should I leave
now?” Expected: before r = 8.5, **“No”** with about (17 − 2r) minutes
until I should leave (about 3–5 minutes); from r = 8.5 to about 13,
**“Yes”**. It ends with the weather: an umbrella tip if rain is likely,
otherwise “It’s clear, so you won’t need an umbrella”.

SAY: “‘Should I leave now?’ isn’t an action with a parameter. It’s a
question that combines several facts: where the new shuttle is, how long
my walk is, and the weather. That’s the first request today that needs
cloud reasoning. The intent first offers it to the on-device assistant,
which only handles simple commands, so it goes to the cloud agent on my
Mac.

The agent is built with LangGraph. My question goes to Gemini with a list
of 12 tools. The model either answers or asks for a tool; LangGraph runs
the tool, an ordinary Python function, gives the result back, and loops
until it can answer. Every application fact, bookings, timetable, rules,
trip status, comes from a tool, never from the model. Tools act; the model
only chooses.

Two tools here. Shuttle status: whether to leave now is computed in code;
the model only phrases it, because an evaluation once caught it saying
‘yes, leave now’ with 11 minutes to spare. And weather, from a small MCP
server I wrote. MCP, the Model Context Protocol, is a standard way for an
AI to discover and call tools in another program; it calls the free
Open-Meteo API.

The model is Gemini 3.5 Flash-Lite, then a retry, then 3.1 Flash-Lite,
each with an 8-second deadline. I chose it by measuring: the cheapest
model that measurably works.”

IF IT FAILS (slow or no answer): “Free-tier Gemini can be slow or
rate-limited. Each attempt gets 8 seconds before the next model; if all
fail, it says honestly that the assistant is unavailable.” Count it.

NEXT: “I asked that through Siri. What if I continue in the app?”

## 13. One conversation, and not every message needs the cloud

Slide: `memory` · Badge: Cloud AI + On-device AI · Time: 2.5 min

DO 1: App → **Ask Clear Path**. Expected: the Siri question and answer
are there, with “Checked the weather · via weather MCP server”.
DO 2: Type “What do I have booked?” → reply labelled **On device · Apple
Intelligence**. Then “Move Monday earlier” → next Monday 7:15 → 7:00, also
on device.

SAY: “The question I asked Siri is already here, with what the agent did:
it checked the weather, via my MCP server. Siri and the chat share one
conversation: the phone keeps a conversation id for 30 minutes, and
LangGraph saves each conversation in Postgres. That’s what makes follow-ups
like ‘make it earlier’ work.

Now look at this label: that answer never left the phone. And ‘Move Monday
earlier’: 7:15 to 7:00, also on the phone. Simple commands go through
three checks. A rules gate in plain code: short, no question words,
exactly one action, a named day for any change. Then Apple’s on-device
model classifies it into an action and a day, within three seconds. Then
the model’s answer must match what the rules read. Any mismatch and it
goes to the cloud. Then it calls the same endpoints Siri uses and saves the
turn into the shared conversation. Faster, free, private, and it keeps
working when the cloud is down. You’ll see that.”

IF IT FAILS (no label): “The on-device model declined or disagreed, so the
cloud answered instead. That’s the safety design working.”

NEXT: “Commands are easy. Explanations need knowledge the app has to look
up.”

## 14. Answers with sources

Slide: `rag` · Badge: On-device AI (speech) + Cloud AI (answer) · Time: 2 min

DO: Tap the mic → “Why can’t I book Saturday?” → tap stop. Expected: the
rule plus a cited Booking Policy passage.

SAY: “I asked by voice. Speech-to-text ran on the phone with Apple’s
SpeechAnalyzer: On-device AI.

The answer is Cloud AI. The agent first called an eligibility tool, which
returns the real rule from BookingService. Then it searched our policy
documents. That’s RAG, retrieval-augmented generation. The four policy
documents are split into 16 sections; each was turned into an embedding,
384 numbers that capture its meaning, by a small model running locally on
my Mac, and stored in Postgres with pgvector. My question is embedded the
same way and compared. Below 0.60 similarity a passage is dropped; only the
top passage, at 0.70 or more, becomes a citation. So the rule comes from
code, the explanation from our documents, and the citation shows where.”

IF IT FAILS: “If nothing is close enough there’s no citation, and the agent
says it doesn’t know.” If the mic isn’t available, type the question.

NEXT: “One more kind of request: instead of a time, I give it a goal.”

## 15. Goals instead of times

Slide: `goal` · Badge: Cloud AI (understanding) + No AI (the planner) ·
Time: 2.5 min

DO 1: “I have a meeting at 8 tomorrow, get me there in time.” Expected:
“Booked your trip plan”: tomorrow 7:45 → **7:15**, arriving 8:00.
DO 2: “Get me to the office by 7:30 on Tuesday.” (next Tuesday, 8
December; not booked since the import) Expected: “No shuttle gets you
there by 7:30 AM. The soonest is the 7:00 AM, arriving 7:45 AM.” Nothing
booked.

SAY: “For the meeting at 8 it moved me from the 7:45 to the 7:15, which
arrives at 8:00. For 7:30 on Tuesday it says honestly that no shuttle gets
me there, offers the earliest, and books nothing.

Here the model only reads: it turns my sentence into a date and an
arrive-by time. A deterministic trip planner, plain Python over the
timetable and the rules, picks the shuttle. It’s the same planner that
found the 7:45 during the delay. A statement like ‘get me there’ books; a
question like ‘will I make it by 8:20?’ only plans.

This wasn’t my first design. Originally the agent did the time arithmetic
itself, and in evaluation it booked impossible trips. Goal scenarios
passed 4 of 9. With the planner: 9 of 9. Let the model understand; let
code decide.”

IF IT FAILS: “When no shuttle meets the goal, it offers the soonest one and
never books it without my OK.”

NEXT: “Everything so far happened in my app. Can other AI tools use Clear
Path too?”

## 16. Booking from Claude Desktop

Slide: `mcp` · Badge: Cloud AI (external client: Claude Desktop); Clear
Path’s side is No AI · Time: 2.5 min

DO: Switch to Claude Desktop. “My offsite next Thursday was cancelled. Book
my usual shuttle for Thursday 10 December” → allow the tool → booked, the
8:00 with its reason → refresh the iPhone app: Thursday is there. “What’s
my usual Monday?” → 7:15 with its reason. “Book Saturday too” → “Shuttles
don’t run on Saturdays.” (Name the date: said on a Thursday, “Thursday”
alone could be read as today.)

SAY: “Claude Desktop is a different AI, from a different company. It asked
my permission to use a Clear Path tool, booked next Thursday, and the
booking is already on my phone. It knows my usual for each day and why.
And Saturday is refused, by my rules, not by Claude.

This is MCP again, in the other direction. Earlier my agent was the client
and the weather server the provider. Here my backend is the provider: an
MCP server with 13 tools, the same 12 my agent uses plus today’s date.
Because those tools call the same services, any AI client is held to
exactly the same business rules. Each tool is labelled read-only or
changing, and cancel is labelled destructive, so a client can ask before
using it. My app is a tool any AI can use, and my agent can use any tool.”

IF IT FAILS: If Claude Desktop shows no tools, check the clear-path server
in Settings → Developer, then retry.

NEXT: “That’s everything working as designed. Now let’s break something
on purpose.”

## 17. The cloud AI goes down

Slide: `outage` · Badge: Cloud AI (unavailable) + On-device AI + No AI ·
Time: 3 min

DO: T3: `python -m scripts.llm_outage on` (no restart). Optional: `curl
localhost:8000/health` → `"llm":"outage"`. Chat: “Why can’t I book
Saturday?” → “Clear Path’s assistant is unavailable right now. Bookings
still work…”. Chat: “Cancel Thursday” → **On device**, next Thursday
cancelled (not Friday: that’s tomorrow’s trip). “Hey Siri, book my usual
shuttle for Thursday with Clear Path” → the 8:00 on Thursday, booked
again. Optionally press the Control Center control.

SAY: “A feature isn’t finished until you know how it fails. I’ve just
simulated the model provider going down, without restarting anything. A
question that needs the cloud gets an honest answer: the assistant is
unavailable, and here’s what still works. Nothing is made up.

‘Cancel Thursday’ still works: On-device AI. Siri booking still works: it
was always No AI. Widgets and Control Center too.

The switch is a flag file that makes the backend hand out stand-in models
that fail immediately, like an unreachable provider. The real fallback
chain still runs all three attempts and then returns an honest error. Why
most of the app survives: every iOS surface sends structured requests to
deterministic services, and simple chat runs on the phone. The AI is an
enhancement, not a single point of failure.”

NEXT: “When that happens for real, how do I find out what went wrong?”

## 18. Tracing every turn

Slide: `trace` · Badge: No AI (it records the Cloud AI and On-device AI
turns) · Time: 2 min

DO: Langfuse (http://localhost:3000) → the failed turn (ERROR, every
attempt) → a normal turn (model calls, tool spans, timings) → an on-device
turn tagged `on-device`. Then T3: `python -m scripts.llm_outage off`, and
ask the chat any question to show it’s back.

SAY: “This is Langfuse, self-hosted in Docker, so nothing leaves my
laptop. Here’s the turn that just failed: an error, with every fallback
attempt and the reason. A normal turn: each model call and tool call, with
inputs, outputs and timings. On-device turns are recorded too, and so is
every evaluation run.

One rule tracing protects: never hide a real change. If the model fails
after a booking has already changed, the reply still says ‘I made changes
to your bookings but couldn’t finish replying.’ The worst thing an
assistant can do is change your booking and then tell you it failed.
I’m switching the cloud back on.”

NEXT: “Those were planned failures. How do I know the normal behaviour is
reliable?”

## 19. How I know it works

Slide: `tests` · Badge: No AI (tests and hard checks) + Cloud AI (agent
evaluations and the AI judge) · Time: 1.5 min

SAY: “Everything worked today. But how do I know it works tomorrow, after I
change a prompt or swap a model? With an LLM you can’t assert an exact
sentence, but you can assert which tools it called, what the bookings look
like afterwards, and which sources it cited. QA folks, this is for you.

Three layers. About 150 backend tests that run in seconds, on a separate
test database with a frozen clock and no network. 76 Swift tests and 2 UI
tests on the iOS side. And evaluations: 36 scenarios run the real agent
with real Gemini on an isolated database at a fixed date, plus 15
documents for schedule extraction.

One evaluation: a setup, like a trip running or shuttles full; messages to
the real agent; then hard checks, like unit-test assertions: right tools,
no wrong ones, the exact final bookings, the right policy cited. Only then
does an AI judge score the reply from 1 to 5. A check mode fails the run
if success drops more than 5 points from the saved baseline.”

NEXT: “Here’s where the numbers stand, and what they caught.”

## 20. What evaluations caught

Slide: `caught` · Badge: Cloud AI (the bugs) → No AI (most fixes moved
the decision into code) · Time: 1.5 min

SAY: “The saved baseline, all 36 scenarios on Gemini 3.5 Flash-Lite: 33
passed, the right tools every time, judge score 4.67 out of 5, median reply
8 seconds, about $0.002 per task at list price, and nothing on the free
tier.

The numbers matter less than what the evaluations found, each connected to
something you saw today. Goals, slide 15: the agent did time arithmetic
and booked impossible trips; the trip planner took it from 4 of 9 to 9 of
9. The habit reason, slide 7: the agent once said ‘4 of your last 5’ with
no data behind it; now it may only use the reason the tool returns. The
policy answers, slide 14: a question didn’t find the FAQ; I reworded and
re-indexed it. And ‘should I leave now’, slide 12: yes with 11 minutes to
spare; now computed in code. That’s why hard checks come first, and I read
every failure myself.”

NOTE: These are the 2026-11-08 baseline numbers. If a new full baseline is
saved, replace them.

NEXT: “So if this can be engineered, why don’t we see many apps like this
yet?”

## 21. Why apps like this are still rare

Slide: `limits-siri` · Time: 1.5 min

SAY: “First, today’s count. How many things failed live?” (Count with the
room; recap each in one line. If one failed naturally: Siri answered
itself → it routes with its own model; slow chat → free-tier limits and
fallbacks; no On-device label → the model must agree with the rules gate;
no Rebook → no faster shuttle was catchable.)

“Siri is the first reason these apps are rare. On iOS 27 Siri uses its own
model to decide which app handles a request, so an App Shortcut phrase is a
strong hint, not a guarantee. It misheard my app’s name as ‘Clear
Footpath’, which is now literally one of the app’s alternative names. It
can drop the day from a request, so the app asks ‘Which day?’. And it
intercepted ‘Where’s my shuttle’.

The models and the platform add more. Apple’s on-device AI isn’t on every
iPhone, so there’s always a fallback. Push needs a paid developer account,
hence trip mode. Free-tier replies can take up to about 29 seconds, so
every call has a deadline and a fallback. The model once replied with just
a tool name, and Siri read it out loud; that reply is now rejected. None
of these are bugs in my code, but a user would blame the app. The AI calls
are a small part of this app; making them trustworthy is most of the
work.”

NEXT: “But this is already changing. Let me show you another app on the
same phone.”

## 22. Siri is catching up: iOS 27

Slide: `siri-next` · Badge: No AI (Clear Path); the redBus app is
someone else’s · Time: 1.5 min

DO (phone mirrored): open redBus on the upcoming trip, then swipe home so
it’s in the background. “Hey Siri, where’s my bus pickup point?”
Expected: Siri answers from redBus with the boarding point and time; no
app name, no Shortcut. Then, for contrast: “Hey Siri, track my shuttle.”
Expected: Siri asks Wallet or Clear Path, or answers itself; either makes
the point.

SAY: “That was redBus. I never set anything up for it, and I’d never used
Siri with it before; the first time I asked, it just answered. Compare
Clear Path: I have to say ‘with Clear Path’, and without it Siri asks
whether I mean Wallet.

So what’s different? iOS 27 rebuilt Siri, and apps can now describe their
actions and their data in shapes Siri already understands. Three pieces.
Intent schemas: an App Intent marked with a schema, which Siri can run
from natural language. No phrases to write, and it keeps working as Siri
learns new languages. Apple’s own example is ‘When and where is my next
meeting?’, answered from a calendar app without naming it. Indexed
entities: the app puts its data, say my next trip with its pickup point
and time, into the system’s semantic index, so Siri can find the answer
and the app that holds it. Apple calls this the main way Siri retrieves
app content. And screen awareness: the app tells Siri which booking is on
screen, so ‘share this ticket’ works.

Clear Path is built with the iOS 26.4 SDK, so it has none of this yet;
it’s the first item on my list. These features are reaching apps slowly,
one app at a time, but the direction is clear: the app name is becoming
optional. The work moves from writing phrases to describing your data
well.”

IF IT FAILS (redBus doesn’t answer): “It answered when I tried it at
home. Siri routing is live and not guaranteed, which is the previous
slide’s point; the slide shows how it works.” Count it.

IF ASKED (why not just add it now?): “It needs Xcode 27 and the iOS 27
SDK; I didn’t want to change the toolchain in the week of a live demo.”

Technical details (on the slide): `@AppIntent(schema:)` /
`@AppEntity(schema:)` for intent schemas; `IndexedEntity`, indexed with
`CSSearchableIndex.indexAppEntities`, for the semantic index;
`.appEntityIdentifier` view annotations and `.userActivity` for screen
awareness. Sources: Apple’s WWDC26 iOS guide and sessions 240, 343, 344
and 345; redBus’s App Store listing (Siri answers boarding details, “Smart
Screen Awareness”).

NEXT: “And Siri is only one part of iOS 27.”

## 23. More from iOS 27

Slide: `ios27-more` · Time: 1.5 min

SAY: “Siri is one part of iOS 27. Three more changes matter for an app
like this.

First, Private Cloud Compute is now open to developers. It’s Apple’s
large server model, with a 32,000-token context and a reasoning level you
choose: light, moderate or deep. No API keys, no accounts to set up; usage
counts against each user’s iCloud account, with daily limits. Apple says
there’s no cloud cost for apps under two million first-time downloads,
though its pages differ on the exact terms, and it only runs on Apple
Intelligence devices. For Clear Path that could replace the free-tier
Gemini calls, with their daily limits and slow replies.

Second, Foundation Models, the on-device framework, got a big upgrade. A
rebuilt on-device model that Apple says is better at logic and tool
calling, with twice the context. It accepts images, and comes with
built-in OCR and barcode tools; my schedule import chains Vision OCR into
the model by hand today. And one LanguageModel protocol covers the
on-device model, Private Cloud Compute, and Swift packages from Google
and Anthropic, so switching providers is a line of code. There’s also a
new Evaluations framework in Xcode, which would finally let me evaluate
the on-device model properly.

Third, App Intents go beyond Siri phrases. RelevantEntities tells the
system what’s relevant now, for proactive suggestions; I removed Siri
donations because Siri reused an old day, so this is the replacement I’d
test. LongRunningIntent runs past the 30-second limit and shows progress
as a Live Activity. AppIntentsTesting tests intents in isolation, no Siri
involved, which would catch the routing problems I’ve only found by hand.
And Siri can act on a notification, so a delay alert on AirPods could be
answered with ‘rebook it’.

All of this needs Xcode 27, so it’s the plan after this demo, not part of
it.”

IF ASKED (is PCC really free?): “Apple says no cloud cost under two
million first-time downloads; one page adds the Small Business Program,
which needs a paid developer account. I’d confirm the terms before relying
on it.”

Technical details (on the slide): `PrivateCloudComputeLanguageModel`
(`ContextOptions(reasoningLevel:)`: `.light`, `.moderate`, `.deep`);
Foundation Models' `LanguageModel` protocol, image attachments,
`OCRTool`, `BarcodeReaderTool`, the Evaluations framework;
`RelevantEntities.shared.updateEntities(_:for:)`, `LongRunningIntent`,
`AppIntentsTesting`, `UNMutableNotificationContent.appEntityIdentifiers`.
Sources: WWDC26 sessions 241, 242, 319, 339 and 345. Not covered by
Apple’s pages: AI notification summaries, Visual Intelligence.

NEXT: “Let me put everything we’ve seen into one picture.”

## 24. Architecture: from iPhone to Gemini

Slide: `arch` · Time: 2 min

SAY: “Left to right. On the iPhone: App Intents for Siri, WidgetKit and the
Control Center control, ActivityKit for the Live Activity, notifications,
the share extension and the chat. Apple’s on-device AI does the private
work: Vision reads documents, Foundation Models reads schedules and routes
simple chat, Speech turns voice into text.

Over this Wi-Fi, HTTP to FastAPI on my Mac. Two paths. Structured
requests, Siri phrases, buttons, notification actions and on-device chat,
go straight to REST endpoints: No AI. Open questions go to the LangGraph
agent, which calls Gemini 3.5 Flash-Lite, with a retry and 3.1 Flash-Lite
behind it, 8 seconds each. That’s the only cloud AI, plus the free
Open-Meteo weather API. Both paths end in the same services: booking, trip
planning, habits, tracking.

Docker runs the rest. Postgres 17 with pgvector holds the bookings, my
ride history, the conversation memory and the policy embeddings, made
locally with a small open model. Langfuse runs as six containers: web,
worker, Postgres, ClickHouse, Redis and MinIO. On the side: MCP in, Claude
Desktop with 13 tools; MCP out, the weather server; and the evaluation
harness. Cost so far: nothing.

At the bottom, the five rules behind all of it: facts stay deterministic;
tools act, the model only chooses; structured requests skip the AI; the
cheapest model that measurably works; and be honest when something fails.”

NEXT: “So what would it take to make this a real product?”

## 25. From prototype to full scale

Slide: `prod` · Time: 2 min

SAY: “This is a prototype, built deliberately for one rider, on a laptop,
with zero spend. Every shortcut was a choice, and here’s what changes for
full scale.

Users and security: today every request says ‘user 1’. Production means
Sign in with Apple or company sign-on, HTTPS, an API gateway, OAuth for the
MCP server, and treating location and habits as personal data. Platform:
from my laptop to a managed, autoscaled service, with migrations, backups,
and a real transit feed instead of the simulator. Mobile: with a paid
developer account, server push for alerts and Live Activities instead of
keeping the app awake; localisation and accessibility. AI quality and
cost: a paid tier with fallback across providers, evaluations gating every
change. And cost: at about $0.002 per AI task, a thousand riders making
four AI requests a day is roughly $8 a day; Siri, widgets, notifications
and on-device chat cost nothing per request.

Where I’d focus next: first, the iOS 27 Siri features we just saw,
with the next trip indexed so Siri can answer without the app name; then
teach the on-device path more commands; push and
Smart Stack relevance; evaluations running on every change; better
retrieval; and proper evaluations for the on-device model.”

NEXT: “And what this means for the work we do here.”

## 26. What this means for our projects

Slide: `busoft` · Time: 1.5 min

SAY: “This isn’t really about shuttles. The same four steps apply to the
client apps we build at BUsoft. Expose the app’s real actions as
structured things: App Intents, widgets, notifications, and describe
your data so Siri can find it; that’s what makes the app name optional.
Add AI only where
it earns its place: on-device when it can, cloud when it must. Make
evaluations part of QA from day one, hard checks first, then a judge. And
design how each AI feature fails before it ships. Banking, retail,
healthcare, logistics: the domain changes, the pattern doesn’t.

(Slowly, then pause.) The AI isn’t a chat box inside the app. It works
through the parts of iOS people already use. That’s the agentic era, and
it’s still being engineered. Thank you. Happy to take questions, and I can
show any part again live.”

Prepared answers:
- Why Gemini? Free tier and measured latency; in production the
  evaluations would decide between providers.
- Why not just a chatbot? Most commute actions are structured; a button or
  a Siri phrase is faster and can’t hallucinate.
- What did it cost? Nothing: free-tier Gemini, self-hosted tools, no paid
  accounts.
- Could it work on Android? Yes. The rules live on the backend; the OS
  surfaces would be rebuilt natively.
- What about prompt injection in imported documents? Five layers:
  instruction-like lines dropped on the phone; the on-device model is told
  the document is data and has no tools; its output can only be typed
  days; the server accepts only a date and a kind; nothing changes until
  Apply.
- What if Siri doesn’t understand? Type to Siri, the widget, or the app;
  every surface reaches the same rules.
- How do you test something non-deterministic? Hard checks on tools,
  bookings and sources first, then a judge for wording (slide 19).

---

# Appendix

## A1. Coverage checklist

Everything built (PRODUCT.md flows F1–F14 and the supporting work), and
where it appears:

| Built | Slides |
|---|---|
| F1 Siri booking, optional day, Earlier/Later card, “Which day?” | 1, 5, 7, 21 |
| F2 Home and Lock Screen widgets, Control Center, Action button, duplicate protection | 8 |
| F3 Schedule import (share sheet, in-app photo/file/PDF, Vision OCR, Foundation Models, validation, rules fallback, review and Apply) | 9 |
| F3/F13 Prompt-injection defences (no live demo) | 9, 26 (Q&A) |
| F4 Delay alert with Rebook / Keep | 11 |
| F5 Time to leave, “Should I leave now?”, weather | 10, 12 |
| F6 Map, trip mode, Live Activity (Lock Screen, Dynamic Island), Siri tracking | 10 |
| F7 Goal planning (book, question-only, honest no) | 15 |
| F8 Rules + RAG with citations | 14 |
| F9 Chat, voice input, Siri “Ask Clear Path”, shared memory, action rows and sources | 12, 13, 14 |
| F10 Learned habits, reasons, pin, Your commute card, reminder with Book | 6, 7, 8 |
| F11 Clear Path MCP server (13 tools, annotations) | 16 |
| E Weather MCP server (agent as MCP client) | 12, 16 |
| F12 Evaluation harness, AI judge, baseline, Langfuse tracing | 18, 19, 20 |
| F13 LLM outage switch, honest 503, /health | 17 |
| F14 On-device routing (chat and Siri) | 12, 13 |
| Model choice, fallback chain, 8-second deadlines, unusable-reply rejection | 12, 21 |
| Partial-failure honesty | 18 |
| Backend tests (isolated database), Swift and UI tests, schedule extraction eval | 19 |
| Alternative app names | 21 |
| iOS 27 Siri without the app name (redBus live; intent schemas, indexed entities, screen awareness) | 22, 25, 26 |
| iOS 27 beyond Siri: Private Cloud Compute, Foundation Models upgrade, App Intents (RelevantEntities, LongRunningIntent, AppIntentsTesting) | 23 |
| Infrastructure: FastAPI, Docker, Postgres + pgvector, Langfuse containers | 24 |
| Production gaps, cost, next focus areas | 25 |
