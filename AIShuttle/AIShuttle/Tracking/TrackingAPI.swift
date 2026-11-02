//
//  TrackingAPI.swift
//  AIShuttle
//

import CoreLocation
import Foundation

public struct CoordinateDTO: Decodable, Hashable, Sendable {
    public let latitude: Double
    public let longitude: Double

    public var location: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }
}

public struct TripStatusDTO: Decodable, Equatable, Sendable {
    public let bookingId: Int
    public let bookingDate: String
    public let shuttleName: String
    /// scheduled, approaching, boarding, in_transit or arrived.
    public let phase: String
    public let message: String
    public let delayMinutes: Int
    public let minutesToPickup: Int?
    public let minutesToArrival: Int?
    public let pickupEta: Date
    public let arrivalEta: Date
    /// 0-1 across the tracked trip: depot -> pickup -> destination.
    public let progress: Double
    public let position: CoordinateDTO
    public let pickup: CoordinateDTO
    public let destination: CoordinateDTO
    public let pickupName: String
    public let destinationName: String
    public let route: [CoordinateDTO]
    public let simulated: Bool

    enum CodingKeys: String, CodingKey {
        case bookingId = "booking_id"
        case bookingDate = "booking_date"
        case shuttleName = "shuttle_name"
        case phase
        case message
        case delayMinutes = "delay_minutes"
        case minutesToPickup = "minutes_to_pickup"
        case minutesToArrival = "minutes_to_arrival"
        case pickupEta = "pickup_eta"
        case arrivalEta = "arrival_eta"
        case progress
        case position
        case pickup
        case destination
        case pickupName = "pickup_name"
        case destinationName = "destination_name"
        case route
        case simulated
    }

    /// The shuttle is moving or about to; worth a Live Activity.
    public var isLive: Bool {
        phase == "approaching" || phase == "boarding" || phase == "in_transit"
    }

    func activityState(now: Date = .now) -> ShuttleActivityAttributes.ContentState {
        // Back out when tracking began from progress and the arrival time,
        // so the Lock Screen progress bar can keep advancing by itself.
        let remaining = arrivalEta.timeIntervalSince(now)
        let windowStart = progress < 1 && remaining > 0
            ? now.addingTimeInterval(-remaining * progress / (1 - progress))
            : now

        return ShuttleActivityAttributes.ContentState(
            phase: phase,
            message: message,
            pickupETA: pickupEta,
            arrivalETA: arrivalEta,
            delayMinutes: delayMinutes,
            windowStart: windowStart
        )
    }
}

extension BookingAPIClient {
    public func fetchNextTrip(userId: Int = 1) async throws -> TripStatusDTO {
        try await get("tracking/next", userId: userId)
    }
}
