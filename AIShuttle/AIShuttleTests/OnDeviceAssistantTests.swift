//
//  OnDeviceAssistantTests.swift
//  AIShuttleTests
//
//  F14: which requests the phone answers, and that everything else (or any
//  doubt) goes to the cloud agent.
//

import Foundation
import Testing
@testable import AIShuttle

@MainActor
struct OnDeviceGateTests {
    @Test(arguments: [
        ("Book my usual shuttle for tomorrow", OnDeviceClassification.Kind.bookUsual, BookingDay.tomorrow),
        ("book thursday", .bookUsual, .thursday),
        ("Move Friday earlier", .moveEarlier, .friday),
        ("Make my Monday shuttle later", .moveLater, .monday),
        ("Cancel my Wednesday shuttle", .cancel, .wednesday),
        ("Am I booked on Friday?", .listBookings, .friday),
    ])
    func simpleRequestsPass(message: String, kind: OnDeviceClassification.Kind, day: BookingDay) {
        #expect(OnDeviceGate.screen(message) == .init(kind: kind, day: day))
    }

    @Test func listingNeedsNoDay() {
        #expect(OnDeviceGate.screen("What do I have booked?") == .init(kind: .listBookings, day: nil))
    }

    /// The demo's cloud showcases must never be taken on device.
    @Test(arguments: [
        "Make it 30 minutes earlier",
        "Make it earlier",
        "Book Friday, the latest shuttle",
        "Why can't I book Saturday?",
        "Should I leave now?",
        "I have a meeting at 8 tomorrow, get me there in time",
        "Get me to the office by 7:30 on Wednesday",
        "Book Monday and cancel Tuesday",
        "Book my usual shuttle for Monday and Tuesday",
        "Don't cancel Friday",
        "Book my usual shuttle next week",
        "Is it going to rain tomorrow?",
        "Cancel",
        "Hi",
        "Book my usual shuttle for the 12th",
    ])
    func everythingElseGoesToTheCloud(message: String) {
        #expect(OnDeviceGate.screen(message) == nil)
    }

    @Test func modelMustAgreeWithTheWords() {
        let screened = OnDeviceGate.Screened(kind: .cancel, day: .friday)

        #expect(OnDeviceGate.verify(.init(kind: .cancel, day: "friday"), against: screened) == .cancel(.friday))
        #expect(OnDeviceGate.verify(.init(kind: .bookUsual, day: "friday"), against: screened) == nil)
        #expect(OnDeviceGate.verify(.init(kind: .cancel, day: "monday"), against: screened) == nil)
        #expect(OnDeviceGate.verify(.init(kind: .other, day: nil), against: screened) == nil)
    }
}

private struct StubClassifier: OnDeviceClassifier {
    var result: @Sendable () async throws -> OnDeviceClassification

    func classify(_ message: String) async throws -> OnDeviceClassification {
        try await result()
    }
}

private struct ModelFailed: Error {}

extension MockedNetworkTests {
    @Suite
    @MainActor
    struct OnDeviceAssistantTests {
        /// Monday 2 November 2026, 06:00: tomorrow is Tuesday the 3rd.
        static let monday: Date = {
            var components = DateComponents(year: 2026, month: 11, day: 2, hour: 6)
            components.calendar = Calendar.current
            return components.date!
        }()

        private func client() -> BookingAPIClient {
            let configuration = URLSessionConfiguration.ephemeral
            configuration.protocolClasses = [MockURLProtocol.self]
            return BookingAPIClient(baseURL: URL(string: "http://127.0.0.1:8000")!, session: URLSession(configuration: configuration))
        }

        private func assistant(
            _ result: @escaping @Sendable () async throws -> OnDeviceClassification,
            deadline: Duration = .seconds(3)
        ) -> OnDeviceAssistant {
            OnDeviceAssistant(
                classifier: StubClassifier(result: result),
                apiClient: client(),
                deadline: deadline,
                now: { Self.monday }
            )
        }

        private static func respond(_ request: URLRequest, _ json: String, status: Int = 200) -> (HTTPURLResponse, Data) {
            (HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: nil, headerFields: nil)!, Data(json.utf8))
        }

        static func booking(id: Int = 7, date: String = "2026-11-03", status: String = "confirmed") -> String {
            """
            {"id": \(id), "booking_date": "\(date)", "pickup_time": "07:30:00", "arrival_time": "08:15:00",
             "status": "\(status)", "shuttle_name": "Morning Shuttle C", "route_name": "Home → Office Morning",
             "pickup_location": "Home", "destination": "Office"}
            """
        }

        static func bookingResponse(_ message: String = "Done.") -> String {
            """
            {"booking_id": 7, "message": "\(message)", "already_booked": false, "booking": \(booking())}
            """
        }

