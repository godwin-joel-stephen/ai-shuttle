//
//  TripNotifications.swift
//  AIShuttle
//
//  Local notifications for trip mode, including a delay alert whose
//  Rebook button moves the booking without opening the app.
//

import UIKit
import UserNotifications

nonisolated enum TripNotifications {
    static let delayCategory = "SHUTTLE_DELAY_WITH_ALTERNATIVE"
    static let rebookAction = "REBOOK"
    static let keepAction = "KEEP"

    static func registerCategories() {
        let rebook = UNNotificationAction(identifier: rebookAction, title: "Rebook", options: [])
        let keep = UNNotificationAction(identifier: keepAction, title: "Keep", options: [])
        let delay = UNNotificationCategory(
            identifier: delayCategory,
            actions: [rebook, keep],
            intentIdentifiers: []
        )
        UNUserNotificationCenter.current().setNotificationCategories([delay])
    }

    static func post(
        id: String,
        title: String,
        body: String,
        category: String? = nil,
        userInfo: [String: Int] = [:]
    ) async {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        content.interruptionLevel = .timeSensitive
        content.userInfo = userInfo
        if let category {
            content.categoryIdentifier = category
        }

        try? await UNUserNotificationCenter.current().add(
            UNNotificationRequest(identifier: id, content: content, trigger: nil)
        )
    }

    static func postDelay(_ trip: TripStatusDTO) async {
        let late = "Your \(trip.shuttleName) is running \(trip.delayMinutes) minutes late."

        guard let alternative = trip.alternative else {
            await post(id: "delay-\(trip.bookingId)", title: "Shuttle delayed", body: late)
            return
        }

        await post(
            id: "delay-\(trip.bookingId)",
            title: "Shuttle delayed",
            body: "\(late) The \(alternative.formattedDeparture) shuttle still gets you to "
                + "\(trip.destinationName) by \(alternative.formattedArrival), "
                + "\(alternative.minutesEarlier) minutes sooner. Rebook?",
            category: delayCategory,
            userInfo: ["bookingId": trip.bookingId, "shuttleId": alternative.shuttleId]
        )
    }
}

/// Receives notification taps, including Rebook/Keep, even when the app
/// was in the background.
///
/// Uses the completion-handler callbacks, called on the main actor: with
/// the async variants iOS completed the response off the main thread,
/// which SwiftUI's application object rejects ("Call must be made on main
/// thread").
final class NotificationResponder: NSObject, UNUserNotificationCenterDelegate {
    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping @Sendable (UNNotificationPresentationOptions) -> Void
    ) {
        Task { @MainActor in
            completionHandler([.banner, .sound, .list])
        }
    }

    nonisolated func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping @Sendable () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        let isRebook = response.actionIdentifier == TripNotifications.rebookAction
        let bookingId = userInfo["bookingId"] as? Int
        let shuttleId = userInfo["shuttleId"] as? Int

        Task { @MainActor in
            defer { completionHandler() }

            guard isRebook, let bookingId, let shuttleId else { return }
            await Self.rebook(bookingId: bookingId, shuttleId: shuttleId)
        }
    }

    private static func rebook(bookingId: Int, shuttleId: Int) async {
        do {
            let trip = try await TripMonitor.shared.switchToAlternative(bookingId: bookingId, shuttleId: shuttleId)
            await TripNotifications.post(
                id: "rebooked-\(bookingId)",
                title: "Rebooked",
                body: "You're on the \(trip.shuttleName). \(trip.message)"
            )
        } catch {
            await TripNotifications.post(
                id: "rebook-failed-\(bookingId)",
                title: "Couldn't rebook",
                body: error.localizedDescription
            )
        }
    }
}

final class AppDelegate: NSObject, UIApplicationDelegate {
    private let notificationResponder = NotificationResponder()

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        // Set before launch finishes so a Rebook tap that launched the app
        // in the background is still delivered.
        UNUserNotificationCenter.current().delegate = notificationResponder
        TripNotifications.registerCategories()
        return true
    }
}
