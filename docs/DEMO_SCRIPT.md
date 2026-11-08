# Demo script: Hey Siri, Welcome to the Agentic Era

Speaker script for each slide of the deck (https://claude.ai/artifact/HZYoYJ5KyrqThf3Z7GCKmZ), the same text as its speaker notes. DO = what to do on the phone or laptop; SAY = what to say; IF IT FAILS = the fallback line. Demo: Tuesday 17 November 2026; setup in [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md), story in [DEMO_STORY.md](DEMO_STORY.md).

## 1. Hey Siri, Welcome to the Agentic Era

DO (before this slide, phone on the Lock Screen, mirrored): “Hey Siri, book my usual shuttle with Clear Path.” Siri: “Done. You’re on the 7:30 AM shuttle tomorrow, arriving at Office by 8:15 AM. That’s your usual: …” Tap Earlier, then Later, so it ends on the 7:30 again (the delay demo needs it).  
SAY: “Hold that thought. I’ll come back to what just happened.”  
DO: show this title slide.  
SAY: “Good morning, everyone. This talk is called ‘Hey Siri, Welcome to the Agentic Era’. What you just saw was a booking made by voice, with no chat window, and in a few minutes I’ll show you it didn’t even need an LLM. Everything today is live, on my iPhone and my laptop, on this Wi-Fi. I’ll walk you through an app I built, and after every step I’ll open the hood and show how the iOS side, the backend and the AI work together.”  
IF IT FAILS (Siri misses the cold open): “And there’s our first live failure. Hold on to it; I’ll explain exactly why it happens in Act 7.” Use Type to Siri and carry on.  

## 2. Bridging mobile development and AI

SAY: “A little about me. I’m a mobile app developer, and I’ve been learning AI engineering by building this app end to end. This slide is the bridge I was trying to build.  
On the left, the iOS side I already knew and leaned on: SwiftUI and Swift concurrency; App Intents, which is how Siri and Shortcuts talk to apps; widgets, controls and Live Activities; notifications, location and maps; and share extensions.  
On the right, the AI side that was new to me: agents that call tools, built with LangGraph; RAG, which means searching your own documents, using pgvector; MCP, a protocol for plugging AI tools together, used in both directions; Apple’s on-device Foundation Models; and evals and tracing with Langfuse.  
Neither column on its own was the hard part. Making them work together was. I’m still learning, and I’ll be honest today about where I hit limits.”  

## 3. Not a chat box inside an app.

SAY: “The app is called Clear Path. It’s a commuter shuttle app: one rider, me, going from home to the office.  
Here’s the idea. Most ‘AI apps’ today are a chat box bolted onto an app: you open the app, find the chat, type a sentence. I wanted the opposite. The AI should work through the parts of iOS you already use every day: Siri, widgets, Control Center, the Action button, Live Activities on the Lock Screen, notifications and the share sheet.  
There is a chat, and you’ll notice it’s drawn dashed on the slide. It’s there only where a conversation genuinely helps, like asking why something isn’t allowed. The app is where you go only when you want to.”  

## 4. Five rules behind every feature

SAY: “Five rules shaped every decision you’ll see today, so keep them in mind.  
One: facts stay deterministic. Bookings, times and seats come from the database, through code. The AI never invents them.  
Two: tools act; the AI only chooses. The model decides which function to call, and the function does the work. Business rules like ‘no weekends’ live in one service that every surface shares: Siri, widgets, chat, even another company’s AI.  
Three: structured requests skip the AI. If you tap a button or say an exact Siri phrase, there’s nothing to interpret, so no LLM is called. Faster, free, and it can’t hallucinate.  
Four: use the cheapest model that measurably works, decided with evals, not by brand name.  
Five: be honest when something fails. Never hide a change, never fake an answer. I’ll break things on purpose later to prove that one.”  

## 5. One phone, one laptop, a little cloud

SAY: “Physically, this is the whole setup.  
On the iPhone the app has three parts: the app itself; a widget extension, which powers the widgets, the Control Center button and the Live Activity; and a share extension, for importing a schedule from the share sheet. The phone also runs Apple’s on-device model, Vision for reading text in images, and speech recognition, all locally.  
The phone talks over this Wi-Fi to my Mac. There, a Python FastAPI backend runs the LangGraph agent, the booking services and the MCP servers.  
Docker runs Postgres with the pgvector extension, which stores bookings, the agent’s conversation memory and the policy embeddings, plus six containers for Langfuse, the tracing tool, self-hosted.  
The only cloud calls are to Gemini Flash-Lite on the free tier and a free weather API. Total cost so far: nothing. No paid APIs, no hosting, no paid Apple developer account. That last one will matter later.”  

## 6. Eight words you’ll hear today

SAY: “We have devs, QA, BAs and managers here, so eight words in plain English, each with an example from this app.  
An LLM is a model that reads and writes text. Here, Gemini understands ‘get me there by 8’.  
An agent is an LLM in a loop that calls tools until the job is done.  
A tool is just a function the agent is allowed to call, like ‘book usual shuttle’ or ‘plan trip’.  
RAG means search your own documents first, then answer from what you found, with a citation.  
MCP is a standard plug for AI tools. Later, Claude Desktop will book a shuttle through it.  
An on-device model is Apple’s model running on the iPhone: no network, no cost, private.  
An eval is a test suite for AI behaviour. QA folks: think of regression tests for things that aren’t deterministic. I have 36.  
And a trace is a recording of every AI step, its timing and its result.”  

## 7. One rider, Home → Office

SAY: “To keep the demo about the AI, not about user management, there’s one rider: me, Home to Office.  
Five morning shuttles, every fifteen minutes from 7:00, each a 45-minute ride with 10 seats.  
Five booking rules, checked in this order: no past dates, no weekends, at most 14 days ahead, booking closes 30 minutes before departure, and no full shuttles. Every refusal comes back as a plain sentence, like ‘Shuttles don’t run on Saturdays.’  
One detail: if you ask to book the same day twice, you don’t get an error; you get the booking you already have.  
The demo database also has six weeks of past rides, so the app has habits to learn from. That’s where we start.”  

## 8. Everything is live. Some of it will fail.

SAY: “Before we start, ground rules. Everything is live: Siri, Apple’s on-device model, a free-tier cloud model, and my laptop on this Wi-Fi.  
Siri and AI aren’t 100% reliable yet, and that’s part of what I want to show you. If something fails, I’ll explain how and why. In Act 5 I’ll break things on purpose.  
I’d actually like you to keep count of what fails today. We’ll come back to that number.  
After each live step you’ll see one ‘Under the hood’ slide with one of these badges: No AI, On device, or Cloud AI. Watch how often it says No AI.”  

## 9. The evening before

SAY: “Act 1: the evening before. The week is about to start and I want my shuttles sorted without thinking about it.  
Four things: a commute card that learned my habits from real rides, a reminder that offers to book for me, Siri booking my learned usual, and a photo of my work schedule turning into bookings.  
Notice: there’s no chat anywhere in this act.”  
DO: switch to the phone mirror.  

## 10. Habits are learned, not guessed

DO: Home → Your commute card: “Thu isn’t booked yet”, “8:00 AM → arrives 8:45 AM”, “You took it on 4 of your last 5 Thursdays”. Expand “Your usual week”. Card menu → “Always use the 8:00 AM” (a pin appears) → “Learn from my rides again”.  
SAY (on the phone): “This card says Thursday isn’t booked yet, my usual Thursday shuttle is the 8:00, and why: I took it on 4 of my last 5 Thursdays. In ‘Your usual week’, sparkles mean learned, a pin means I pinned it, a circle means the default. I can pin a shuttle to override the learning, and unpin it again.”  
SAY (this slide): “How does it work? The SwiftUI card calls one endpoint, GET /habits. On the backend, a HabitService looks at my past rides in Postgres. For each weekday: a pinned shuttle wins; otherwise the one I took most in my last 5 rides on that weekday; otherwise my last 10 rides overall; otherwise the saved default, the 7:30. It needs at least 3 rides and a clear majority, and only the last 8 weeks count.  
Look at the badge: No AI. This is counting. Counting is cheaper, faster and, above all, explainable, so every surface can tell you why.”  
IF IT FAILS: “If there’s no clear habit, it falls back to the 7:30 and simply gives no reason, rather than making one up.”  

## 11. A reminder that suggests, never books

DO: card menu → Preview reminder (Debug build; fires in 5 seconds) → lock the phone → “Book Thursday’s shuttle?” → long-press → Book → “Shuttle booked”.  
SAY (on the phone): “In real life this arrives at 7 PM the evening before any usual day I haven’t booked. I’ll trigger it now. ‘Book Thursday’s shuttle? Your usual Thursday shuttle is the 8:00 AM, arriving 8:45 AM, you took it on 4 of your last 5 Thursdays. You haven’t booked it yet.’ Long-press, Book. Done, and the app never opened.”  
SAY (this slide): “It’s a local notification the app schedules from the habits it loaded. The Book button is a notification action that runs in the background and calls the same booking endpoint as everything else, with the same rules. If I’d booked Thursday another way, through Siri, the widget or the card, this reminder would have been withdrawn.  
The design decision I care about: it suggests, it never books by itself. Proactive, but not presumptuous.”  
IF IT FAILS: “If the booking is refused, I get a ‘Couldn’t book’ notification with the reason.” If the notification doesn’t appear, check notifications are on for Clear Path, say so, and move on.  

## 12. Siri books the learned usual

DO: “Hey Siri, book my usual shuttle for Monday with Clear Path.” Expect the 7:15 and “That’s your usual: you took it on 4 of your last 5 Mondays.”  
SAY (on the phone): “Notice it booked the 7:15, not my saved 7:30, because on Mondays I usually take the 7:15. And it told me why.”  
SAY (this slide): “How does Siri know about my app? App Intents. The app registers nine booking phrases through App Shortcuts when it’s installed: no setup by the user, and they appear in the Shortcuts app too. ‘Monday’ is a typed parameter, a list of today, tomorrow and the weekdays, which is how Siri fills it in.  
The intent sends a structured request with a date to the backend. It’s already structured, so no LLM is called: No AI again. The backend applies the same rules and asks HabitService for Monday’s usual.  
Every booking is also donated to iOS, so Siri Suggestions and Spotlight can start suggesting it.”  
IF IT FAILS (Siri answers itself or says the app can’t do that): “That’s iOS 27 Siri routing requests with its own model. The phrase is a strong hint, not a guarantee. Let’s count that one.” Retry once, then Type to Siri.  

## 13. A photo becomes bookings, privately

DO: Photos → next week’s schedule → Share → Clear Path. Review shows Monday keep, Tuesday WFH cancel, Wednesday book, Thursday offsite and Friday leave nothing needed. Switch one row off and on. Point at “Read on this iPhone with Apple Intelligence” and “Text read from your document”. Tap Apply 2 Changes.  
SAY (on the phone): “My work schedule for next week came as an image. I share it to Clear Path from Photos. It read Monday: office, already booked, so keep. Tuesday: work from home, so cancel the booking I had. Wednesday: office, book. Thursday offsite and Friday leave: nothing to do. I can switch any change off. Apply.”  
SAY (this slide): “Everything up to this review happens inside the share sheet, on the phone. Vision reads the text from the photo. Then a safety step removes any line that looks like instructions to an AI; remember that, it matters in Act 5. Then Apple’s on-device model turns the text into days, using guided generation: it can only output a list of weekday, date and kind. No free text, no tools.  
Only those typed days go to the server, which plans with the normal booking rules. The document itself never leaves the phone. Private and free.  
It also takes PDFs and files, from Home, Import work schedule.”  
IF IT FAILS: “If Apple Intelligence is off or the model fails, keyword rules take over, and the screen says ‘Read on this iPhone with text rules’ and why.”  

## 14. The morning

SAY: “Act 2: the morning. This is where the app should help before I ask: tell me when to leave, warn me about delays, and let me act right from the Lock Screen.  
Seven steps, starting with what happened in the very first minute of this talk.”  

## 15. The cold open needed no LLM

SAY: “Remember the cold open? ‘Book my usual shuttle with Clear Path.’ No day, so it means tomorrow, and Siri always says the day back.  
The card Siri showed is a SnippetIntent, an interactive view inside Siri. The Earlier and Later buttons are App Intents themselves: they call the reschedule endpoint, and the backend moves me to the nearest shuttle I can still book. If there’s no earlier or later one, that button is disabled.  
The badge says No AI. There was nothing to interpret, so we don’t call an LLM. Fast, free, and impossible to hallucinate. If I had to pick one line from this whole project: the most reliable AI step is the one you don’t need.”  
IF IT FAILS: “If my laptop weren’t reachable, Siri would say ‘I couldn’t reach Clear Path. Check your connection and try again.’ A rule refusal is read out as the server’s own sentence.”  

## 16. One tap, from anywhere

DO: Show the Home Screen widget (tomorrow’s ride, no Book tomorrow button), the Lock Screen widget, then press the Control Center button or the Action button → notification “Already booked”.  
SAY (on the phone): “Same booking, other surfaces. The Home Screen widget shows my next ride. It normally has a ‘Book tomorrow’ button, but tomorrow is already booked, so it hides it. Same on the Lock Screen. Now the Control Center button, which I’ve also put on the Action button. Press. ‘Already booked.’”  
SAY (this slide): “The widgets use WidgetKit. The button is a ControlWidget, which you can place in Control Center, on the Lock Screen or on the Action button. Both run one small intent inside the widget extension that calls the API directly and confirms with a local notification.  
The backend checks for duplicates first, so pressing twice can never double-book.”  
IF IT FAILS: “On a Friday or Saturday you’d see ‘Booking failed: Shuttles don’t run on Saturdays.’ That’s exactly why this demo is on a Tuesday.”  

## 17. Trip mode: live updates without push

DO: Terminal: python -m scripts.demo_trip. Phone: Where’s my shuttle → map → Start trip mode → lock the phone. Live Activity on the Lock Screen and in the Dynamic Island. (The delay step must happen within about 8 minutes of this.)  
SAY (on the phone): “Now the trip. I’m starting a simulated trip for tomorrow’s 7:30, replayed as if it’s happening now. Here’s the route and the bus. Start trip mode, lock the phone. There’s the Live Activity on the Lock Screen and in the Dynamic Island, with a countdown to pickup and a progress bar.”  
SAY (this slide): “How does it stay updated with the phone locked? Normally you’d use push notifications, but push needs a paid Apple developer account, which I don’t have. So trip mode keeps the app alive with background location sessions. Every 15 seconds it asks the backend for the trip status and updates the Live Activity itself. It also sends my location after I move 50 metres, or every two minutes, so the server knows my walking time.  
Honest note: the shuttle is simulated, along an illustrative Bengaluru route. Real push is on the production slides at the end.”  

## 18. Time to leave, and Siri tracking

DO: Wait for the “Time to leave” notification (about a minute): “Your shuttle reaches … in N minutes. It’s about a 4-minute walk to …”. Then: “Hey Siri, track my shuttle with Clear Path.”  
SAY (on the phone): “There’s my time-to-leave notification. … And now: ‘Hey Siri, track my shuttle with Clear Path.’”  
SAY (this slide): “Time to leave: the backend compares the minutes until the shuttle reaches my stop with my walking time. When it’s time, trip mode posts a time-sensitive notification, once per trip.  
Siri tracking uses a special kind of intent, a LiveActivityIntent, which is allowed to start a Live Activity straight from Siri. It asks the backend for the status, and Siri reads it out. Still No AI on our side.  
A lesson learned: my first phrase was ‘Where’s my shuttle’, and on iOS 27 Siri often answered that itself without ever calling my app. So the phrase leads with ‘Track my shuttle’.”  
IF IT FAILS (Siri answers itself): “That’s exactly the problem I just described. One more for the count.” Use Type to Siri.  

## 19. The model chooses. Tools act.

SAY: “Before the next step, how the cloud agent works, because this is the first time we use it.  
Your question goes to Gemini together with a list of tools. The model either answers, or asks to call a tool. LangGraph runs that tool, which is a normal Python function, and gives the result back to the model. That loops, up to 12 steps, until it can answer. Then you get the reply plus a record of what was actually done.  
Three things to remember. Twelve tools: bookings, shuttle status, eligibility, policy search, a trip planner, habits. Facts only ever come from tools.  
A fallback chain: Gemini 3.5 Flash-Lite, then a fresh retry, then 3.1 Flash-Lite, 8 seconds each. I chose Flash-Lite by measuring: the older model took 20 to 47 seconds under load, this one takes one to two.  
And memory: every conversation is saved in Postgres, so follow-ups like ‘make it earlier’ work.”  

## 20. “Should I leave now?” through Siri

DO: “Hey Siri, ask Clear Path.” Siri: “What would you like Clear Path to do?” → “Should I leave now?” → yes or no, plus the weather.  
SAY (on the phone): “Now the agent, through Siri. … A yes or no, and it mentioned the weather.”  
SAY (this slide): “The Ask Clear Path intent first offers the request to the on-device assistant. ‘Should I leave now’ is a question, so it goes to the cloud agent.  
The agent called the shuttle-status tool. An important detail: whether I should leave now is computed in code, not by the model. My evals caught the model saying ‘Yes, leave now’ with 11 minutes to spare. Arithmetic belongs in code.  
The agent also called a weather tool, and that tool comes from an MCP server I wrote, using the free Open-Meteo API. The backend starts it at launch and hands its tools to the agent; it’s recorded as ‘via weather MCP server’. This is the first Cloud AI badge today.”  
IF IT FAILS: “Free-tier Gemini can be slow or rate-limited. Each attempt gets 8 seconds, then the next model; if all fail, it says honestly the assistant is unavailable and that bookings still work.” Count it.  

## 21. Delay → Rebook, from the notification

DO (within about 8 minutes of starting the trip): python -m scripts.demo_trip --delay 20. Lock Screen: “20 min late”, orange bar. Notification: “…running 20 minutes late. The 7:45 AM shuttle still gets you to Office by 8:30 AM, 5 minutes sooner. Rebook?” → long-press → Rebook → “Rebooked”.  
SAY (on the phone): “Now something goes wrong in the real world: my shuttle is 20 minutes late. The Live Activity turns orange. And a notification offers me the 7:45, which gets me there 5 minutes sooner. Long-press, Rebook. Rebooked, without opening the app.”  
SAY (this slide): “Trip mode noticed the delay grow by 5 minutes or more. The backend’s trip planner looked for a shuttle I can still catch, more than my walk plus 5 minutes away, that arrives sooner than the delayed one. The delayed 7:30 now arrives 8:35; the 7:45 arrives 8:30. Rebook moves the booking in the background. Keep just dismisses it.  
Badge: No AI. It’s arithmetic over a timetable.”  
IF IT FAILS (no Rebook button): “No faster shuttle could still be caught, because I started the delay late. That’s correct behaviour, not a bug.”  

## 22. One conversation: Siri and the app

DO: Open the app → Ask Clear Path. The Siri question is there with “Checked the weather · via weather MCP server”.  
SAY (on the phone): “Now I open the chat in the app. The question I asked Siri is already here, with the action row: checked the weather, via weather MCP server.”  
SAY (this slide): “Siri and the chat share one conversation. The phone keeps a conversation id that lasts 30 minutes after the last message, so one commute stays one conversation.  
On the backend, LangGraph saves every conversation in Postgres, keyed by my user id and the conversation id, so one user can never read another’s. That’s also why follow-ups work.  
By design, after 30 idle minutes a fresh conversation starts.”  

## 23. Chat, used on purpose

SAY: “Act 3: chat, used on purpose. I’m on the shuttle and I open the app. The chat is for things that genuinely need a conversation: explanations, goals, unusual requests.  
But even here, simple requests don’t need the cloud. Four steps.”  

## 24. Simple requests stay on the phone

DO: Ask Clear Path → “What do I have booked?” → label “On device · Apple Intelligence”. Then “Move Monday earlier” → Monday 7:15 → 7:00, also on device.  
SAY (on the phone): “Look at the label: ‘On device, Apple Intelligence’. That answer never left the phone. ‘Move Monday earlier’: 7:15 to 7:00, also on device.”  
SAY (this slide): “How do we decide what stays on the phone? Three checks.  
First, a rules gate in plain code: short, no digits, no question words like why or should, exactly one action like book, earlier, later or cancel, and a named day for any change.  
Second, Apple’s on-device model classifies the request into an action and a day, within 3 seconds.  
Third, the model must agree with what the rules read from the words. Any disagreement, error or timeout, and it goes to the cloud. So the model can decline, but it can never pick a different action.  
Then it calls the same plain endpoints Siri uses, and records the turn in the conversation so the cloud agent has the context later. Faster, free, private, and as you’ll see in Act 5, it keeps working when the cloud is down.”  
IF IT FAILS (no label): “The on-device model declined or disagreed, so the cloud answered. That’s the safety design working.”  

## 25. A spoken question, a cited answer

DO: Tap the mic → “Why can’t I book Saturday?” → tap stop. Reply: the rule plus a cited Booking Policy passage.  
SAY (on the phone): “Now by voice. … I get the rule, and a citation from the Booking Policy.”  
SAY (this slide): “Two badges here. The voice part is on device: iOS’s SpeechAnalyzer turns speech into text on the phone, tuned for words like ‘Clear Path’ and ‘shuttle’.  
Then the cloud agent. First it calls an eligibility tool, which returns the real rule from the booking service. Then it searches the policies. That’s RAG. Our four policy documents are split into 16 sections. Each section was turned into a list of 384 numbers, an embedding, by a small model on my laptop, and stored in Postgres with pgvector. My question is embedded the same way and compared.  
Anything below 0.60 similarity is treated as noise. Only the top match is cited, and only if it scores 0.70 or more. So the rule comes from code, the explanation from the documents, and the citation shows where.”  
IF IT FAILS: “If nothing is close enough, there’s no citation and the agent says it doesn’t know.” If the mic is unavailable, type the question.  

## 26. The model reads. The planner decides.

DO 1: “I have a meeting at 8 tomorrow, get me there in time.” → “Booked your trip plan”: 7:45 → 7:15, arriving 8:00.  
DO 2: “Get me to the office by 7:30 on Friday.” → “No shuttle gets you there by 7:30 AM. The soonest is the 7:00 AM, arriving 7:45 AM (15 minutes late).” Nothing booked.  
SAY (on the phone): “Now a goal instead of a time. ‘I have a meeting at 8 tomorrow, get me there in time.’ It moved me from the 7:45 to the 7:15, which arrives at 8:00. Now an impossible one: ‘by 7:30 on Friday’. No shuttle gets me there, the soonest arrives 7:45, and it books nothing.”  
SAY (this slide): “That honest no is the point of this slide. The model only reads: it turns my sentence into a date and an arrive-by time. A deterministic trip planner, plain Python over the timetable and the rules, picks the shuttle.  
Why? Before the planner existed, the agent did the time arithmetic itself, and in my evals it booked a shuttle for an impossible goal and claimed it would arrive on time. Goal cases scored 4 out of 9. After moving the decision into code: 9 out of 9. Let the model understand; let code decide.”  
IF IT FAILS: “If no shuttle meets the goal, it offers the soonest option and books nothing without my OK.”  

## 27. At the desk

SAY: “Act 4: at the desk. I’m on my laptop and I use Claude Desktop for work. I shouldn’t have to pick up my phone to book a shuttle.  
So another company’s AI is going to book it, under my rules.”  
DO: switch to Claude Desktop.  

## 28. MCP, in both directions

DO: Claude Desktop: “Book my usual shuttle for Friday” → allow the tool → booked → refresh the iPhone app: Friday is there. “What’s my usual Thursday?” → 8:00 with its reason. “Book Saturday too” → “Shuttles don’t run on Saturdays.”  
SAY (on the laptop): “Claude asked permission to use my tool, booked Friday, and it’s already on my phone. It knows my usual Thursday and why. And Saturday is refused, by my rules, not Claude’s.”  
SAY (this slide): “This is MCP, the Model Context Protocol, used in both directions.  
In: my backend publishes an MCP server with 13 tools, the same 12 my agent uses plus one for today’s date. Claude Desktop launches it locally. Because those tools call the same services, a completely different AI from a different company is held to exactly the same booking rules. Each tool is also labelled read-only or changing, and cancel is labelled destructive, so clients can ask before using it.  
Out: my own agent is an MCP client. The weather tool from the Siri question comes from a small MCP server I wrote.  
My app is a tool for any AI, and my agent can use any tool.”  
IF IT FAILS: “If the weather server doesn’t start, the agent simply runs without weather.”  

## 29. Breaking it on purpose

SAY: “Act 5: breaking it on purpose. A feature isn’t done until you know how it fails.  
Two attacks: a document with hidden instructions for the AI, and the cloud AI going completely down. Watch what keeps working.”  

## 30. Instructions hidden in a document

DO: Photos → the injection version of the schedule → Share → Clear Path. Orange warning: “Ignored 1 line that looked like instructions to an AI”; only the real days are proposed. Close without applying.  
SAY (on the phone): “This schedule has fine print aimed at an AI, the kind of thing someone could hide in a document to make an assistant do something you didn’t ask. Clear Path says ‘Ignored 1 line that looked like instructions to an AI’, shows me the line, and proposes only the real days.”  
SAY (this slide): “Five layers of defence. One: on the phone, lines that look like instructions are removed before any model sees the text. Two: the model is told the document is data, and it has no tools to call anyway. Three: its output can only be typed days. Four: the server accepts only a date and a kind, nothing else; document text never reaches Gemini or any tool. Five: nothing changes until I tap Apply.  
Honest limit: a sneaky line like ‘make Wednesday leave’ looks like data, so layer one can’t catch it. But layers three to five limit the damage to a visible change I can review. That’s defence in depth.”  

## 31. The cloud AI goes down

DO: Second terminal in backend/: python -m scripts.llm_outage on (no restart). Optional: curl localhost:8000/health → "llm": "outage". Chat: “Why can’t I book Saturday?” → unavailable message. Same chat: “Cancel Friday” → On device. Then “Hey Siri, book my usual shuttle for Friday with Clear Path” → booked. Optionally press the Control Center button.  
SAY (live): “Now I’m switching off the cloud AI, simulating the model provider going down. No restart. A question that needs the cloud: ‘Why can’t I book Saturday?’ It says honestly: ‘Clear Path’s assistant is unavailable right now. Bookings still work: say Book my usual shuttle with Clear Path, or use the widget.’ It doesn’t make anything up.  
Same chat: ‘Cancel Friday.’ On device: the Friday Claude booked is cancelled. Siri: ‘Book my usual shuttle for Friday.’ Booked again.”  
SAY (this slide): “How the switch works: a flag file makes the backend hand out stand-in models that fail immediately, like an unreachable provider. The real fallback chain still runs all three attempts, then returns an honest error. Nothing is faked on the phone.  
Why does most of it keep working? Every OS surface sends structured requests to deterministic services, and simple chat runs on the phone. The AI is an enhancement, not a single point of failure.”  

## 32. Every turn leaves a trace

DO: Langfuse (localhost:3000) → the failed turn: ERROR trace with each attempt. Then a normal turn: model calls, tool spans, timings. Then an on-device turn tagged on-device. Then terminal: python -m scripts.llm_outage off, and ask the chat once more to show it’s back.  
SAY: “When an AI answer goes wrong, you need to see why. This is Langfuse, self-hosted in Docker, so nothing leaves my laptop. Here’s the failed turn from a minute ago: marked as an error, with every fallback attempt and the reason. Here’s a normal turn: each model call and tool call, with inputs, outputs and timings. And on-device turns are recorded too, tagged on-device.  
One more rule on this slide: never hide a real change. If the model fails after a booking already changed, the reply still says ‘I made changes to your bookings but couldn’t finish replying. Check your rides to see the latest.’ The worst thing an assistant can do is change your booking and then tell you it failed.  
Now I switch the cloud back on.”  

## 33. What you may have seen, and why

USE ONLY IF something failed by itself earlier; otherwise skip this slide.  
SAY: “Earlier, [what failed]. Here’s what was happening.” Point at the matching row:  
Siri answered by itself: iOS 27 Siri routes with its own model; App Shortcut phrases are a hint, not a guarantee.  
Slow or rate-limited Gemini: free-tier limits; 8 seconds per attempt, three attempts, then an honest error.  
No On-device label: the on-device model must agree with the rules gate, otherwise the cloud answers.  
“I couldn’t reach Clear Path”: the phone and the laptop must be on the same Wi-Fi.  
No Rebook: no faster shuttle could still be caught.  
SAY: “In every case the failure was visible and honest: you knew what happened and what still worked.”  

## 34. Testing and evals are half the work.

SAY: “Act 6: how I know it works. QA folks, this one is for you. Testing and evals are half the work. A demo shows it can work; tests and evals show it keeps working.  
With an LLM you can’t assert an exact sentence. But you can assert which tools it called, what the bookings look like afterwards and which sources it cited, and then have a judge grade the wording. I spent as much effort here as on features.”  

## 35. Three layers of checking

SAY: “Three layers of checking.  
About 150 backend tests, running in around 6 seconds, on a separate test database with a frozen clock and no network. The suite refuses to run unless it’s on the test database.  
76 Swift tests on the iOS side, about 107 cases with their arguments, plus 2 UI tests, covering the API client, on-device routing, schedule import, habits and tracking.  
And 36 eval scenarios that run the real agent with real Gemini calls, on their own isolated database at a fixed date.”  

## 36. Hard checks first, then a judge

SAY: “How one eval works. Setup: for example, I already have a booking on Tuesday, or a trip is running, or shuttles are full. Run: send one or more messages to the real agent.  
Then hard checks, like unit-test assertions: did it call the right tools, did it avoid the wrong ones (for example, never cancelling unasked), are the final bookings exactly what we expect, did it cite the right policy.  
Only then does an AI judge score the reply from 1 to 5 against a rubric and the actual tool results. A 2 or less counts as a hallucination.  
The table shows the 36 cases by area: goals, rules and policies, booking, tracking, follow-ups, habits and safety. There’s also a check mode that fails the run if success drops more than 5 points from the saved baseline.”  

## 37. Gemini 3.5 Flash-Lite, measured

SAY: “The saved baseline: 33 cases on Gemini 3.5 Flash-Lite. 32 of 33 tasks succeeded, and the one failure was actually the judge’s mistake: it read the pickup time as the arrival time.  
100% right tools chosen. Average judge score 4.94 out of 5. Zero hallucination flags. Median reply 5.5 seconds; the slowest 5% took 22.6 seconds, which is the free tier showing. And about $0.0017 per task at list price; on the free tier, nothing.  
Honest note: the dataset has since grown to 36 cases, and a fresh full baseline run is on my list.”  
NOTE: if the full 36-case baseline is saved before the demo, update these numbers and this line.  

## 38. Bugs a demo would never show

SAY: “And this is why evals matter: four real bugs, each caught by an eval, not by trying the app.  
One: the agent did time arithmetic itself and booked impossible trips. The fix was the deterministic planner: 4 of 9 to 9 of 9.  
Two: it invented habit history, saying ‘4 of your last 5’ with no data behind it, because it copied an example from a tool description. Now it may only use the reason the tool returns.  
Three: a question about a colleague using my booking didn’t find the FAQ. I reworded the FAQ and re-indexed it.  
Four: ‘Yes, leave now’ with 11 minutes to spare. Now that’s computed in code.  
And the judge itself got one wrong, which is why hard checks come first and I read every failure myself.”  

## 39. Why don’t we see many apps like this yet?

SAY: “Act 7, the question I promised: why don’t we see many apps like this yet?  
Let’s start with today’s count. How many things failed live?” (Count with the room; recap each in one line.)  
SAY: “My honest answer: the AI calls are a small part of this app. The engineering around them, the rules, fallbacks, evals and honesty, is most of the work, and the platforms themselves are still maturing. Here are the real limits I hit.”  

## 40. Voice assistants are still learning too

SAY: “Siri first. On iOS 27, Siri uses its own model to route requests to apps, so an App Shortcut phrase is a strong hint, not a guarantee. Sometimes it misses, or answers by itself. I tested phrases, used one intent with an optional day because two similar intents confused it, and Type to Siri is the fallback.  
It misheard my app’s name in a dictation test as ‘Clear Footpath’, so that is now literally one of the app’s alternative names.  
It can drop the day from a request, so if no day arrives and tomorrow is a weekend, the app asks which day.  
And ‘Where’s my shuttle’ was intercepted by Siri, so tracking leads with ‘Track my shuttle’.  
None of these are bugs in my code, but a user would blame the app. That’s one big reason these apps are rare.”  

## 41. Models and platforms have edges

SAY: “And the AI and platform edges.  
Apple’s on-device AI isn’t on every iPhone, so there’s always a fallback, and the screen says which one ran.  
No push without a paid account, so trip mode.  
Free-tier limits meant the slowest replies took over 22 seconds, so every call has an 8-second deadline and a fallback chain.  
Once, the model replied with just the name of a tool instead of a sentence, and Siri read it out loud. Now that kind of reply is rejected and the next model is tried.  
The AI judge miscounts sometimes, so hard checks come first.  
And a pure UX one: the first tap on the chat box froze for seconds while iOS loaded the keyboard, so the app quietly warms the keyboard up on Home.  
That’s the real answer: making the AI trustworthy is most of the work.”  

## 42. One backend, many surfaces

SAY: “Now everything you saw, in one picture.  
At the top, the iPhone surfaces, with Apple’s on-device models doing the private work locally: reading schedules, routing simple chat, speech.  
Two paths into the backend. Structured requests, from Siri phrases, buttons, notifications and on-device chat, go straight to REST endpoints with no AI. Open-ended requests go to the LangGraph agent, which uses Gemini to choose among 12 tools.  
Both paths end in the same services, one set of rules: booking, the trip planner, habits and tracking. Underneath, Postgres with pgvector holds the bookings, the agent’s memory and the policy embeddings.  
On the side: MCP in, where Claude Desktop uses the same 13 tools; MCP out, my weather server; and Langfuse and evals watching every turn.  
The key design: the rules exist once, and every surface, human or AI, goes through them.”  

## 43. Most of the app needs no LLM at all

SAY: “And all the badges in one table. Count them.  
Siri booking, widgets, habits, reminders, trip mode and alerts: no AI at all. Schedule import, simple chat and voice: on the phone. Only the genuinely open-ended questions, ‘should I leave now’, ‘why can’t I’, ‘get me there by 8’, go to the cloud, and even there, deterministic tools make the decisions.  
That’s what ‘AI only where it earns its place’ means in practice, and it’s exactly why the app kept working when I switched the cloud AI off.”  

## 44. Three lessons from building it

SAY: “What did I learn? Three lessons.  
One: the LLM does less than you think. Its best job is turning language into a structured request. Then code should decide.  
Two: evals find what demos hide. The agent’s worst bugs, booking impossible trips and inventing habit history, came from evals, not from clicking around.  
Three: honest failure is a feature. Users forgive ‘unavailable’. They don’t forgive a wrong booking.  
What carried over from mobile was thinking in surfaces and user moments, designing failure states, and testing discipline. And I’m still learning: retrieval quality, evals in CI and running this at real scale are next for me.”  

## 45. Scaling up for the real world

SAY: “Now: scaling up for the real world. This is a demo, built deliberately for one rider, on a laptop, with zero spend. Every shortcut was a choice, not an oversight, and I want to show you I know exactly what changes for production.  
Four areas: users and security, platform and scale, mobile, and AI quality and cost. Each slide has three columns: what it is today and why, what production needs, and how I’d get there.”  

## 46. Users and security

SAY: “Users and security.  
Today every request says ‘user 1’, on purpose, to keep the demo about the AI. In production the user must come from a verified token, Sign in with Apple or the company’s single sign-on, never from the request body, with a tenant per company for its own routes and rules.  
Today the phone talks plain HTTP to my laptop. Production needs HTTPS, an API gateway with rate limits, and secrets in a secrets manager.  
The MCP server runs locally as user 1. For real users it becomes a remote server with OAuth, per-user permissions and an audit log.  
And location and commute habits are personal data: consent, retention limits, deletion on request, and India’s Digital Personal Data Protection Act.”  

## 47. Platform and scale

SAY: “Platform and scale.  
The backend runs on my laptop. Production means containers on a managed platform with autoscaling, and separate staging and production.  
Today tables are created at startup and I have demo reset scripts. Production needs versioned migrations, for example Alembic, backups, and managed Postgres with pgvector.  
The agent’s tools share one database session behind a lock: fine for one rider. Many users need a session per request, async I/O, a job queue for slow work, idempotency keys so a retried booking never doubles, and caching.  
And the shuttle is simulated. A real fleet means vehicle GPS or a transit feed, road-snapped routes and a proper arrival-time model.”  

## 48. Mobile

SAY: “Mobile.  
With a paid developer account, delay and time-to-leave alerts come from the server through push, and Live Activities can be started and updated by push: far better for battery than keeping the app awake with location. Trip mode stays as a fallback.  
For Siri: more App Intents and App Entities so Siri understands more of the app, Smart Stack relevance so the widget appears at the right moment, and more Shortcuts actions.  
On-device AI only works where Apple Intelligence runs, so the fallbacks stay, and I’d measure the on-device model on real iPhones, which I couldn’t do on my Mac.  
And reach: Indian languages for speech and search, an accessibility review, and Android on the same backend, which is straightforward because all the rules live on the server.”  

## 49. AI quality and cost

SAY: “AI quality and cost.  
Today: free-tier Flash-Lite with fallbacks inside one provider. Production: a paid tier with a service-level agreement, fallback across providers, say Gemini, Claude or OpenAI behind one interface, and every model choice made by running the same evals.  
Retrieval: 16 sections is fine for a demo. A real knowledge base needs an ingestion pipeline, hybrid keyword and vector search, a reranker, and evals for retrieval itself.  
Evals are run by hand today because I chose no CI. In production they gate every prompt or model change, run nightly, and real failing conversations from traces become new test cases.  
Monitoring: dashboards and alerts for latency, cost and errors, plus crash reporting in the app.  
And safety: the injection defence I showed you, applied to all outside text, with confirmation for actions that change things.”  

## 50. cost

SAY: “What would it cost? This is an estimate, not a measurement. The eval baseline puts one AI task at about $0.0017 at list price. A thousand riders making four AI requests a day comes to about $7 a day.  
And remember most of the app never calls the LLM: Siri phrases, widgets, notifications, trip mode and on-device chat cost nothing per request.  
So ‘AI only where it earns its place’ isn’t only a reliability decision. It’s a cost decision too.”  

## 51. Now, next, later

SAY: “The roadmap.  
Now: teach the on-device router more requests, like ‘book the 7:15 on Friday’, and save a fresh full 36-case eval baseline.  
Next: push notifications and push-updated Live Activities, Smart Stack relevance, and evals running automatically on every change.  
Later: the production items from the last few slides: sign-in and many riders, real transit data, fallback across model providers, and proper evals for the on-device model.”  

## 52. A pattern for any client app

SAY: “So what does this mean for us at BUsoft? This isn’t really about shuttles. The same four steps apply to any client app we build.  
One: expose the app’s real actions as structured things: App Intents, widgets, notifications.  
Two: add AI only where it earns its place; on device when it can, cloud when it must.  
Three: make evals part of QA from day one, hard checks first, then a judge.  
Four: design how each AI feature fails before it ships, and say honestly what broke and what still works.  
Banking, retail, healthcare, logistics: the domain changes, the pattern doesn’t. And every role in this room owns a piece of it: devs, QA, BAs and managers.”  

## 53. “The AI isn’t a chat box inside the app. It works through the parts of iOS people already use.”

SAY (slowly, then pause): “The AI isn’t a chat box inside the app. It works through the parts of iOS people already use. That’s the agentic era, and it’s still being engineered.”  
SAY: “Thank you.”  

## 54. Questions?

SAY: “I’m happy to take questions, and I can show any part again live.”  
PREPARED ANSWERS:  
Why Gemini? Free tier and measured latency; in production the evals would decide between providers.  
Why not just a chatbot? Most commute actions are structured; a button or a Siri phrase is faster and can’t hallucinate.  
What did it cost? Nothing in money: free-tier Gemini, self-hosted tools, no paid accounts.  
Could it work on Android? Yes. All rules live on the backend; the OS surfaces would be rebuilt natively.  
How do you stop prompt injection? Five layers (go back to the injection slide).  
What if Siri doesn’t understand? Type to Siri, the widget, or the app; every surface reaches the same rules.  
How do you test something non-deterministic? Hard checks on tools, bookings and sources first, then a judge for wording (go back to the eval slide).  
