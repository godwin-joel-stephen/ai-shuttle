//
//  ScheduleModels.swift
//  Schedule import (F3): shared by the app and the ClearPathShare extension.
//
//  Kept free of UIKit/SwiftUI so the on-device extraction eval
//  (ScheduleImportEvals/) can compile it for macOS.
//

import Foundation

/// Where the rider works on a day. Raw values match the backend.
nonisolated enum WorkdayKind: String, Codable, CaseIterable, Hashable, Sendable {
    case office
    case remote
    case offsite
    case leave

    var label: String {
        switch self {
        case .office: "Office"
        case .remote: "Home"
        case .offsite: "Offsite"
        case .leave: "Off"
        }
    }

    var symbolName: String {
        switch self {
        case .office: "building.2"
        case .remote: "house"
        case .offsite: "mappin.and.ellipse"
        case .leave: "sun.max"
        }
    }
}

/// One typed day: the only thing that leaves the phone.
nonisolated struct ScheduleDay: Codable, Hashable, Sendable {
    /// `yyyy-MM-dd`
    let date: String
    let kind: WorkdayKind
}

nonisolated enum ExtractionMethod: String, Sendable {
    /// Apple Foundation Models, on this device.
    case onDevice
    /// Keyword rules (Apple Intelligence unavailable or the model failed).
    case rules
}

nonisolated struct ScheduleExtraction: Sendable {
    var days: [ScheduleDay]
    var method: ExtractionMethod
    /// Why the keyword rules were used instead of the on-device model.
    var fallbackReason: String?
    /// Lines that read like instructions to an AI; never shown to a model.
    var ignoredLines: [String]
    /// Days before today (already past, nothing to do).
    var pastDays: Int = 0
    /// Entries dropped by validation (bad date, outside the horizon,
    /// date/weekday mismatch, duplicate).
    var discarded: Int = 0
}

/// Dates for schedule import, in the device's time zone.
nonisolated struct ScheduleCalendar: Sendable {
    /// Days ahead a schedule may cover (the server's booking window is
    /// 14 days; later days come back with "opens on …").
    static let horizonDays = 28

    let calendar: Calendar
    let today: Date

    init(today: Date = .now, timeZone: TimeZone = .current) {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = timeZone
        calendar.locale = Locale(identifier: "en_US_POSIX")
        calendar.firstWeekday = 2  // Monday
        self.calendar = calendar
        self.today = calendar.startOfDay(for: today)
    }

    private var isoFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.calendar = calendar
        formatter.timeZone = calendar.timeZone
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }

    func iso(_ date: Date) -> String {
        isoFormatter.string(from: date)
    }

    func date(iso: String) -> Date? {
        guard iso.wholeMatch(of: #/\d{4}-\d{2}-\d{2}/#) != nil,
              let date = isoFormatter.date(from: iso),
              self.iso(date) == iso  // DateFormatter turns Nov 31 into Dec 1
        else { return nil }
        return date
    }

    func adding(days: Int, to date: Date) -> Date {
        calendar.date(byAdding: .day, value: days, to: date)!
    }

    var lastDay: Date { adding(days: Self.horizonDays, to: today) }

    /// Every day from today to the end of the horizon.
    var upcomingDays: [Date] {
        (0...Self.horizonDays).map { adding(days: $0, to: today) }
    }

    /// 1 = Monday … 7 = Sunday.
    func weekdayNumber(_ date: Date) -> Int {
        (calendar.component(.weekday, from: date) + 5) % 7 + 1
    }

    func weekdayName(_ date: Date) -> String {
        Self.weekdayNames[weekdayNumber(date) - 1]
    }

    /// Monday of the week containing `date`.
    func monday(of date: Date) -> Date {
        adding(days: 1 - weekdayNumber(date), to: calendar.startOfDay(for: date))
    }

    /// The week a schedule that names only weekdays is about: this week
    /// when today is Monday, otherwise next week.
    var defaultWeekStart: Date {
        weekdayNumber(today) == 1 ? today : adding(days: 7, to: monday(of: today))
    }

    func date(weekday: Int, inWeekStarting weekStart: Date) -> Date {
        adding(days: weekday - 1, to: weekStart)
    }

    static let weekdayNames = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    ]
}

nonisolated enum ScheduleImportError: Error, LocalizedError, Equatable {
    case unsupportedContent
    case unreadableDocument
    case noText
    case noDays

    var errorDescription: String? {
        switch self {
        case .unsupportedContent:
            "Share a photo, screenshot, PDF or text of your work schedule."
        case .unreadableDocument:
            "Clear Path couldn't open that document."
        case .noText:
            "No text was found. Try a sharper photo of the schedule."
        case .noDays:
            "No office, home, offsite or leave days were found in that schedule."
        }
    }
}
