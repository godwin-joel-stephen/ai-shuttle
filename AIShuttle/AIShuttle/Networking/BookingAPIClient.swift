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

    public init(
        baseURL: URL = URL(string: "http://127.0.0.1:8000")!,
        session: URLSession = .shared
    ) {
        self.baseURL = baseURL
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
}
