//
//  TripMonitor.swift
//  AIShuttle
//
//  Trip mode: while a trip is under way, background location keeps the app
//  running so it can follow the shuttle without server push (which needs a
//  paid developer account). Every few seconds it shares the rider's
//  location, refreshes the trip, updates the Live Activity and posts local
//  notifications for "time to leave" and delays. It stops on arrival.
//

import CoreLocation
import Foundation
import Observation
import UserNotifications
import WidgetKit

@MainActor
@Observable
final class TripMonitor {
    static let shared = TripMonitor()

    private(set) var isActive = false
    private(set) var latestTrip: TripStatusDTO?
    var errorMessage: String?

    private let apiClient: BookingAPIClient
    private let pollInterval: Duration
    private var backgroundSession: CLBackgroundActivitySession?
    private var serviceSession: CLServiceSession?
    private var locationTask: Task<Void, Never>?
    private var pollTask: Task<Void, Never>?
    private var latestLocation: CLLocation?
    private var reportedLocation: CLLocation?

    // What was already announced, so each alert fires once per trip.
    private var leaveNotified = false
    private var announcedDelay = 0

    init(apiClient: BookingAPIClient = .withTimeouts(), pollInterval: Duration = .seconds(15)) {
        self.apiClient = apiClient
        self.pollInterval = pollInterval
    }

    /// Must be called while the app is in the foreground: iOS only lets a
    /// background location session begin from the foreground.
    func start() {
        guard !isActive else { return }
        isActive = true
        errorMessage = nil
        leaveNotified = false
        announcedDelay = 0

        serviceSession = CLServiceSession(authorization: .whenInUse)
        backgroundSession = CLBackgroundActivitySession()

        locationTask = Task { [weak self] in
            do {
                for try await update in CLLocationUpdate.liveUpdates(.otherNavigation) {
                    if let location = update.location {
                        self?.latestLocation = location
                    }
                }
            } catch {
                self?.errorMessage = "Location updates stopped."
            }
        }

        pollTask = Task { [weak self] in
            while !Task.isCancelled, let self {
                await self.tick()
                try? await Task.sleep(for: self.pollInterval)
            }
        }
    }

    func stop() {
        locationTask?.cancel()
        pollTask?.cancel()
        backgroundSession?.invalidate()
        serviceSession?.invalidate()
        locationTask = nil
        pollTask = nil
        backgroundSession = nil
        serviceSession = nil
        isActive = false
    }

    /// Takes the faster alternative, e.g. from the delay notification.
    func switchToAlternative(bookingId: Int, shuttleId: Int) async throws -> TripStatusDTO {
        let trip = try await apiClient.moveBooking(id: bookingId, toShuttle: shuttleId)
        announcedDelay = 0
        leaveNotified = false
        await apply(trip)
        WidgetCenter.shared.reloadAllTimelines()
        return trip
    }

    private func tick() async {
        await reportLocationIfMoved()

        do {
            let trip = try await apiClient.fetchNextTrip()
            errorMessage = nil
            await apply(trip)
            await notifyIfNeeded(trip)

            if trip.phase == "arrived" {
                stop()
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func apply(_ trip: TripStatusDTO) async {
        latestTrip = trip
        await ShuttleActivityController.show(trip)
    }

    private func reportLocationIfMoved() async {
        guard let location = latestLocation else { return }
        if let reported = reportedLocation,
           location.distance(from: reported) < 50,
           Date.now.timeIntervalSince(reported.timestamp) < 120 {
            return
        }

        do {
            try await apiClient.reportLocation(
                latitude: location.coordinate.latitude,
                longitude: location.coordinate.longitude
            )
            reportedLocation = location
        } catch {
            // Walking estimates are optional; tracking carries on without.
        }
    }

    private func notifyIfNeeded(_ trip: TripStatusDTO) async {
        if let leaveIn = trip.leaveInMinutes, leaveIn <= 0, !leaveNotified {
            leaveNotified = true
            let walk = trip.walkMinutes.map { " It's about a \($0)-minute walk to \(trip.pickupName)." } ?? ""
            await TripNotifications.post(
                id: "leave-\(trip.bookingId)",
                title: "Time to leave",
                body: "Your shuttle reaches \(trip.pickupName) in \(trip.minutesToPickup ?? 0) minutes.\(walk)"
            )
        }

        // Announce a delay once, and again only if it grows by 5+ minutes.
        if trip.delayMinutes >= 5, trip.delayMinutes >= announcedDelay + 5 {
            announcedDelay = trip.delayMinutes
            await TripNotifications.postDelay(trip)
        }
    }
}
