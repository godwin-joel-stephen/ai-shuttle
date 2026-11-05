//
//  AssistantAPI.swift
//  AIShuttle
//

import Foundation

public struct AssistantMessageRequest: Encodable, Sendable {
    let userId: Int
    let message: String
    let conversationId: String?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case message
        case conversationId = "conversation_id"
    }
}

/// One tool call the agent made while answering.
public struct AssistantActionDTO: Codable, Equatable, Hashable, Sendable {
    public let tool: String
    public let succeeded: Bool
    public let error: String?
    /// External MCP server that provided the tool; nil for Clear Path's own.
    public let server: String?

    /// Plain-language label for showing the agent's work, naming the MCP
    /// server when the step used an outside one.
    public var label: String {
        guard let server else { return action }
        return "\(action) · via \(server) MCP server"
    }

    private var action: String {
        switch tool {
        case "get_my_bookings": return "Checked your bookings"
        case "list_shuttle_options": return "Checked shuttle options"
        case "book_usual_shuttle": return "Booked your usual shuttle"
        case "change_booking_shuttle": return "Changed your shuttle"
        case "cancel_booking": return "Cancelled a booking"
        case "get_shuttle_status": return "Checked live shuttle status"
        case "check_booking_eligibility": return "Checked the booking rules"
        case "plan_trip": return "Planned your trip"
        case "book_trip_plan": return "Booked your trip plan"
        case "search_policies": return "Searched Clear Path policies"
        case "get_current_weather": return "Checked the weather"
        default: return tool.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }
}

public struct AssistantMessageResponse: Decodable, Equatable, Sendable {
    public let conversationId: String
    public let reply: String
    public let actions: [AssistantActionDTO]
    public let bookingsChanged: Bool
    /// Policy sections the answer is grounded in, e.g.
    /// "Booking Policy › Service days".
    public let sources: [String]?

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case reply
        case actions
        case bookingsChanged = "bookings_changed"
        case sources
    }
}

public struct ConversationDTO: Decodable, Equatable, Sendable {
    public struct Message: Decodable, Equatable, Sendable {
        public let role: String
        public let text: String
        public let actions: [AssistantActionDTO]
        public let sources: [String]?
    }

    public let conversationId: String
    public let messages: [Message]

    enum CodingKeys: String, CodingKey {
        case conversationId = "conversation_id"
        case messages
    }
}

extension BookingAPIClient {
    /// The agent may make several model and tool calls per message, so it
    /// gets a longer budget than plain booking requests.
    nonisolated public static func forAssistant() -> BookingAPIClient {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 40
        configuration.timeoutIntervalForResource = 45
        return BookingAPIClient(session: URLSession(configuration: configuration))
    }

    public func sendAssistantMessage(
        _ message: String,
        conversationId: String?,
        userId: Int = 1
    ) async throws -> AssistantMessageResponse {
        try await post(
            "assistant/messages",
            body: AssistantMessageRequest(userId: userId, message: message, conversationId: conversationId)
        )
    }

    public func fetchConversation(id: String, userId: Int = 1) async throws -> ConversationDTO {
        try await get("assistant/conversations/\(id)", userId: userId)
    }
}

/// The conversation shared by the in-app chat and the "Ask Clear Path" Siri
/// intent. It continues while active and starts fresh after a quiet spell,
/// so an old topic doesn't leak into a new request.
///
/// Nonisolated: Siri runs AskClearPathIntent off the main actor, and
/// UserDefaults is thread-safe.
nonisolated struct ConversationStore {
    private static let idKey = "assistant.conversationId"
    private static let lastActivityKey = "assistant.lastActivity"

    var defaults: UserDefaults = .standard
    var expiry: TimeInterval = 30 * 60

    var currentConversationId: String? {
        guard let id = defaults.string(forKey: Self.idKey),
              let lastActivity = defaults.object(forKey: Self.lastActivityKey) as? Date,
              Date.now.timeIntervalSince(lastActivity) < expiry else {
            return nil
        }
        return id
    }

    func save(_ conversationId: String) {
        defaults.set(conversationId, forKey: Self.idKey)
        defaults.set(Date.now, forKey: Self.lastActivityKey)
    }

    func reset() {
        defaults.removeObject(forKey: Self.idKey)
        defaults.removeObject(forKey: Self.lastActivityKey)
    }
}
