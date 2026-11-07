//
//  BookingAPIClientTests.swift
//  AIShuttleTests
//

import AppIntents
import Foundation
import Testing
@testable import AIShuttle

/// Parent of every suite that sets `MockURLProtocol.requestHandler`. The
/// handler is process-wide and Swift Testing runs suites in parallel, so
/// those suites must nest here: `.serialized` applies to nested suites too.
@Suite(.serialized)
struct MockedNetworkTests {}

final class MockURLProtocol: URLProtocol, @unchecked Sendable {
    nonisolated(unsafe) static var requestHandler: ((URLRequest) throws -> (HTTPURLResponse, Data))?

    override class func canInit(with request: URLRequest) -> Bool {
        return true
    }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest {
        return request
    }

    override func startLoading() {
        guard let handler = MockURLProtocol.requestHandler else {
            client?.urlProtocol(self, didFailWithError: URLError(.unknown))
            return
        }

        do {
            let (response, data) = try handler(request)
            client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            client?.urlProtocol(self, didLoad: data)
            client?.urlProtocolDidFinishLoading(self)
        } catch {
            client?.urlProtocol(self, didFailWithError: error)
        }
    }

    override func stopLoading() {}
}

extension MockedNetworkTests {
    @Suite
    @MainActor
    struct BookingAPIClientTests {
        private func makeTestClient() -> BookingAPIClient {
            let configuration = URLSessionConfiguration.ephemeral
            configuration.protocolClasses = [MockURLProtocol.self]
            let session = URLSession(configuration: configuration)
            return BookingAPIClient(baseURL: URL(string: "http://127.0.0.1:8000")!, session: session)
        }

