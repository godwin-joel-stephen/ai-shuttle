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
