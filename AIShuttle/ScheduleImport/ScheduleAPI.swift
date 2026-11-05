//
//  ScheduleAPI.swift
//  POST /schedule/plan and /schedule/apply (typed days only).
//

import Foundation

nonisolated enum ScheduleActionDTO: String, Codable, Sendable {
    case book
    case keep
    case cancel
    case none
    case blocked

    var changesBookings: Bool { self == .book || self == .cancel }
}

nonisolated struct ScheduleDayResultDTO: Codable, Equatable, Identifiable, Sendable {
    let date: String
    let kind: WorkdayKind
    let action: ScheduleActionDTO
    let message: String
    let reasonCode: String?
    let bookings: [BookingDetailDTO]
    /// nil in a plan; true/false once applied.
    let succeeded: Bool?

    var id: String { date }

    enum CodingKeys: String, CodingKey {
        case date, kind, action, message, bookings, succeeded
        case reasonCode = "reason_code"
    }
}

nonisolated struct SchedulePlanDTO: Codable, Equatable, Sendable {
    let days: [ScheduleDayResultDTO]
    let summary: String
    let changes: Int
}

nonisolated struct ScheduleApplyDTO: Codable, Equatable, Sendable {
    let days: [ScheduleDayResultDTO]
    let summary: String
    let bookingsChanged: Bool

    enum CodingKeys: String, CodingKey {
        case days, summary
        case bookingsChanged = "bookings_changed"
    }
}

nonisolated struct ScheduleRequestDTO: Encodable, Sendable {
    let userId: Int
    let days: [ScheduleDay]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case days
    }
}

extension BookingAPIClient {
    func planSchedule(_ days: [ScheduleDay], userId: Int = 1) async throws -> SchedulePlanDTO {
        try await post("schedule/plan", body: ScheduleRequestDTO(userId: userId, days: days))
    }

    func applySchedule(_ days: [ScheduleDay], userId: Int = 1) async throws -> ScheduleApplyDTO {
        try await post("schedule/apply", body: ScheduleRequestDTO(userId: userId, days: days))
    }
}
