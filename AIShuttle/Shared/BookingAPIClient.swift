//
//  BookingAPIClient.swift
//  AIShuttle
//

import Foundation

public enum BookingAPIError: Error, LocalizedError, Equatable {
    case invalidURL
    case networkError(String)
    case httpError(statusCode: Int)
    /// The server rejected the request with a user-facing reason.
    case serverMessage(statusCode: Int, message: String)
    case decodingError(String)

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The booking server URL is invalid."
        case .networkError(let message):
            return "Network failure: \(message)"
        case .httpError(let statusCode):
            return "Server returned non-2xx status code: \(statusCode)"
        case .serverMessage(_, let message):
            return message
        case .decodingError(let message):
            return "Failed to decode booking response: \(message)"
        }
    }
}

/// Response type for endpoints that return no body (204 No Content).
struct NoContent: Decodable {}

public final class BookingAPIClient: Sendable {
    /// Override per environment with the `BookingAPIBaseURL` Info.plist key.
    nonisolated static let defaultBaseURL: URL = {
        if let value = Bundle.main.object(forInfoDictionaryKey: "BookingAPIBaseURL") as? String,
           let url = URL(string: value) {
            return url
        }
        return URL(string: "http://192.168.1.6:8000")!
    }()

    public let baseURL: URL
    private let session: URLSession

    nonisolated public init(
        baseURL: URL? = nil,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL ?? Self.defaultBaseURL
        self.session = session
    }

    /// Fails within seconds instead of URLSession's 60s default. Siri gives
    /// up on intents that run too long, and the app shouldn't spin forever.
    nonisolated public static func withTimeouts() -> BookingAPIClient {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 15
        configuration.timeoutIntervalForResource = 20
        return BookingAPIClient(session: URLSession(configuration: configuration))
    }

    public func bookUsualShuttle(
        userId: Int = 1,
        message: String = "Book my usual shuttle for tomorrow."
    ) async throws -> BookingResponse {
        try await post("bookings", body: BookingRequest(userId: userId, message: message))
    }

    /// Structured booking: the backend skips LLM interpretation.
    public func bookUsualShuttle(
        userId: Int = 1,
        on date: Date
    ) async throws -> BookingResponse {
        try await post(
            "bookings",
            body: BookingRequest(userId: userId, bookingDate: Self.isoDay(date))
        )
    }

    public func rescheduleBooking(
        id bookingId: Int,
        direction: RescheduleDirectionDTO,
        userId: Int = 1
    ) async throws -> BookingResponse {
        try await post(
            "bookings/\(bookingId)/reschedule",
            body: RescheduleRequest(userId: userId, direction: direction)
        )
    }

    public func fetchBooking(id bookingId: Int, userId: Int = 1) async throws -> BookingDetailDTO {
        try await get("bookings/\(bookingId)", userId: userId)
    }

    public func fetchUpcomingBookings(userId: Int = 1) async throws -> [BookingDetailDTO] {
        try await get("bookings", userId: userId)
    }

    // MARK: - Transport
    // Internal (not private) so feature-specific extensions can reuse them.

    func post<Body: Encodable, Response: Decodable>(
        _ path: String,
        body: Body
    ) async throws -> Response {
        let endpoint = baseURL.appendingPathComponent(path)
        guard endpoint.scheme != nil, endpoint.host != nil else {
            throw BookingAPIError.invalidURL
        }

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            request.httpBody = try JSONEncoder().encode(body)
        } catch {
            throw BookingAPIError.networkError(error.localizedDescription)
        }

        return try await send(request)
    }

    func get<Response: Decodable>(_ path: String, userId: Int) async throws -> Response {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: true)
        components?.queryItems = [
            URLQueryItem(name: "user_id", value: String(userId))
        ]

        guard let endpoint = components?.url, endpoint.scheme != nil, endpoint.host != nil else {
            throw BookingAPIError.invalidURL
        }

        var request = URLRequest(url: endpoint)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        return try await send(request)
    }

    private func send<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw BookingAPIError.networkError(error.localizedDescription)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw BookingAPIError.networkError("Invalid HTTP response.")
        }

        guard (200...299).contains(httpResponse.statusCode) else {
            if let body = try? JSONDecoder().decode(APIErrorBody.self, from: data) {
                throw BookingAPIError.serverMessage(statusCode: httpResponse.statusCode, message: body.detail)
            }
            throw BookingAPIError.httpError(statusCode: httpResponse.statusCode)
        }

        do {
            // 204 responses have no body; decode NoContent from an empty object.
            return try Self.decoder.decode(Response.self, from: data.isEmpty ? Data("{}".utf8) : data)
        } catch {
            throw BookingAPIError.decodingError(error.localizedDescription)
        }
    }

    /// Decodes ISO 8601 timestamps with UTC offset (e.g. tracking ETAs).
    nonisolated static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    /// `yyyy-MM-dd` in the device's calendar, so "tomorrow" means the
    /// user's tomorrow regardless of the server's time zone.
    static func isoDay(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .gregorian)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = .current
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: date)
    }
}
