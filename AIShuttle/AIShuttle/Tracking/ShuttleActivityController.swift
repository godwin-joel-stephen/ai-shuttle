//
//  ShuttleActivityController.swift
//  AIShuttle
//

import ActivityKit
import Foundation

/// Starts, updates and ends the trip Live Activity. One trip at a time.
enum ShuttleActivityController {
    static var isShowing: Bool {
        !Activity<ShuttleActivityAttributes>.activities.isEmpty
    }

    static func show(_ trip: TripStatusDTO) async {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        let content = ActivityContent(state: trip.activityState(), staleDate: trip.arrivalEta)
        let activities = Activity<ShuttleActivityAttributes>.activities

        for activity in activities where activity.attributes.bookingId != trip.bookingId {
            await activity.end(nil, dismissalPolicy: .immediate)
        }

        if let current = activities.first(where: { $0.attributes.bookingId == trip.bookingId }) {
            await update(current, with: trip, content: content)
            return
        }

        guard trip.phase != "arrived" else { return }

        _ = try? Activity.request(
            attributes: ShuttleActivityAttributes(
                bookingId: trip.bookingId,
                shuttleName: trip.shuttleName,
                pickupName: trip.pickupName,
                destinationName: trip.destinationName
            ),
            content: content
        )
    }

    /// Refreshes a running Live Activity, e.g. after a delay is announced.
    static func refresh(_ trip: TripStatusDTO) async {
        guard let current = Activity<ShuttleActivityAttributes>.activities.first(where: {
            $0.attributes.bookingId == trip.bookingId
        }) else { return }

        let content = ActivityContent(state: trip.activityState(), staleDate: trip.arrivalEta)
        await update(current, with: trip, content: content)
    }

    private static func update(
        _ activity: Activity<ShuttleActivityAttributes>,
        with trip: TripStatusDTO,
        content: ActivityContent<ShuttleActivityAttributes.ContentState>
    ) async {
        if trip.phase == "arrived" {
            await activity.end(content, dismissalPolicy: .after(.now.addingTimeInterval(5 * 60)))
        } else {
            await activity.update(content)
        }
    }
}
