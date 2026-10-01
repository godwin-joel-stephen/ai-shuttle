//
//  BookingAPIClientTests.swift
//  AIShuttleTests
//

import AppIntents
import Foundation
import Testing
@testable import AIShuttle

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

@Suite(.serialized)
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
                "child_name": "Emma",
                "shuttle_name": "Morning Shuttle A",
                "route_name": "Home → School Morning Route",
                "pickup_location": "Home",
                "destination": "AI Shuttle Academy"
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
        #expect(first.childName == "Emma")
        #expect(first.shuttleName == "Morning Shuttle A")
        #expect(first.routeName == "Home → School Morning Route")
        #expect(first.pickupLocation == "Home")
        #expect(first.destination == "AI Shuttle Academy")
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

    @Test func intentExecutesWithMockedClient() async throws {

        let client = makeTestClient()
        let expectedJSON = """
        {
            "booking_id": 42,
            "message": "Shuttle booked successfully. Booking ID: 42."
        }
        """

        MockURLProtocol.requestHandler = { _ in
            let response = HTTPURLResponse(
                url: URL(string: "http://127.0.0.1:8000/bookings")!,
                statusCode: 200,
                httpVersion: nil,
                headerFields: ["Content-Type": "application/json"]
            )!
            return (response, expectedJSON.data(using: .utf8)!)
        }

        let intent = BookMyUsualShuttleIntent(apiClient: client)
        let _ = try await intent.perform()
    }

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

        let intent = BookMyUsualShuttleIntent(apiClient: client)
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
                "child_name": "Emma",
                "shuttle_name": "Morning Shuttle A",
                "route_name": "Home → School Morning Route",
                "pickup_location": "Home",
                "destination": "AI Shuttle Academy"
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
        #expect(viewModel.upcomingBooking?.childName == "Emma")
        #expect(viewModel.errorMessage == nil)
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

@Suite(.serialized)
struct LiveBookingIntegrationTests {
    @Test(.disabled("Deliberate live integration verification test only"))
    func liveEndToEndBookingVerification() async throws {
        let intent = BookMyUsualShuttleIntent()
        let _ = try await intent.perform()
    }
}
