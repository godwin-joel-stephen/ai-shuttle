//
//  WhereIsMyShuttleIntent.swift
//  AIShuttle
//
//  "Where's my shuttle?": speaks the live status and puts the trip on the
//  Lock Screen and Dynamic Island. LiveActivityIntent lets it start the
//  Live Activity while the app is in the background.
//

import AppIntents
import Foundation

struct WhereIsMyShuttleIntent: LiveActivityIntent {
    static var title: LocalizedStringResource = "Where's My Shuttle"

    static var description = IntentDescription(
        "Tells you where your next Clear Path shuttle is and how long until pickup, and shows it live on your Lock Screen.",
        categoryName: "Tracking",
        searchKeywords: ["where is my shuttle", "track shuttle", "shuttle ETA", "how far", "Clear Path"]
    )

    init() {}

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let trip: TripStatusDTO
        do {
            trip = try await BookingAPIClient.withTimeouts().fetchNextTrip()
        } catch {
            throw BookingIntentError(error)
        }

        await ShuttleActivityController.show(trip)

        return .result(dialog: IntentDialog(stringLiteral: trip.message))
    }
}
