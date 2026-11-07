//
//  BookMyUsualShuttleIntent.swift
//  AIShuttle
//

import AppIntents
import Foundation
import WidgetKit

public struct BookMyUsualShuttleIntent: AppIntent {
    public static var title: LocalizedStringResource = "Book My Usual Shuttle"

    // Siri's language model reads this metadata when deciding whether a
    // request belongs to this app, so describe the action plainly.
    public static var description = IntentDescription(
        "Books a seat on your usual Clear Path commuter shuttle from Home to Office for a given day, such as tomorrow or Friday. Books tomorrow when no day is given.",
        categoryName: "Shuttle Booking",
        searchKeywords: ["shuttle", "book shuttle", "usual shuttle", "commute", "office shuttle", "Clear Path"]
    )

    // One intent rather than separate "tomorrow" and "for a day" intents:
    // with two near-identical phrase sets, Siri on iOS 27 picked the
    // tomorrow intent even for an exactly typed "...for Friday..." phrase.
    // No default either, so a missing day stays visible as nil; the dialog
    // and card always name the day that was booked.
    @Parameter(title: "Day")
    public var day: BookingDay?

    public static var parameterSummary: some ParameterSummary {
        Summary("Book my usual shuttle for \(\.$day)")
    }

    private let apiClient: BookingAPIClient

    public init() {
        self.apiClient = .withTimeouts()
    }

    public init(day: BookingDay? = nil, apiClient: BookingAPIClient) {
        self.apiClient = apiClient
        self.day = day
    }

    public func perform() async throws -> some IntentResult & ProvidesDialog & ShowsSnippetIntent {
        let booked = try await ShuttleBooking.book(on: (day ?? .tomorrow).date(), using: apiClient)
        return .result(dialog: booked.dialog, snippetIntent: booked.snippet)
    }
}

enum ShuttleBooking {
    struct Booked {
        let dialog: IntentDialog
        let snippet: BookingSnippetIntent
    }

    /// The intent and day are already known, so send a structured request
    /// and let the backend skip the LLM.
    static func book(on date: Date, using apiClient: BookingAPIClient) async throws -> Booked {
        let response: BookingResponse
        do {
            response = try await apiClient.bookUsualShuttle(userId: 1, on: date)
        } catch {
            throw BookingIntentError(error)
        }

        WidgetCenter.shared.reloadAllTimelines()
        HabitReminderID.withdraw(for: date)

        return Booked(
            dialog: IntentDialog(stringLiteral: response.spokenConfirmation),
            snippet: BookingSnippetIntent(bookingId: response.bookingId)
        )
    }
}