        @Test func booksTheUsualWithAStructuredRequest() async throws {
            nonisolated(unsafe) var sent: [String: Any]?
            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.path == "/bookings")
                sent = try JSONSerialization.jsonObject(with: request.bodyData) as? [String: Any]
                return Self.respond(request, Self.bookingResponse())
            }

            let answer = try #require(await assistant({ .init(kind: .bookUsual, day: "tomorrow") })
                .answer("Book my usual shuttle for tomorrow"))

            #expect(sent?["booking_date"] as? String == "2026-11-03")
            #expect(sent?["message"] == nil)
            #expect(answer.reply.hasPrefix("Done. You're on the 7:30 AM shuttle"))
            #expect(answer.actions.map(\.label) == ["Booked your usual shuttle"])
            #expect(answer.bookingsChanged)
        }

        @Test func cloudRequestsNeverReachTheModel() async {
            MockURLProtocol.requestHandler = { _ in
                Issue.record("No request expected")
                throw ModelFailed()
            }

            let answer = await assistant({
                Issue.record("The model shouldn't be asked")
                return .init(kind: .other, day: nil)
            }).answer("Why can't I book Saturday?")

            #expect(answer == nil)
        }

        @Test func disagreementGoesToTheCloud() async {
            MockURLProtocol.requestHandler = { _ in
                Issue.record("No request expected")
                throw ModelFailed()
            }

            let answer = await assistant({ .init(kind: .other, day: nil) }).answer("Cancel my Friday shuttle")

            #expect(answer == nil)
        }

        @Test func modelFailureGoesToTheCloud() async {
            let answer = await assistant({ throw ModelFailed() }).answer("Book thursday")

            #expect(answer == nil)
        }

        @Test func slowModelGoesToTheCloud() async {
            let started = ContinuousClock.now
            let answer = await assistant({
                try await Task.sleep(for: .seconds(5))
                return .init(kind: .bookUsual, day: "thursday")
            }, deadline: .milliseconds(200)).answer("Book thursday")

            #expect(answer == nil)
            #expect(ContinuousClock.now - started < .seconds(2))
        }

        @Test func bookingRuleRefusalIsTheAnswer() async throws {
            MockURLProtocol.requestHandler = { request in
                Self.respond(request, #"{"detail": "Shuttles don't run on Saturdays."}"#, status: 409)
            }

            let answer = try #require(await assistant({ .init(kind: .bookUsual, day: "saturday") })
                .answer("Book my usual shuttle for Saturday"))

            #expect(answer.reply == "Shuttles don't run on Saturdays.")
            #expect(answer.actions.first?.succeeded == false)
            #expect(!answer.bookingsChanged)
        }

        @Test func cancelsTheBookingOnThatDay() async throws {
            nonisolated(unsafe) var paths: [String] = []
            MockURLProtocol.requestHandler = { request in
                paths.append(request.url!.path)
                if request.httpMethod == "GET" {
                    return Self.respond(request, "[\(Self.booking(id: 9, date: "2026-11-06"))]")
                }
                return Self.respond(request, Self.bookingResponse("Done. I cancelled the 7:30 AM shuttle."))
            }

            let answer = try #require(await assistant({ .init(kind: .cancel, day: "friday") })
                .answer("Cancel my Friday shuttle"))

            #expect(paths == ["/bookings", "/bookings/9/cancel"])
            #expect(answer.reply == "Done. I cancelled the 7:30 AM shuttle.")
            #expect(answer.actions.map(\.tool) == ["cancel_booking"])
        }

        @Test func movingADayWithoutABookingSaysSo() async throws {
            MockURLProtocol.requestHandler = { request in Self.respond(request, "[]") }

            let answer = try #require(await assistant({ .init(kind: .moveEarlier, day: "friday") })
                .answer("Move Friday earlier"))

            #expect(answer.reply == "You don't have a shuttle booked on Friday.")
            #expect(!answer.bookingsChanged)
        }

        @Test func listsUpcomingBookings() async throws {
            MockURLProtocol.requestHandler = { request in
                Self.respond(request, "[\(Self.booking(id: 1)), \(Self.booking(id: 2, status: "cancelled"))]")
            }

            let answer = try #require(await assistant({ .init(kind: .listBookings, day: nil) })
                .answer("What do I have booked?"))

            #expect(answer.reply.hasPrefix("You're booked on the 7:30 AM"))
            #expect(!answer.reply.contains(" and "))
        }

        @Test func chatShowsAndRecordsTheOnDeviceAnswer() async throws {
            nonisolated(unsafe) var recorded: [String: Any]?
            MockURLProtocol.requestHandler = { request in
                if request.url?.path == "/assistant/on-device-turns" {
                    recorded = try JSONSerialization.jsonObject(with: request.bodyData) as? [String: Any]
                    return Self.respond(request, #"{"conversation_id": "conv-1"}"#)
                }
                return Self.respond(request, Self.bookingResponse())
            }
            let store = ConversationStore(defaults: UserDefaults(suiteName: "OnDevice-\(UUID().uuidString)")!)
            var refreshed = 0
            let viewModel = AssistantViewModel(
                apiClient: client(),
                store: store,
                onDevice: assistant({ .init(kind: .bookUsual, day: "tomorrow") }),
                onBookingsChanged: { refreshed += 1 }
            )

            await viewModel.send("Book my usual shuttle for tomorrow")

            #expect(viewModel.messages.count == 2)
            #expect(viewModel.messages[1].onDevice)
            #expect(viewModel.messages[1].text.hasPrefix("Done. You're on the 7:30 AM shuttle"))
            #expect(recorded?["message"] as? String == "Book my usual shuttle for tomorrow")
            #expect((recorded?["actions"] as? [[String: Any]])?.first?["tool"] as? String == "book_usual_shuttle")
            #expect(store.currentConversationId == "conv-1")
            #expect(refreshed == 1)
        }

        @Test func chatFallsBackToTheCloud() async throws {
            nonisolated(unsafe) var paths: [String] = []
            MockURLProtocol.requestHandler = { request in
                paths.append(request.url!.path)
                return Self.respond(request, """
                {"conversation_id": "abc", "reply": "Policy says no.", "actions": [], "bookings_changed": false}
                """)
            }
            let store = ConversationStore(defaults: UserDefaults(suiteName: "OnDevice-\(UUID().uuidString)")!)
            let viewModel = AssistantViewModel(
                apiClient: client(),
                store: store,
                onDevice: assistant({ .init(kind: .other, day: nil) })
            )

            await viewModel.send("Why can't I book Saturday?")

            #expect(paths == ["/assistant/messages"])
            #expect(viewModel.messages[1].onDevice == false)
        }
    }
}
