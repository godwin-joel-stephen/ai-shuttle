//
//  BookingDTOs.swift
//  AIShuttle
//

import Foundation

/// Either natural language (`message`) or an already-structured date.
/// Structured requests skip LLM interpretation on the backend.
public struct BookingRequest: Codable, Equatable, Sendable {
    public let userId: Int
    public let message: String?
    public let bookingDate: String?

    public init(userId: Int, message: String) {
        self.userId = userId
        self.message = message
        self.bookingDate = nil
    }

    public init(userId: Int, bookingDate: String) {
        self.userId = userId
        self.message = nil
        self.bookingDate = bookingDate
    }

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case message
        case bookingDate = "booking_date"
    }
}

public enum RescheduleDirectionDTO: String, Codable, Sendable {
    case earlier
    case later
}

public struct RescheduleRequest: Codable, Equatable, Sendable {
    public let userId: Int
    public let direction: RescheduleDirectionDTO

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case direction
    }
}

public struct BookingResponse: Codable, Equatable, Sendable {
    public let bookingId: Int
    public let message: String
    public let alreadyBooked: Bool
    public let booking: BookingDetailDTO?
    /// Why "your usual" meant this shuttle, for a new booking of a learned
    /// or pinned usual: "you took it on 4 of your last 5 Mondays".
    public let usualReason: String?

    public init(
        bookingId: Int,
        message: String,
        alreadyBooked: Bool = false,
        booking: BookingDetailDTO? = nil,
        usualReason: String? = nil
    ) {
        self.bookingId = bookingId
        self.message = message
        self.alreadyBooked = alreadyBooked
        self.booking = booking
        self.usualReason = usualReason
    }

    enum CodingKeys: String, CodingKey {
        case bookingId = "booking_id"
        case message
        case alreadyBooked = "already_booked"
        case booking
        case usualReason = "usual_reason"
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        bookingId = try container.decode(Int.self, forKey: .bookingId)
        message = try container.decode(String.self, forKey: .message)
        alreadyBooked = try container.decodeIfPresent(Bool.self, forKey: .alreadyBooked) ?? false
        booking = try container.decodeIfPresent(BookingDetailDTO.self, forKey: .booking)
        usualReason = try container.decodeIfPresent(String.self, forKey: .usualReason)
    }
}

/// FastAPI error body: `{"detail": "..."}`.
struct APIErrorBody: Decodable {
    let detail: String
}

public struct BookingDetailDTO: Codable, Equatable, Identifiable, Hashable, Sendable {
    public let id: Int
    public let bookingDate: String
    public let pickupTime: String
    public let arrivalTime: String?
    public let status: String
    public let shuttleName: String
    public let routeName: String
    public let pickupLocation: String?
    public let destination: String?
    public let earlierAvailable: Bool?
    public let laterAvailable: Bool?

    public init(
        id: Int,
        bookingDate: String,
        pickupTime: String,
        arrivalTime: String? = nil,
        status: String,
        shuttleName: String,
        routeName: String,
        pickupLocation: String? = nil,
        destination: String? = nil,
        earlierAvailable: Bool? = nil,
        laterAvailable: Bool? = nil
    ) {
        self.id = id
        self.bookingDate = bookingDate
        self.pickupTime = pickupTime
        self.arrivalTime = arrivalTime
        self.status = status
        self.shuttleName = shuttleName
        self.routeName = routeName
        self.pickupLocation = pickupLocation
        self.destination = destination
        self.earlierAvailable = earlierAvailable
        self.laterAvailable = laterAvailable
    }

    enum CodingKeys: String, CodingKey {
        case id
        case bookingDate = "booking_date"
        case pickupTime = "pickup_time"
        case arrivalTime = "arrival_time"
        case status
        case shuttleName = "shuttle_name"
        case routeName = "route_name"
        case pickupLocation = "pickup_location"
        case destination
        case earlierAvailable = "earlier_available"
        case laterAvailable = "later_available"
    }

    public var formattedPickupTime: String {
        Self.formatTime(pickupTime)
    }

    public var formattedArrivalTime: String? {
        arrivalTime.map(Self.formatTime)
    }

    /// "Home → Office", falling back to the route name.
    public var tripTitle: String {
        guard let pickupLocation, let destination else {
            return routeName
        }
        return "\(pickupLocation) → \(destination)"
    }

    public var formattedDate: String {
        guard let date = parsedDate else {
            return bookingDate
        }

        let calendar = Calendar.current
        let displayFormatter = DateFormatter()
        displayFormatter.dateFormat = "MMM d"

        if calendar.isDateInToday(date) {
            return "Today · \(displayFormatter.string(from: date))"
        } else if calendar.isDateInTomorrow(date) {
            return "Tomorrow · \(displayFormatter.string(from: date))"
        } else {
            let yearFormatter = DateFormatter()
            yearFormatter.dateFormat = "EEEE, MMM d, yyyy"
            return yearFormatter.string(from: date)
        }
    }

    /// Relative day for speech: "today", "tomorrow" or "on Friday".
    public var spokenDay: String {
        guard let date = parsedDate else {
            return "on \(bookingDate)"
        }

        let calendar = Calendar.current
        if calendar.isDateInToday(date) {
            return "today"
        } else if calendar.isDateInTomorrow(date) {
            return "tomorrow"
        }

        let formatter = DateFormatter()
        formatter.dateFormat = "EEEE"
        return "on \(formatter.string(from: date))"
    }

    private var parsedDate: Date? {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter.date(from: bookingDate)
    }

    nonisolated static func formatTime(_ time: String) -> String {
        let parts = time.split(separator: ":")
        if parts.count >= 2, let hour = Int(parts[0]), let minute = Int(parts[1]) {
            let period = hour >= 12 ? "PM" : "AM"
            let standardHour = hour % 12 == 0 ? 12 : hour % 12
            return String(format: "%d:%02d %@", standardHour, minute, period)
        }
        return time
    }
}