        @Test func successfulBookingDecodesCorrectly() async throws {
            let client = makeTestClient()
            let expectedJSON = """
            {
                "booking_id": 42,
                "message": "Shuttle booked successfully. Booking ID: 42."
            }
            """

            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.absoluteString == "http://127.0.0.1:8000/bookings")
                #expect(request.httpMethod == "POST")
                #expect(request.value(forHTTPHeaderField: "Content-Type") == "application/json")

                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, expectedJSON.data(using: .utf8)!)
            }

            let result = try await client.bookUsualShuttle(userId: 1, message: "Book my usual shuttle for tomorrow.")
            #expect(result.bookingId == 42)
            #expect(result.message == "Shuttle booked successfully. Booking ID: 42.")
        }

        @Test func non2xxResponseThrowsError() async {
            let client = makeTestClient()

            MockURLProtocol.requestHandler = { request in
                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 500,
                    httpVersion: nil,
                    headerFields: nil
                )!
                return (response, Data())
            }

            await #expect(throws: BookingAPIError.self) {
                try await client.bookUsualShuttle(userId: 1, message: "Book my usual shuttle for tomorrow.")
            }
        }

        @Test func malformedJSONThrowsDecodingError() async {
            let client = makeTestClient()
            let badJSON = "{\"invalid\": \"payload\"}"

            MockURLProtocol.requestHandler = { request in
                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, badJSON.data(using: .utf8)!)
            }

            await #expect(throws: BookingAPIError.self) {
                try await client.bookUsualShuttle(userId: 1, message: "Book my usual shuttle for tomorrow.")
            }
        }

        @Test func fetchUpcomingBookingsDecodesSuccessfully() async throws {
            let client = makeTestClient()
            let expectedJSON = """
            [
                {
                    "id": 101,
                    "booking_date": "2026-10-02",
                    "pickup_time": "07:30:00",
                    "status": "confirmed",
                    "shuttle_name": "Morning Shuttle C",
                    "route_name": "Home → Office Morning Route",
                    "pickup_location": "Home",
                    "destination": "Office"
                }
            ]
            """

            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.absoluteString == "http://127.0.0.1:8000/bookings?user_id=1")
                #expect(request.httpMethod == "GET")
                #expect(request.value(forHTTPHeaderField: "Accept") == "application/json")

                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, expectedJSON.data(using: .utf8)!)
            }

            let bookings = try await client.fetchUpcomingBookings(userId: 1)
            #expect(bookings.count == 1)
            let first = bookings[0]
            #expect(first.id == 101)
            #expect(first.bookingDate == "2026-10-02")
            #expect(first.pickupTime == "07:30:00")
            #expect(first.formattedPickupTime == "7:30 AM")
            #expect(first.tripTitle == "Home → Office")
            #expect(first.shuttleName == "Morning Shuttle C")
            #expect(first.routeName == "Home → Office Morning Route")
            #expect(first.pickupLocation == "Home")
            #expect(first.destination == "Office")
        }

        @Test func fetchUpcomingBookingsEmptyListDecodesCorrectly() async throws {
            let client = makeTestClient()
            let expectedJSON = "[]"

            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.absoluteString == "http://127.0.0.1:8000/bookings?user_id=1")
                #expect(request.httpMethod == "GET")

                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, expectedJSON.data(using: .utf8)!)
            }

            let bookings = try await client.fetchUpcomingBookings(userId: 1)
            #expect(bookings.isEmpty)
        }

        @Test func fetchUpcomingBookingsNon2xxThrowsError() async {
            let client = makeTestClient()

            MockURLProtocol.requestHandler = { request in
                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 500,
                    httpVersion: nil,
                    headerFields: nil
                )!
                return (response, Data())
            }

            await #expect(throws: BookingAPIError.self) {
                _ = try await client.fetchUpcomingBookings(userId: 1)
            }
        }

        @Test func fetchUpcomingBookingsMalformedJSONThrowsDecodingError() async {
            let client = makeTestClient()
            let badJSON = "{\"not\": \"an array\"}"

            MockURLProtocol.requestHandler = { request in
                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, badJSON.data(using: .utf8)!)
            }

            await #expect(throws: BookingAPIError.self) {
                _ = try await client.fetchUpcomingBookings(userId: 1)
            }
        }

        @Test func intentSendsStructuredDateAndSucceeds() async throws {
            let client = makeTestClient()
            let expectedDay = BookingAPIClient.isoDay(BookingDay.friday.date())

            MockURLProtocol.requestHandler = { request in
                let body = try JSONSerialization.jsonObject(with: request.bodyData) as? [String: Any]
                #expect(body?["booking_date"] as? String == expectedDay)
                #expect(body?["message"] == nil)
                let response = HTTPURLResponse(
                    url: URL(string: "http://127.0.0.1:8000/bookings")!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, Self.bookingResponseJSON.data(using: .utf8)!)
            }

            let intent = BookMyUsualShuttleIntent(day: .friday, apiClient: client)
            let _ = try await intent.perform()
        }

        @Test func serverDetailBecomesSpokenError() async {
            let client = makeTestClient()

            MockURLProtocol.requestHandler = { request in
                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 409,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, #"{"detail": "That date has already passed."}"#.data(using: .utf8)!)
            }

            do {
                _ = try await client.bookUsualShuttle(userId: 1, on: .now)
                Issue.record("Expected an error")
            } catch {
                #expect(error as? BookingAPIError == .serverMessage(statusCode: 409, message: "That date has already passed."))
                #expect(error.localizedDescription == "That date has already passed.")
            }
        }

        @Test func rescheduleDecodesUpdatedBooking() async throws {
            let client = makeTestClient()

            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.absoluteString == "http://127.0.0.1:8000/bookings/42/reschedule")
                let body = try JSONSerialization.jsonObject(with: request.bodyData) as? [String: Any]
                #expect(body?["direction"] as? String == "earlier")

                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, Self.bookingResponseJSON.data(using: .utf8)!)
            }

            let result = try await client.rescheduleBooking(id: 42, direction: .earlier)
            #expect(result.booking?.earlierAvailable == true)
            #expect(result.booking?.formattedArrivalTime == "8:15 AM")
        }

        @Test func dialogReadsNaturally() throws {
            let response = try JSONDecoder().decode(
                BookingResponse.self,
                from: Self.bookingResponseJSON.data(using: .utf8)!
            )

            #expect(
                response.spokenConfirmation
                    == "Done. You're on the 7:30 AM shuttle \(response.booking!.spokenDay), arriving at Office by 8:15 AM."
            )
        }

        @Test func bookingDayResolvesRelativeToToday() {
            var calendar = Calendar(identifier: .gregorian)
            calendar.timeZone = TimeZone(identifier: "Asia/Kolkata")!
            // Monday, 2 November 2026, 9 PM.
            let reference = calendar.date(from: DateComponents(year: 2026, month: 11, day: 2, hour: 21))!

            func day(_ value: BookingDay) -> Int {
                calendar.component(.day, from: value.date(from: reference, calendar: calendar))
            }

            #expect(day(.today) == 2)
            #expect(day(.tomorrow) == 3)
            #expect(day(.friday) == 6)
            #expect(day(.monday) == 9)
        }

        static let bookingResponseJSON = """
        {
            "booking_id": 42,
            "message": "Done. You're booked on the 7:30 AM shuttle.",
            "already_booked": false,
            "booking": {
                "id": 42,
                "booking_date": "2026-11-03",
                "pickup_time": "07:30:00",
                "arrival_time": "08:15:00",
                "status": "confirmed",
                "shuttle_name": "Morning Shuttle C",
                "route_name": "Home → Office Morning Route",
                "pickup_location": "Home",
                "destination": "Office",
                "earlier_available": true,
                "later_available": true
            }
        }
        """

        @Test func intentThrowsWhenBookingFails() async {
            let client = makeTestClient()

            MockURLProtocol.requestHandler = { _ in
                let response = HTTPURLResponse(
                    url: URL(string: "http://127.0.0.1:8000/bookings")!,
                    statusCode: 503,
                    httpVersion: nil,
                    headerFields: nil
                )!
                return (response, Data())
            }

            let intent = BookMyUsualShuttleIntent(day: .monday, apiClient: client)
            await #expect(throws: BookingIntentError.self) {
                try await intent.perform()
            }
        }

        @Test func viewModelLoadsBookingsSuccessfully() async {
            let client = makeTestClient()
            let expectedJSON = """
            [
                {
                    "id": 1,
                    "booking_date": "2026-10-02",
                    "pickup_time": "07:30:00",
                    "status": "confirmed",
                    "shuttle_name": "Morning Shuttle C",
                    "route_name": "Home → Office Morning Route",
                    "pickup_location": "Home",
                    "destination": "Office"
                }
            ]
            """
            MockURLProtocol.requestHandler = { _ in
                let response = HTTPURLResponse(
                    url: URL(string: "http://127.0.0.1:8000/bookings?user_id=1")!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, expectedJSON.data(using: .utf8)!)
            }

            let viewModel = RidesViewModel(apiClient: client)
            #expect(viewModel.state == .idle)
            #expect(viewModel.upcomingBooking == nil)

            await viewModel.loadBookings()

            #expect(viewModel.bookings.count == 1)
            #expect(viewModel.upcomingBooking?.id == 1)
            #expect(viewModel.upcomingBooking?.tripTitle == "Home → Office")
            #expect(viewModel.errorMessage == nil)
        }

        @Test func viewModelSurvivesCancelledCallersAndJoinsLoads() async {
            let client = makeTestClient()
            nonisolated(unsafe) var requestCount = 0
            MockURLProtocol.requestHandler = { request in
                // A load also refreshes /habits; count the rides requests.
                if request.url?.path == "/bookings" {
                    requestCount += 1
                }
                Thread.sleep(forTimeInterval: 0.2)
                let response = HTTPURLResponse(
                    url: request.url!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, "[]".data(using: .utf8)!)
            }

            let viewModel = RidesViewModel(apiClient: client)

            // Simulate a tab switch: the first `.task` is cancelled mid-load
            // while the other tab starts its own load.
            let cancelled = Task { await viewModel.loadBookings() }
            try? await Task.sleep(for: .milliseconds(50))
            cancelled.cancel()
            await viewModel.loadBookings()

            #expect(viewModel.state == .loaded([]))
            #expect(requestCount == 1)
        }

        @Test func viewModelHandlesEmptyBookings() async {
            let client = makeTestClient()
            MockURLProtocol.requestHandler = { _ in
                let response = HTTPURLResponse(
                    url: URL(string: "http://127.0.0.1:8000/bookings?user_id=1")!,
                    statusCode: 200,
                    httpVersion: nil,
                    headerFields: ["Content-Type": "application/json"]
                )!
                return (response, "[]".data(using: .utf8)!)
            }

            let viewModel = RidesViewModel(apiClient: client)
            await viewModel.loadBookings()

            #expect(viewModel.bookings.isEmpty)
            #expect(viewModel.upcomingBooking == nil)
            #expect(viewModel.errorMessage == nil)
        }

        @Test func viewModelHandlesErrorState() async {
            let client = makeTestClient()
            MockURLProtocol.requestHandler = { _ in
                let response = HTTPURLResponse(
                    url: URL(string: "http://127.0.0.1:8000/bookings?user_id=1")!,
                    statusCode: 500,
                    httpVersion: nil,
                    headerFields: nil
                )!
                return (response, Data())
            }

            let viewModel = RidesViewModel(apiClient: client)
            await viewModel.loadBookings()

            #expect(viewModel.bookings.isEmpty)
            #expect(viewModel.errorMessage != nil)
        }
    }
}

extension URLRequest {
    /// URLProtocol receives uploads as a body stream, not `httpBody`.
    var bodyData: Data {
        if let httpBody { return httpBody }
        guard let stream = httpBodyStream else { return Data() }
        stream.open()
        defer { stream.close() }
        var data = Data()
        var buffer = [UInt8](repeating: 0, count: 1024)
        while stream.hasBytesAvailable {
            let count = stream.read(&buffer, maxLength: buffer.count)
            guard count > 0 else { break }
            data.append(buffer, count: count)
        }
        return data
    }
}

@Suite(.serialized)
struct LiveBookingIntegrationTests {
    @Test(.disabled("Deliberate live integration verification test only"))
    func liveEndToEndBookingVerification() async throws {
        let intent = BookMyUsualShuttleIntent()
        let _ = try await intent.perform()
    }
}
