//
//  HabitSurfaces.swift
//  AIShuttle
//
//  F10: hand the learned commute habit to the OS so it can suggest the
//  booking before the rider asks.
//
//  - Donations: every booking, whatever surface made it (Siri, widget,
//    Control Center, chat, schedule import, Claude Desktop), is donated as
//    "Book my usual shuttle for <weekday>", so Siri Suggestions, Spotlight
//    and the Lock Screen learn when the rider books.
//  - Reminders: a local notification the evening before a day the rider
//    usually rides but hasn't booked, with a Book button that books the
//    usual shuttle without opening the app. No APNs needed.
//

import AppIntents
import Foundation
import UserNotifications

enum HabitDonations {
    private static let donatedKey = "habit.donatedBookingIds"
    private static let remembered = 60

    /// Donates bookings not donated before. Run after the rides list
    /// loads: it's the one place that sees bookings from every surface,
    /// including the widget extension and the backend's own agents.
    static func donateNewBookings(_ bookings: [BookingDetailDTO]) async {
        var donated = UserDefaults.standard.array(forKey: donatedKey) as? [Int] ?? []
        let fresh = bookings.filter { !donated.contains($0.id) }
        guard !fresh.isEmpty else { return }

        for booking in fresh {
            guard let date = BookingAPIClient.parseISODay(booking.bookingDate) else { continue }
            await donate(day: date)
            donated.append(booking.id)
        }
        UserDefaults.standard.set(Array(donated.suffix(remembered)), forKey: donatedKey)
    }

    static func donate(day: Date) async {
        var intent = BookMyUsualShuttleIntent()
        intent.day = BookingDay(weekdayOf: day)
        _ = try? await IntentDonationManager.shared.donate(intent: intent)
    }
}

nonisolated enum HabitReminders {
    static let category = "HABIT_BOOK_REMINDER"
    static let bookAction = "BOOK_USUAL"
    static let dayKey = "habitDay"
    /// The evening before the ride.
    static let reminderHour = 19

    static var notificationCategory: UNNotificationCategory {
        UNNotificationCategory(
            identifier: category,
            actions: [UNNotificationAction(identifier: bookAction, title: "Book", options: [])],
            intentIdentifiers: []
        )
    }

    /// Replaces every pending habit reminder with one per upcoming day the
    /// rider usually rides but hasn't booked.
    static func schedule(_ habits: HabitsDTO, now: Date = .now) async {
        let center = UNUserNotificationCenter.current()
        let stale = await center.pendingNotificationRequests()
            .map(\.identifier)
            .filter { $0.hasPrefix(HabitReminderID.prefix) }
        center.removePendingNotificationRequests(withIdentifiers: stale)

        for day in habits.upcoming where day.habit.regular && !day.booked {
            guard let date = day.day, let fire = reminderDate(before: date), fire > now else { continue }
            let trigger = UNCalendarNotificationTrigger(
                dateMatching: Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: fire),
                repeats: false
            )
            try? await center.add(
                UNNotificationRequest(identifier: HabitReminderID.forDay(date), content: content(for: day), trigger: trigger)
            )
        }
    }

    /// Debug builds: show the reminder for this day in a few seconds.
    static func preview(_ day: UpcomingHabitDayDTO) async {
        try? await UNUserNotificationCenter.current().add(
            UNNotificationRequest(
                identifier: "habit-preview-\(day.date)",
                content: content(for: day),
                trigger: UNTimeIntervalNotificationTrigger(timeInterval: 5, repeats: false)
            )
        )
    }

    static func reminderDate(before day: Date, calendar: Calendar = .current) -> Date? {
        guard let previous = calendar.date(byAdding: .day, value: -1, to: calendar.startOfDay(for: day)) else {
            return nil
        }
        return calendar.date(bySettingHour: reminderHour, minute: 0, second: 0, of: previous)
    }

    /// "Book Monday's shuttle?" / "Your usual Monday shuttle is the
    /// 7:15 AM — you took it on 4 of your last 5 Mondays. Book it?"
    static func content(for day: UpcomingHabitDayDTO) -> UNMutableNotificationContent {
        let habit = day.habit
        let content = UNMutableNotificationContent()
        content.title = "Book \(day.weekday)'s shuttle?"
        content.body = "Your usual \(day.weekday) shuttle is the \(habit.formattedDeparture), "
            + "arriving \(habit.formattedArrival) — \(habit.reason). You haven't booked it yet."
        content.sound = .default
        content.categoryIdentifier = category
        content.userInfo = [dayKey: day.date]
        // Groups with the app's other reminders and helps iOS rank it.
        content.threadIdentifier = "habit-reminders"
        content.relevanceScore = 0.8
        return content
    }

    /// The Book button: books that day's usual without opening the app.
    @MainActor
    static func book(dayText: String) async {
        guard let date = BookingAPIClient.parseISODay(dayText) else { return }
        do {
            let response = try await BookingAPIClient.withTimeouts().bookUsualShuttle(userId: 1, on: date)
            await HabitDonations.donate(day: date)
            await TripNotifications.post(
                id: "habit-booked-\(dayText)",
                title: response.alreadyBooked ? "Already booked" : "Shuttle booked",
                body: response.spokenConfirmation
            )
        } catch {
            await TripNotifications.post(
                id: "habit-failed-\(dayText)",
                title: "Couldn't book",
                body: String(localized: BookingIntentError(error).localizedStringResource)
            )
        }
    }
}
