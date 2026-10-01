//
//  BookMyUsualShuttleIntent.swift
//  AIShuttle
//

import AppIntents
import Foundation

public struct BookMyUsualShuttleIntent: AppIntent {
    public static var title: LocalizedStringResource = "Book My Usual Shuttle"
    public static var description = IntentDescription("Books your usual shuttle for tomorrow.")

    private let apiClient: BookingAPIClient

    public init() {
        self.apiClient = BookingAPIClient()
    }

    public init(apiClient: BookingAPIClient) {
        self.apiClient = apiClient
    }

    public func perform() async throws -> some IntentResult & ProvidesDialog {
        do {
            let response = try await apiClient.bookUsualShuttle(
                userId: 1,
                message: "Book my usual shuttle for tomorrow."
            )
            return .result(dialog: IntentDialog(stringLiteral: response.message))
        } catch {
            throw BookingIntentError.bookingFailed
        }
    }
}

public enum BookingIntentError: Error, CustomLocalizedStringResourceConvertible {
    case bookingFailed

    public var localizedStringResource: LocalizedStringResource {
        switch self {
        case .bookingFailed:
            return "Sorry, I couldn't book your shuttle right now."
        }
    }
}
