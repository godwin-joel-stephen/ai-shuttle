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
}

@Suite(.serialized)
struct LiveBookingIntegrationTests {
    @Test(.disabled("Deliberate live integration verification test only"))
    func liveEndToEndBookingVerification() async throws {
        let intent = BookMyUsualShuttleIntent()
        let _ = try await intent.perform()
    }
}
