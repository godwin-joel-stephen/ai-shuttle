//
//  BookTomorrowIntent.swift
//  AIShuttle
//
//  One-tap booking for the widget button, the Control Center control and
//  the Action button. Compiled into both the app and the widget extension,
//  because interactive widgets and controls run their intent in-extension.
//

import AppIntents
import Foundation
import WidgetKit

struct BookTomorrowIntent: AppIntent {
    static var title: LocalizedStringResource = "Book Tomorrow's Shuttle"
    static var description = IntentDescription("Books your usual Clear Path shuttle for tomorrow with one tap.")
    static var isDiscoverable = false

    init() {}

    func perform() async throws -> some IntentResult {
        let tomorrow = Calendar.current.date(byAdding: .day, value: 1, to: .now)!

        do {
            let response = try await BookingAPIClient.withTimeouts().bookUsualShuttle(userId: 1, on: tomorrow)
            WidgetCenter.shared.reloadAllTimelines()
            await BookingNotifier.post(
                title: response.alreadyBooked ? "Already booked" : "Shuttle booked",
                body: response.spokenConfirmation
            )
        } catch {
            let failure = BookingIntentError(error)
            await BookingNotifier.post(
                title: "Booking failed",
                body: String(localized: failure.localizedStringResource)
            )
            throw failure
        }

        return .result()
    }
}
