//
//  TrackingTests.swift
//  AIShuttleTests
//

import Foundation
import Testing
@testable import AIShuttle

extension MockedNetworkTests {
    @Suite
    @MainActor
    struct TrackingTests {
        static let tripJSON = """
        {
            "booking_id": 47,
            "booking_date": "2026-11-03",
            "shuttle_name": "Morning Shuttle C",
            "phase": "approaching",
            "message": "Your shuttle is 12 minutes from Home.",
            "delay_minutes": 0,
            "minutes_to_pickup": 12,
            "minutes_to_arrival": 57,
            "pickup_eta": "2026-11-02T17:47:53+05:30",
            "arrival_eta": "2026-11-02T18:32:53+05:30",
            "progress": 0.05,
            "position": {"latitude": 12.9612, "longitude": 77.6471},
            "pickup": {"latitude": 12.9719, "longitude": 77.6412},
            "destination": {"latitude": 13.045, "longitude": 77.6205},
            "pickup_name": "Home",
            "destination_name": "Office",
            "route": [{"latitude": 12.9719, "longitude": 77.6412}, {"latitude": 13.045, "longitude": 77.6205}],
            "simulated": true
        }
        """

        @Test func fetchNextTripDecodesTimestampsWithOffset() async throws {
            let configuration = URLSessionConfiguration.ephemeral
            configuration.protocolClasses = [MockURLProtocol.self]
            let client = BookingAPIClient(baseURL: URL(string: "http://127.0.0.1:8000")!, session: URLSession(configuration: configuration))
            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.absoluteString == "http://127.0.0.1:8000/tracking/next?user_id=1")
                let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
                return (response, Self.tripJSON.data(using: .utf8)!)
            }

            let trip = try await client.fetchNextTrip()

            #expect(trip.isLive)
            #expect(trip.route.count == 2)
            // 17:47:53 IST is 12:17:53 UTC.
            #expect(trip.pickupEta == ISO8601DateFormatter().date(from: "2026-11-02T12:17:53Z"))
        }

        @Test func activityStateProgressBarStartsWhereTrackingBegan() throws {
            let trip = try BookingAPIClient.decoder.decode(TripStatusDTO.self, from: Self.tripJSON.data(using: .utf8)!)
            let now = trip.arrivalEta.addingTimeInterval(-950)  // 95% of the window left

            let state = trip.activityState(now: now)

            // progress 0.05 with 950s remaining -> the window began 50s ago.
            #expect(abs(state.windowStart.timeIntervalSince(now) + 50) < 0.001)
            #expect(state.countdownTarget == trip.pickupEta)
            #expect(state.countdownCaption == "to pickup")
        }

        @Test func tripModeFieldsDecodeAndReadNaturally() throws {
            var json = try JSONSerialization.jsonObject(with: Self.tripJSON.data(using: .utf8)!) as! [String: Any]
            json["delay_minutes"] = 20
            json["walk_minutes"] = 17
            json["leave_in_minutes"] = -2
            json["alternative"] = [
                "shuttle_id": 4, "shuttle_name": "Morning Shuttle D",
                "departure": "07:45", "arrival": "08:30", "minutes_earlier": 5
            ]
            let trip = try BookingAPIClient.decoder.decode(
                TripStatusDTO.self,
                from: JSONSerialization.data(withJSONObject: json)
            )

            #expect(trip.departureAdvice == "17 min walk · leave now")
            #expect(trip.alternative?.formattedDeparture == "7:45 AM")
            #expect(trip.alternative?.minutesEarlier == 5)
        }

        @Test func departureAdviceWithoutLocationIsHidden() throws {
            let trip = try BookingAPIClient.decoder.decode(TripStatusDTO.self, from: Self.tripJSON.data(using: .utf8)!)

            #expect(trip.walkMinutes == nil)
            #expect(trip.departureAdvice == nil)
            #expect(trip.alternative == nil)
        }

        @Test func reportLocationAcceptsEmptyNoContentResponse() async throws {
            let client = makeClient()
            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.absoluteString == "http://127.0.0.1:8000/users/1/location")
                let body = try JSONSerialization.jsonObject(with: request.bodyData) as? [String: Double]
                #expect(body?["latitude"] == 12.98)
                let response = HTTPURLResponse(url: request.url!, statusCode: 204, httpVersion: nil, headerFields: nil)!
                return (response, Data())
            }

            try await client.reportLocation(latitude: 12.98, longitude: 77.64)
        }

        @Test func moveBookingPostsShuttleAndDecodesTrip() async throws {
            let client = makeClient()
            MockURLProtocol.requestHandler = { request in
                #expect(request.url?.absoluteString == "http://127.0.0.1:8000/bookings/47/move")
                let body = try JSONSerialization.jsonObject(with: request.bodyData) as? [String: Int]
                #expect(body?["shuttle_id"] == 4)
                let response = HTTPURLResponse(url: request.url!, statusCode: 200, httpVersion: nil, headerFields: nil)!
                return (response, Self.tripJSON.data(using: .utf8)!)
            }

            let trip = try await client.moveBooking(id: 47, toShuttle: 4)
            #expect(trip.bookingId == 47)
        }

        private func makeClient() -> BookingAPIClient {
            let configuration = URLSessionConfiguration.ephemeral
            configuration.protocolClasses = [MockURLProtocol.self]
            return BookingAPIClient(baseURL: URL(string: "http://127.0.0.1:8000")!, session: URLSession(configuration: configuration))
        }

        @Test func countdownSwitchesToArrivalOnceAboard() {
            let state = ShuttleActivityAttributes.ContentState(
                phase: "in_transit",
                message: "On the way.",
                pickupETA: .now,
                arrivalETA: .now.addingTimeInterval(600),
                delayMinutes: 0,
                windowStart: .now.addingTimeInterval(-600)
            )

            #expect(state.countdownTarget == state.arrivalETA)
            #expect(state.countdownCaption == "to arrival")
        }
    }
}
