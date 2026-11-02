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

/// A faster departure offered when the booked shuttle is running late.
public struct AlternativeDTO: Decodable, Equatable, Sendable {
    public let shuttleId: Int
    public let shuttleName: String
    public let departure: String
    public let arrival: String
    public let minutesEarlier: Int

    enum CodingKeys: String, CodingKey {
        case shuttleId = "shuttle_id"
        case shuttleName = "shuttle_name"
        case departure
        case arrival
        case minutesEarlier = "minutes_earlier"
    }

    var formattedDeparture: String { Self.twelveHour(departure) }
    var formattedArrival: String { Self.twelveHour(arrival) }

    private static func twelveHour(_ time: String) -> String {
        let parts = time.split(separator: ":").compactMap { Int($0) }
        guard parts.count == 2 else { return time }
        let hour = parts[0] % 12 == 0 ? 12 : parts[0] % 12
        return String(format: "%d:%02d %@", hour, parts[1], parts[0] >= 12 ? "PM" : "AM")
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
    /// Present while trip mode shares the rider's location.
    public let walkMinutes: Int?
    /// Minutes until the rider should set off; 0 or less means now.
    public let leaveInMinutes: Int?
    public let alternative: AlternativeDTO?

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
        case walkMinutes = "walk_minutes"
        case leaveInMinutes = "leave_in_minutes"
        case alternative
    }

    /// "12 min walk · leave in 3 min", when the walk is known.
    public var departureAdvice: String? {
        guard let walkMinutes else { return nil }
        guard let leaveInMinutes else { return "\(walkMinutes) min walk to \(pickupName)" }
        return leaveInMinutes <= 0
            ? "\(walkMinutes) min walk · leave now"
            : "\(walkMinutes) min walk · leave in \(leaveInMinutes) min"
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

struct LocationRequest: Encodable {
    let latitude: Double
    let longitude: Double
}

struct MoveBookingRequest: Encodable {
    let userId: Int
    let shuttleId: Int

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case shuttleId = "shuttle_id"
    }
}

extension BookingAPIClient {
    public func fetchNextTrip(userId: Int = 1) async throws -> TripStatusDTO {
        try await get("tracking/next", userId: userId)
    }

    /// Shares the rider's location during trip mode for walking estimates.
    public func reportLocation(latitude: Double, longitude: Double, userId: Int = 1) async throws {
        let _: NoContent = try await post(
            "users/\(userId)/location",
            body: LocationRequest(latitude: latitude, longitude: longitude)
        )
    }

    /// Moves a booking to a specific shuttle, e.g. the faster alternative.
    public func moveBooking(id bookingId: Int, toShuttle shuttleId: Int, userId: Int = 1) async throws -> TripStatusDTO {
        try await post(
            "bookings/\(bookingId)/move",
            body: MoveBookingRequest(userId: userId, shuttleId: shuttleId)
        )
    }
}
