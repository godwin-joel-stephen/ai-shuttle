//
//  BookingDTOs.swift
//  AIShuttle
//

import Foundation

public struct BookingRequest: Codable, Equatable, Sendable {
    public let userId: Int
    public let message: String

    public init(userId: Int, message: String) {
        self.userId = userId
        self.message = message
    }

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case message
    }
}

public struct BookingResponse: Codable, Equatable, Sendable {
    public let bookingId: Int
    public let message: String

    public init(bookingId: Int, message: String) {
        self.bookingId = bookingId
        self.message = message
    }

    enum CodingKeys: String, CodingKey {
        case bookingId = "booking_id"
        case message
    }
}

public struct BookingDetailDTO: Codable, Equatable, Identifiable, Hashable, Sendable {
    public let id: Int
    public let bookingDate: String
    public let pickupTime: String
    public let status: String
    public let childName: String
    public let shuttleName: String
    public let routeName: String
    public let pickupLocation: String?
    public let destination: String?

    public init(
        id: Int,
        bookingDate: String,
        pickupTime: String,
        status: String,
        childName: String,
        shuttleName: String,
        routeName: String,
        pickupLocation: String? = nil,
        destination: String? = nil
    ) {
        self.id = id
        self.bookingDate = bookingDate
        self.pickupTime = pickupTime
        self.status = status
        self.childName = childName
        self.shuttleName = shuttleName
        self.routeName = routeName
        self.pickupLocation = pickupLocation
        self.destination = destination
    }

    enum CodingKeys: String, CodingKey {
        case id
        case bookingDate = "booking_date"
        case pickupTime = "pickup_time"
        case status
        case childName = "child_name"
        case shuttleName = "shuttle_name"
        case routeName = "route_name"
        case pickupLocation = "pickup_location"
        case destination
    }

    public var formattedPickupTime: String {
        let parts = pickupTime.split(separator: ":")
        if parts.count >= 2, let hour = Int(parts[0]), let minute = Int(parts[1]) {
            let period = hour >= 12 ? "PM" : "AM"
            let standardHour = hour % 12 == 0 ? 12 : hour % 12
            return String(format: "%d:%02d %@", standardHour, minute, period)
        }
        return pickupTime
    }

    public var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.locale = Locale(identifier: "en_US_POSIX")
        guard let date = formatter.date(from: bookingDate) else {
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
}
