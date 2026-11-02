//
//  AssistantTests.swift
//  AIShuttleTests
//

import Foundation
import Testing
@testable import AIShuttle

@Suite(.serialized)
@MainActor
struct AssistantTests {
    private func makeClient() -> BookingAPIClient {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        return BookingAPIClient(baseURL: URL(string: "http://127.0.0.1:8000")!, session: URLSession(configuration: configuration))
    }

    private func makeStore() -> ConversationStore {
        let suite = "AssistantTests-\(UUID().uuidString)"
        return ConversationStore(defaults: UserDefaults(suiteName: suite)!)
    }

    private static func ok(_ request: URLRequest, _ json: String) -> (HTTPURLResponse, Data) {
        let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
        return (response, json.data(using: .utf8)!)
    }

    private static let bookedReply = """
    {
        "conversation_id": "abc",
        "reply": "Done. You're on the 7:30 AM shuttle tomorrow.",
        "actions": [{"tool": "book_usual_shuttle", "arguments": {"booking_date": "2026-11-03"}, "succeeded": true, "error": null}],
        "bookings_changed": true
    }
    """

    @Test func sendAppendsReplyAndContinuesConversation() async throws {
        let store = makeStore()
        nonisolated(unsafe) var sentConversationIds: [Any] = []
        MockURLProtocol.requestHandler = { request in
            let body = try JSONSerialization.jsonObject(with: request.bodyData) as? [String: Any]
            sentConversationIds.append(body?["conversation_id"] ?? NSNull())
            return Self.ok(request, Self.bookedReply)
        }

        var refreshed = 0
        let viewModel = AssistantViewModel(apiClient: makeClient(), store: store, onBookingsChanged: { refreshed += 1 })

        await viewModel.send("Book my usual shuttle for tomorrow")
        await viewModel.send("Thanks")

        #expect(viewModel.messages.count == 4)
        #expect(viewModel.messages[1].text == "Done. You're on the 7:30 AM shuttle tomorrow.")
        #expect(viewModel.messages[1].actions.first?.label == "Booked your usual shuttle")
        #expect(sentConversationIds.first is NSNull)
        #expect(sentConversationIds.last as? String == "abc")
        #expect(store.currentConversationId == "abc")
        #expect(refreshed == 2)
    }

    @Test func failedSendShowsErrorAndKeepsUserMessage() async {
        MockURLProtocol.requestHandler = { request in
            let response = HTTPURLResponse(url: request.url!, statusCode: 503, httpVersion: nil, headerFields: nil)!
            return (response, #"{"detail": "Clear Path's assistant is unavailable right now."}"#.data(using: .utf8)!)
        }

        let viewModel = AssistantViewModel(apiClient: makeClient(), store: makeStore())
        await viewModel.send("Hi")

        #expect(viewModel.messages.map(\.text) == ["Hi"])
        #expect(viewModel.errorMessage == "Clear Path's assistant is unavailable right now.")
        #expect(viewModel.isSending == false)
    }

    @Test func loadsConversationStartedFromSiri() async {
        let store = makeStore()
        store.save("siri-convo")
        MockURLProtocol.requestHandler = { request in
            #expect(request.url?.absoluteString == "http://127.0.0.1:8000/assistant/conversations/siri-convo?user_id=1")
            return Self.ok(request, """
            {"conversation_id": "siri-convo", "messages": [
                {"role": "user", "text": "Make it earlier", "actions": []},
                {"role": "assistant", "text": "Moved you to 7:15 AM.", "actions": [
                    {"tool": "change_booking_shuttle", "arguments": {}, "succeeded": true, "error": null}
                ]}
            ]}
            """)
        }

        let viewModel = AssistantViewModel(apiClient: makeClient(), store: store)
        await viewModel.loadConversation()

        #expect(viewModel.messages.map(\.role) == [.user, .assistant])
        #expect(viewModel.messages[1].actions.first?.label == "Changed your shuttle")
    }

    @Test func conversationExpiresAfterQuietPeriod() {
        var store = makeStore()
        store.save("old")
        #expect(store.currentConversationId == "old")

        store.expiry = 0
        #expect(store.currentConversationId == nil)
    }

    @Test func newConversationClearsMessagesAndStoredId() async {
        let store = makeStore()
        MockURLProtocol.requestHandler = { request in Self.ok(request, Self.bookedReply) }
        let viewModel = AssistantViewModel(apiClient: makeClient(), store: store)

        await viewModel.send("Book tomorrow")
        viewModel.startNewConversation()

        #expect(viewModel.messages.isEmpty)
        #expect(store.currentConversationId == nil)
    }
}


@Suite(.serialized)
@MainActor
struct AssistantSourcesTests {
    @Test func replyCarriesPolicySources() async {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [MockURLProtocol.self]
        let client = BookingAPIClient(baseURL: URL(string: "http://127.0.0.1:8000")!, session: URLSession(configuration: configuration))
        MockURLProtocol.requestHandler = { request in
            let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
            return (response, """
            {
                "conversation_id": "c1",
                "reply": "Per the Booking Policy, shuttles run Monday to Friday.",
                "actions": [
                    {"tool": "check_booking_eligibility", "arguments": {}, "succeeded": true, "error": null},
                    {"tool": "search_policies", "arguments": {}, "succeeded": true, "error": null}
                ],
                "bookings_changed": false,
                "sources": ["Booking Policy › Service days"]
            }
            """.data(using: .utf8)!)
        }

        let store = ConversationStore(defaults: UserDefaults(suiteName: "AssistantSourcesTests-\(UUID().uuidString)")!)
        let viewModel = AssistantViewModel(apiClient: client, store: store)
        await viewModel.send("Why can't I book Saturday?")

        #expect(viewModel.messages[1].sources == ["Booking Policy › Service days"])
        #expect(viewModel.messages[1].actions.map(\.label) == ["Checked the booking rules", "Searched Clear Path policies"])
    }
}
