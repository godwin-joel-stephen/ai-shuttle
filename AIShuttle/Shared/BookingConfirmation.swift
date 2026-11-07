//
//  BookingConfirmation.swift
//  AIShuttle
//
//  Shared by the app (Siri) and the widget extension (widget, Control
//  Center, Action button), so every surface confirms a booking the same way.
//

import AppIntents
import Foundation
import UserNotifications

extension BookingResponse {
    /// "Done. You're on the 7:30 AM shuttle tomorrow, arriving at Office by 8:15 AM."
    public var spokenConfirmation: String {
        guard let booking else {
            return message
        }

        let ride = "the \(booking.formattedPickupTime) shuttle \(booking.spokenDay)"
        let arrival = booking.formattedArrivalTime.map { ", arriving at \(booking.destination ?? "your stop") by \($0)" } ?? ""

        if alreadyBooked {
            return "You're already booked on \(ride)."
        }
        let habit = usualReason.map { " That's your usual: \($0)." } ?? ""
        return "Done. You're on \(ride)\(arrival).\(habit)"
    }
}

public enum BookingIntentError: Error, CustomLocalizedStringResourceConvertible {
    case bookingFailed
    case unreachable
    case rejected(String)

    init(_ error: Error) {
        switch error {
        case BookingAPIError.serverMessage(_, let message):
            self = .rejected(message)
        case BookingAPIError.networkError:
            self = .unreachable
        default:
            self = .bookingFailed
        }
    }

    public var localizedStringResource: LocalizedStringResource {
        switch self {
        case .bookingFailed:
            return "Sorry, I couldn't book your shuttle right now."
        case .unreachable:
            return "I couldn't reach Clear Path. Check your connection and try again."
        case .rejected(let message):
            return "\(message)"
        }
    }
}

/// Controls and widget buttons can't speak or show a dialog, so confirm
/// their result with a notification instead.
enum BookingNotifier {
    static func post(title: String, body: String) async {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "booking-confirmation",
            content: content,
            trigger: nil
        )
        try? await UNUserNotificationCenter.current().add(request)
    }
}
