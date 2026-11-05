//
//  RuleBasedScheduleParser.swift
//  Keyword rules for schedules with one day per line ("Mon 9 Nov | Office").
//
//  Used when Apple Intelligence is unavailable (older iPhone, turned off,
//  model still downloading) or the model fails, so import still works.
//  It is also the baseline the on-device model is measured against in
//  ScheduleImportEvals. It can't read grids (weekdays as column headers)
//  or free prose; the model can.
//

import Foundation

struct RuleBasedScheduleParser {
    let calendar: ScheduleCalendar

    /// Days in document order; dates may repeat or be out of range
    /// (ScheduleExtractor validates).
    func parse(_ text: String) -> [ScheduleDay] {
        var weekStart = calendar.defaultWeekStart
        var days: [ScheduleDay] = []

        for rawLine in text.components(separatedBy: .newlines) {
            let line = rawLine.lowercased()

            // "Week of 9 November" / "w/c 09/11" sets the week for the
            // weekday-only lines that follow.
            if line.contains(Self.weekHeader), let date = explicitDate(in: line, weekday: nil) {
                weekStart = calendar.monday(of: date)
                if weekday(in: line) == nil { continue }
            }

            guard let kind = Self.kind(in: line) else { continue }
            let weekday = weekday(in: line)

            if let date = explicitDate(in: line, weekday: weekday) {
                days.append(ScheduleDay(date: calendar.iso(date), kind: kind))
            } else if let weekday {
                let date = calendar.date(weekday: weekday, inWeekStarting: weekStart)
                days.append(ScheduleDay(date: calendar.iso(date), kind: kind))
            }
        }
        return days
    }

    // MARK: - Kind

    /// Checked in this order: "out of office" is leave, not office;
    /// "offsite at the client office" is offsite.
    static func kind(in line: String) -> WorkdayKind? {
        for (kind, pattern) in kindPatterns where line.contains(pattern) {
            return kind
        }
        return nil
    }

    private static var kindPatterns: [(WorkdayKind, Regex<Substring>)] { [
        (.leave, #/\b(?:holiday|leave|pto|vacation|ooo|out of (?:the )?office|day off|off|sick|closed|annual leave|time off)\b/#),
        (.offsite, #/\b(?:off-?site|client|customer|conference|site visit|travel(?:l?ing)?|training)\b/#),
        (.remote, #/\b(?:wfh|work(?:ing)? from home|home|remote(?:ly)?)\b/#),
        (.office, #/\b(?:office|wfo|in-?office|on-?site|hq|campus|in person)\b/#),
    ] }

    // MARK: - Weekday

    /// 1 = Monday … 7 = Sunday.
    func weekday(in line: String) -> Int? {
        guard let match = line.firstMatch(of: Self.weekdayPattern) else { return nil }
        let prefix = String(match.output.prefix(3))
        return Self.weekdayPrefixes.firstIndex(of: prefix).map { $0 + 1 }
    }

    private static let weekdayPrefixes = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    private static var weekdayPattern: Regex<Substring> {
        #/\b(?:monday|mon|tuesday|tues|tue|wednesday|wed|thursday|thurs|thur|thu|friday|fri|saturday|sat|sunday|sun)\b/#
    }
    private static var weekHeader: Regex<Substring> {
        #/\b(?:week of|week starting|week commencing|w\/c|week beginning)\b/#
    }

    // MARK: - Dates

    private static let months = [
        "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    ]

    /// A date written in the line, as ISO, "9 Nov", "Nov 9" or "9/11".
    /// Numeric dates are ambiguous (day/month vs month/day); the weekday
    /// on the same line decides when there is one.
    func explicitDate(in line: String, weekday: Int?) -> Date? {
        if let match = line.firstMatch(of: #/(\d{4})-(\d{2})-(\d{2})/#) {
            return calendar.date(iso: "\(match.1)-\(match.2)-\(match.3)")
        }
        if let match = line.firstMatch(of: #/\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b/#),
           let day = Int(match.1), let month = Self.months.firstIndex(of: String(match.2)) {
            return nearest(month: month + 1, day: day)
        }
        if let match = line.firstMatch(of: #/\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b/#),
           let day = Int(match.2), let month = Self.months.firstIndex(of: String(match.1)) {
            return nearest(month: month + 1, day: day)
        }
        if let match = line.firstMatch(of: #/\b(\d{1,2})[\/.](\d{1,2})(?:[\/.]\d{2,4})?\b/#),
           let first = Int(match.1), let second = Int(match.2) {
            let candidates = [
                nearest(month: second, day: first),  // day/month (most of the world)
                nearest(month: first, day: second),  // month/day (US)
            ].compactMap { $0 }
            if let weekday {
                return candidates.first { calendar.weekdayNumber($0) == weekday }
            }
            return candidates.first
        }
        return nil
    }

    /// The year that puts month/day closest to today (schedules are about
    /// the next few weeks, sometimes the past few days).
    private func nearest(month: Int, day: Int) -> Date? {
        guard (1...12).contains(month), (1...31).contains(day) else { return nil }
        let year = calendar.calendar.component(.year, from: calendar.today)
        return [year - 1, year, year + 1]
            .compactMap { year -> Date? in
                let components = DateComponents(year: year, month: month, day: day)
                guard let date = calendar.calendar.date(from: components),
                      calendar.calendar.component(.day, from: date) == day else { return nil }
                return date
            }
            .min { abs($0.timeIntervalSince(calendar.today)) < abs($1.timeIntervalSince(calendar.today)) }
    }
}
