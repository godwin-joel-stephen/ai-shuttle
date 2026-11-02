//
//  BookingDay.swift
//  AIShuttle
//

import AppIntents
import Foundation

/// Days Siri can recognise inside a shortcut phrase. App Shortcut phrases
/// only accept enum/entity parameters, so this is how "for Friday" works.
public enum BookingDay: String, AppEnum {
    case today
    case tomorrow
    case monday
    case tuesday
    case wednesday
    case thursday
    case friday
    case saturday
    case sunday

    public static let typeDisplayRepresentation: TypeDisplayRepresentation = "Day"

    public static let caseDisplayRepresentations: [BookingDay: DisplayRepresentation] = [
        .today: DisplayRepresentation(title: "today", synonyms: ["this morning"]),
        .tomorrow: DisplayRepresentation(title: "tomorrow", synonyms: ["tomorrow morning"]),
        .monday: DisplayRepresentation(title: "Monday"),
        .tuesday: DisplayRepresentation(title: "Tuesday"),
        .wednesday: DisplayRepresentation(title: "Wednesday"),
        .thursday: DisplayRepresentation(title: "Thursday"),
        .friday: DisplayRepresentation(title: "Friday"),
        .saturday: DisplayRepresentation(title: "Saturday"),
        .sunday: DisplayRepresentation(title: "Sunday")
    ]

    /// Resolves to a calendar day. Weekdays mean the next occurrence after
    /// today, so "Friday" said on a Friday books next week.
    public func date(from reference: Date = .now, calendar: Calendar = .current) -> Date {
        let startOfToday = calendar.startOfDay(for: reference)

        switch self {
        case .today:
            return startOfToday
        case .tomorrow:
            return calendar.date(byAdding: .day, value: 1, to: startOfToday)!
        default:
            return calendar.nextDate(
                after: startOfToday,
                matching: DateComponents(weekday: weekday),
                matchingPolicy: .nextTime
            )!
        }
    }

    private var weekday: Int? {
        switch self {
        case .sunday: return 1
        case .monday: return 2
        case .tuesday: return 3
        case .wednesday: return 4
        case .thursday: return 5
        case .friday: return 6
        case .saturday: return 7
        case .today, .tomorrow: return nil
        }
    }
}
