//
//  HabitDTOs.swift
//  AIShuttle
//
//  Learned commute habits (F10): the usual shuttle per weekday and why,
//  and the next days the rider usually rides. Compiled into the app and
//  both extensions.
//

import Foundation
import UserNotifications

nonisolated public enum HabitSourceDTO: String, Codable, Sendable {
    /// The rider pinned this shuttle; it beats the learned habit.
    case pinned
    /// Learned from recent rides on this weekday.
    case weekday
    /// Learned from recent rides on any day.
    case overall
    /// No habit yet: the saved usual.
    case `default`
}

nonisolated public struct HabitDayDTO: Codable, Equatable, Hashable, Sendable {
    public let weekday: String
    public let shuttleId: Int
    public let departure: String
    public let arrival: String
    public let source: HabitSourceDTO
    /// "you took it on 4 of your last 5 Mondays"
    public let reason: String
    public let rides: Int
    public let sample: Int
    /// Rides this weekday often enough that a missing booking is worth a
    /// reminder.
    public let regular: Bool

    enum CodingKeys: String, CodingKey {
        case weekday
        case shuttleId = "shuttle_id"
        case departure, arrival, source, reason, rides, sample, regular
    }

    public var formattedDeparture: String { BookingDetailDTO.formatTime(departure) }
    public var formattedArrival: String { BookingDetailDTO.formatTime(arrival) }
    public var isLearned: Bool { source == .weekday || source == .overall }
}

nonisolated public struct UpcomingHabitDayDTO: Codable, Equatable, Hashable, Sendable, Identifiable {
    public let date: String
    public let weekday: String
    public let booked: Bool
    public let bookedDeparture: String?
    public let habit: HabitDayDTO

    public var id: String { date }

    enum CodingKeys: String, CodingKey {
        case date, weekday, booked
        case bookedDeparture = "booked_departure"
        case habit
    }

    /// Start of that day in the device's calendar.
    public var day: Date? { BookingAPIClient.parseISODay(date) }
}

nonisolated public struct HabitsDTO: Codable, Equatable, Sendable {
    public let pinnedShuttleId: Int?
    /// Monday to Friday.
    public let days: [HabitDayDTO]
    /// Service days from tomorrow, one week ahead.
    public let upcoming: [UpcomingHabitDayDTO]

    enum CodingKeys: String, CodingKey {
        case pinnedShuttleId = "pinned_shuttle_id"
        case days, upcoming
    }

    /// The next day the rider usually rides but hasn't booked.
    public var nextUnbooked: UpcomingHabitDayDTO? {
        upcoming.first { $0.habit.regular && !$0.booked }
    }
}

struct PinUsualRequest: Encodable {
    let userId: Int
    let shuttleId: Int?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case shuttleId = "shuttle_id"
    }

    // Always send shuttle_id, as null to unpin.
    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(userId, forKey: .userId)
        try container.encode(shuttleId, forKey: .shuttleId)
    }
}

extension BookingAPIClient {
    public func fetchHabits(userId: Int = 1) async throws -> HabitsDTO {
        try await get("habits", userId: userId)
    }

    /// Pin a shuttle as the usual on every day, or unpin with nil so the
    /// learned habit takes over again.
    public func pinUsual(shuttleId: Int?, userId: Int = 1) async throws -> HabitsDTO {
        try await post("habits/pin", body: PinUsualRequest(userId: userId, shuttleId: shuttleId))
    }

    nonisolated static func parseISODay(_ text: String) -> Date? {
        HabitReminderID.dayFormatter().date(from: text)
    }
}

/// Identifiers of the "book your usual ride?" reminders, shared so any
/// surface that books a day (including the widget extension) can withdraw
/// that day's pending reminder.
nonisolated public enum HabitReminderID {
    static let prefix = "habit-reminder-"

    public static func forDay(_ date: Date) -> String {
        prefix + dayFormatter().string(from: date)
    }

    /// `yyyy-MM-dd` in the device's calendar, as BookingAPIClient.isoDay.
    static func dayFormatter() -> DateFormatter {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }

    public static func withdraw(for date: Date) {
        UNUserNotificationCenter.current()
            .removePendingNotificationRequests(withIdentifiers: [forDay(date)])
    }
}
