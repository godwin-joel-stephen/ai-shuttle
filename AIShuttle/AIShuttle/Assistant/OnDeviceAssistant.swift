//
//  OnDeviceAssistant.swift
//  AIShuttle
//
//  F14 on-device routing: simple chat requests ("Book my usual shuttle for
//  Thursday", "Move Friday earlier", "Cancel Monday", "What do I have
//  booked?") are understood by Apple's on-device model and carried out
//  through the structured endpoints, so they are fast, private and keep
//  working when the cloud LLM is down. Everything else goes to the cloud
//  agent, which keeps the showcases that need it (policy answers with
//  citations, weather via MCP, goal planning, follow-ups like "make it
//  earlier").
//
//  Three layers, so a wrong guess never does the wrong thing:
//  1. `OnDeviceGate` (rules) passes only short, single-action requests
//     that name at most one day and nothing the cloud agent is needed for
//     (times, goals, "why", weather, pronouns, negations).
//  2. The on-device model classifies the request (guided generation).
//  3. The classification must agree with the words in the message (the
//     action keyword and the day); otherwise the request goes to the cloud.
//

import Foundation
import FoundationModels
import OSLog

// MARK: - Requests the phone can handle

enum OnDeviceRequest: Equatable {
    case bookUsual(BookingDay)
    case move(BookingDay, RescheduleDirectionDTO)
    case cancel(BookingDay)
    /// Upcoming bookings, optionally only on one day ("Am I booked Friday?").
    case listBookings(BookingDay?)
}

/// The on-device model's reading of a message, before verification.
nonisolated struct OnDeviceClassification: Equatable, Sendable {
    enum Kind: String, Sendable {
        case bookUsual, moveEarlier, moveLater, cancel, listBookings, other
    }

    var kind: Kind
    /// A `BookingDay` raw value, or nil when the message names no day.
    var day: String?
}

nonisolated protocol OnDeviceClassifier: Sendable {
    func classify(_ message: String) async throws -> OnDeviceClassification
}

// MARK: - Rules: what may be tried on device at all

enum OnDeviceGate {
    /// Words that mean the request needs the cloud agent: questions about
    /// rules or conditions, goals and times, references to earlier turns,
    /// negations and compound requests.
    static let cloudWords: Set<String> = [
        "why", "how", "when", "where", "what's", "whats", "can", "could", "would",
        "should", "can't", "cant", "don't", "dont", "not", "never", "won't",
        "weather", "rain", "raining", "leave", "plan", "meeting", "need",
        "arrive", "arriving", "arrival", "by", "before", "after", "get",
        "latest", "earliest", "last", "first", "instead", "if",
        "it", "that", "this", "them", "those", "same",
        "and", "also", "then", "too", "next", "week", "weeks",
        "minute", "minutes", "hour", "hours", "policy", "policies", "rules",
    ]

    static let days: [String: BookingDay] = [
        "today": .today, "tomorrow": .tomorrow,
        "monday": .monday, "tuesday": .tuesday, "wednesday": .wednesday,
        "thursday": .thursday, "friday": .friday, "saturday": .saturday, "sunday": .sunday,
    ]

    static let actionWords: [OnDeviceClassification.Kind: Set<String>] = [
        .bookUsual: ["book"],
        .moveEarlier: ["earlier"],
        .moveLater: ["later"],
        .cancel: ["cancel"],
        .listBookings: ["booked", "bookings", "rides", "upcoming"],
    ]

    struct Screened: Equatable {
        /// The one action the message's words point to.
        let kind: OnDeviceClassification.Kind
        /// The one day the message names, if any.
        let day: BookingDay?
    }

    /// nil means "send it to the cloud agent".
    static func screen(_ message: String) -> Screened? {
        let text = message.lowercased().replacingOccurrences(of: "’", with: "'")
        guard text.count <= 100 else { return nil }

        let words = text
            .split(whereSeparator: { !($0.isLetter || $0.isNumber || $0 == "'") })
            .map { String($0).trimmingCharacters(in: CharacterSet(charactersIn: "'")) }
            .filter { !$0.isEmpty }
        guard !words.isEmpty, words.count <= 14 else { return nil }

        // Any number is a time, a duration or a date: the cloud's job.
        if words.contains(where: { $0.contains(where: \.isNumber) }) { return nil }
        if words.contains(where: cloudWords.contains) { return nil }

        let namedDays = Set(words.compactMap { days[$0] })
        guard namedDays.count <= 1 else { return nil }
        let day = namedDays.first

        let kinds = actionWords.filter { _, keywords in words.contains(where: keywords.contains) }.map(\.key)
        guard kinds.count == 1, let kind = kinds.first else { return nil }

        // Changing a booking needs a day; without one, "it" lives in the
        // conversation, which only the cloud agent sees.
        if kind != .listBookings && day == nil { return nil }

        return Screened(kind: kind, day: day)
    }

