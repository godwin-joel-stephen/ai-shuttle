//
//  BookingAPIClient.swift
//  AIShuttle
//

import Foundation

public enum BookingAPIError: Error, LocalizedError, Equatable {
    case invalidURL
    case networkError(String)
    case httpError(statusCode: Int)
    case decodingError(String)

    public var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The booking server URL is invalid."
        case .networkError(let message):
            return "Network failure: \(message)"
        case .httpError(let statusCode):
            return "Server returned non-2xx status code: \(statusCode)"
        case .decodingError(let message):
            return "Failed to decode booking response: \(message)"
        }
    }
}

public final class BookingAPIClient: Sendable {
    public let baseURL: URL
    private let session: URLSession

    nonisolated public init(
        baseURL: URL? = nil,
        session: URLSession = .shared
    ) {
        #if targetEnvironment(simulator)
        let defaultURL = URL(
            string: "http://127.0.0.1:8000"
        )!
        #else
        let defaultURL = URL(
            string: "http://192.168.1.6:8000"
        )!
        #endif

        self.baseURL = baseURL ?? defaultURL
        self.session = session
    }


    public func bookUsualShuttle(
        userId: Int = 1,
        message: String = "Book my usual shuttle for tomorrow."
    ) async throws -> BookingResponse {
        let endpoint = baseURL.appendingPathComponent("bookings")
        guard endpoint.scheme != nil, endpoint.host != nil else {
            throw BookingAPIError.invalidURL
        }

        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let requestDTO = BookingRequest(userId: userId, message: message)
        do {
            request.httpBody = try JSONEncoder().encode(requestDTO)
        } catch {
            throw BookingAPIError.networkError(error.localizedDescription)
        }

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
            throw BookingAPIError.httpError(statusCode: httpResponse.statusCode)
        }

        do {
            return try JSONDecoder().decode(BookingResponse.self, from: data)
        } catch {
            throw BookingAPIError.decodingError(error.localizedDescription)
        }
    }

    public func fetchUpcomingBookings(userId: Int = 1) async throws -> [BookingDetailDTO] {
        var components = URLComponents(url: baseURL.appendingPathComponent("bookings"), resolvingAgainstBaseURL: true)
        components?.queryItems = [
            URLQueryItem(name: "user_id", value: String(userId))
        ]

        guard let endpoint = components?.url, endpoint.scheme != nil, endpoint.host != nil else {
            throw BookingAPIError.invalidURL
        }

        var request = URLRequest(url: endpoint)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")

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
            throw BookingAPIError.httpError(statusCode: httpResponse.statusCode)
        }

        do {
            return try JSONDecoder().decode([BookingDetailDTO].self, from: data)
        } catch {
            throw BookingAPIError.decodingError(error.localizedDescription)
        }
    }
}
