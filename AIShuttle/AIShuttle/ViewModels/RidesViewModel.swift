//
//  RidesViewModel.swift
//  AIShuttle
//

import Foundation
import Observation

@MainActor
@Observable
public final class RidesViewModel {
    public enum ViewState: Equatable {
        case idle
        case loading
        case loaded([BookingDetailDTO])
        case error(String)
    }

    public var state: ViewState = .idle
    private let apiClient: BookingAPIClient

    public init(apiClient: BookingAPIClient? = nil) {
        self.apiClient = apiClient ?? BookingAPIClient()
    }


    public var bookings: [BookingDetailDTO] {
        if case .loaded(let list) = state {
            return list
        }
        return []
    }

    public var upcomingBooking: BookingDetailDTO? {
        bookings.first
    }

    public var isLoading: Bool {
        if case .loading = state {
            return true
        }
        return false
    }

    public var errorMessage: String? {
        if case .error(let msg) = state {
            return msg
        }
        return nil
    }

    public func loadBookings() async {
        state = .loading
        do {
            let fetched = try await apiClient.fetchUpcomingBookings(userId: 1)
            state = .loaded(fetched)
        } catch let error as BookingAPIError {
            state = .error(error.localizedDescription)
        } catch {
            state = .error("Unable to load your rides. Please try again.")
        }
    }
}