    /// The model's reading, accepted only if it matches the words.
    static func verify(_ classification: OnDeviceClassification, against screened: Screened) -> OnDeviceRequest? {
        guard classification.kind == screened.kind,
              classification.day == screened.day?.rawValue else { return nil }

        switch (classification.kind, screened.day) {
        case (.bookUsual, let day?): return .bookUsual(day)
        case (.moveEarlier, let day?): return .move(day, .earlier)
        case (.moveLater, let day?): return .move(day, .later)
        case (.cancel, let day?): return .cancel(day)
        case (.listBookings, let day): return .listBookings(day)
        default: return nil
        }
    }
}

// MARK: - Apple Foundation Models classifier

@Generable(description: "What a shuttle rider's chat message asks the app to do")
nonisolated struct GeneratedChatRequest {
    @Guide(description: "The single action the message asks for")
    var kind: GeneratedRequestKind
    @Guide(description: "The day named in the message, or none if it names no day")
    var day: GeneratedRequestDay
}

@Generable
nonisolated enum GeneratedRequestKind: String {
    case bookUsual, moveEarlier, moveLater, cancel, listBookings, other
}

@Generable
nonisolated enum GeneratedRequestDay: String {
    case none, today, tomorrow, monday, tuesday, wednesday, thursday, friday, saturday, sunday
}

nonisolated struct FoundationModelsClassifier: OnDeviceClassifier {
    static let instructions = """
    You read one message from a commuter to their shuttle booking app and \
    say which single action it asks for.
    - bookUsual: book their usual shuttle on a day.
    - moveEarlier / moveLater: move an existing booking on a day to an \
    earlier or later shuttle.
    - cancel: cancel the booking on a day.
    - listBookings: asks what they have booked.
    - other: anything else, including questions, several actions, or \
    anything you are unsure about.
    Report the day exactly as the message names it; use none if it names no day.
    """

    static var isAvailable: Bool {
        let model = SystemLanguageModel.default
        return model.availability == .available && model.supportsLocale()
    }

    /// Loads the model before the first request, e.g. when the chat opens.
    static func prewarm() {
        guard isAvailable else { return }
        LanguageModelSession(instructions: instructions).prewarm()
    }

    func classify(_ message: String) async throws -> OnDeviceClassification {
        // A fresh session per message: no earlier turn can sway it.
        let session = LanguageModelSession(instructions: Self.instructions)
        let response = try await session.respond(
            to: "Message: \(message)",
            generating: GeneratedChatRequest.self,
            options: GenerationOptions(sampling: .greedy)
        )
        let generated = response.content
        return OnDeviceClassification(
            kind: OnDeviceClassification.Kind(rawValue: generated.kind.rawValue) ?? .other,
            day: generated.day == .none ? nil : generated.day.rawValue
        )
    }
}

// MARK: - Router

/// A request answered on the phone.
struct OnDeviceAnswer: Equatable, Sendable {
    let reply: String
    let actions: [AssistantActionDTO]
    let bookingsChanged: Bool
    /// The day a booking was made, so its evening reminder can be withdrawn.
    var bookedDate: Date?
}

struct OnDeviceAssistant: Sendable {
    let classifier: any OnDeviceClassifier
    let apiClient: BookingAPIClient
    /// The model gets this long; a slow answer goes to the cloud instead.
    var deadline: Duration = .seconds(3)
    var now: @Sendable () -> Date = { .now }

    /// nil when Apple Intelligence can't be used on this device.
    static func live(apiClient: BookingAPIClient = .withTimeouts()) -> OnDeviceAssistant? {
        guard FoundationModelsClassifier.isAvailable else { return nil }
        return OnDeviceAssistant(classifier: FoundationModelsClassifier(), apiClient: apiClient)
    }

    /// nil means "not handled here": send the message to the cloud agent.
    func answer(_ message: String) async -> OnDeviceAnswer? {
        guard let screened = OnDeviceGate.screen(message) else { return nil }

        let classification: OnDeviceClassification
        do {
            classification = try await classifyWithinDeadline(message)
        } catch {
            Logger.onDevice.info("On-device model failed, using the cloud: \(String(describing: error), privacy: .public)")
            return nil
        }

        guard let request = OnDeviceGate.verify(classification, against: screened) else {
            Logger.onDevice.info("On-device reading \(classification.kind.rawValue, privacy: .public)/\(classification.day ?? "none", privacy: .public) didn't match the message; using the cloud")
            return nil
        }

        do {
            return try await perform(request)
        } catch BookingAPIError.serverMessage(_, let message) {
            // A booking rule said no ("Shuttles don't run on Saturdays"):
            // that is the answer, and the cloud would say the same.
            return OnDeviceAnswer(
                reply: message,
                actions: [Self.action(for: request, succeeded: false, error: message)],
                bookingsChanged: false
            )
        } catch {
            // Network trouble: let the cloud path report it.
            return nil
        }
    }

    private func classifyWithinDeadline(_ message: String) async throws -> OnDeviceClassification {
        try await withThrowingTaskGroup(of: OnDeviceClassification.self) { group in
            group.addTask { try await classifier.classify(message) }
            group.addTask {
                try await Task.sleep(for: deadline)
                throw CancellationError()
            }
            defer { group.cancelAll() }
            return try await group.next()!
        }
    }

    private func perform(_ request: OnDeviceRequest) async throws -> OnDeviceAnswer {
        switch request {
        case .bookUsual(let day):
            let date = day.date(from: now())
            let response = try await apiClient.bookUsualShuttle(userId: 1, on: date)
            return OnDeviceAnswer(
                reply: response.spokenConfirmation,
                actions: [Self.action(for: request)],
                bookingsChanged: !response.alreadyBooked,
                bookedDate: date
            )

        case .move(let day, let direction):
            guard let booking = try await booking(on: day) else {
                return noBooking(on: day, request)
            }
            let response = try await apiClient.rescheduleBooking(id: booking.id, direction: direction)
            return OnDeviceAnswer(reply: response.message, actions: [Self.action(for: request)], bookingsChanged: true)

        case .cancel(let day):
            guard let booking = try await booking(on: day) else {
                return noBooking(on: day, request)
            }
            let response = try await apiClient.cancelBooking(id: booking.id)
            return OnDeviceAnswer(reply: response.message, actions: [Self.action(for: request)], bookingsChanged: true)

        case .listBookings(let day):
            var bookings = try await apiClient.fetchUpcomingBookings().filter { $0.status == "confirmed" }
            if let day {
                let iso = BookingAPIClient.isoDay(day.date(from: now()))
                bookings = bookings.filter { $0.bookingDate == iso }
            }
            return OnDeviceAnswer(reply: Self.describe(bookings, on: day), actions: [Self.action(for: request)], bookingsChanged: false)
        }
    }

    private func booking(on day: BookingDay) async throws -> BookingDetailDTO? {
        let iso = BookingAPIClient.isoDay(day.date(from: now()))
        return try await apiClient.fetchUpcomingBookings()
            .first { $0.bookingDate == iso && $0.status == "confirmed" }
    }

    private func noBooking(on day: BookingDay, _ request: OnDeviceRequest) -> OnDeviceAnswer {
        let reply = "You don't have a shuttle booked \(Self.spoken(day))."
        return OnDeviceAnswer(reply: reply, actions: [Self.action(for: request, succeeded: false, error: reply)], bookingsChanged: false)
    }

    static func describe(_ bookings: [BookingDetailDTO], on day: BookingDay?) -> String {
        guard !bookings.isEmpty else {
            return day.map { "You don't have a shuttle booked \(spoken($0))." } ?? "You don't have any shuttles booked."
        }
        let rides = bookings.map { "the \($0.formattedPickupTime) \($0.spokenDay)" }
        if rides.count == 1 {
            return "You're booked on \(rides[0])."
        }
        return "You're booked on \(rides.dropLast().joined(separator: ", ")) and \(rides.last!)."
    }

    static func spoken(_ day: BookingDay) -> String {
        switch day {
        case .today, .tomorrow: day.rawValue
        default: "on \(day.rawValue.capitalized)"
        }
    }

    /// Named like the cloud agent's tools, so the chat labels them the same.
    static func action(for request: OnDeviceRequest, succeeded: Bool = true, error: String? = nil) -> AssistantActionDTO {
        let tool = switch request {
        case .bookUsual: "book_usual_shuttle"
        case .move: "change_booking_shuttle"
        case .cancel: "cancel_booking"
        case .listBookings: "get_my_bookings"
        }
        return AssistantActionDTO(tool: tool, succeeded: succeeded, error: error, server: nil)
    }
}

extension Logger {
    nonisolated static let onDevice = Logger(subsystem: "com.yourcompany.AIShuttle", category: "OnDevice")
}
