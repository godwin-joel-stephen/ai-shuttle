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
    /// The learned commute habit (F10); nil until loaded or if it failed.
    public var habits: HabitsDTO?
    private let apiClient: BookingAPIClient
    private var inFlightLoad: Task<Void, Never>?

    public init(apiClient: BookingAPIClient? = nil) {
        self.apiClient = apiClient ?? .withTimeouts()
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

    /// Both tabs share this model and call this from `.task`, which SwiftUI
    /// cancels on every tab switch. Run the request in an unstructured task
    /// so a cancelled caller can't abort it, and join any load in progress
    /// instead of starting a competing one.
    public func loadBookings() async {
        if let inFlightLoad {
            await inFlightLoad.value
            return
        }

        let load = Task { await performLoad() }
        inFlightLoad = load
        await load.value
        inFlightLoad = nil
    }

    private func performLoad() async {
        // Keep showing loaded rides during a refresh instead of a spinner.
        if case .loaded = state {} else {
            state = .loading
        }

        do {
            let fetched = try await fetchWithRetry()
            state = .loaded(fetched)
            await syncHabits(bookings: fetched)
        } catch let error as BookingAPIError {
            state = .error(error.localizedDescription)
        } catch {
            state = .error("Unable to load your rides. Please try again.")
        }
    }

    /// Refreshes the habit and hands it to the OS: donations for new
    /// bookings and reminders for usual days not booked yet.
    private func syncHabits(bookings: [BookingDetailDTO]) async {
        await HabitDonations.donateNewBookings(bookings)
        guard let fetched = try? await apiClient.fetchHabits(userId: 1) else { return }
        habits = fetched
        await HabitReminders.schedule(fetched)
    }

    /// Books a day's usual shuttle from the habit card; returns what to
    /// show the rider.
    public func bookUsual(on day: UpcomingHabitDayDTO) async -> String {
        guard let date = day.day else { return "That day isn't valid." }
        do {
            let response = try await apiClient.bookUsualShuttle(userId: 1, on: date)
            HabitReminderID.withdraw(for: date)
            await loadBookings()
            return response.spokenConfirmation
        } catch {
            return String(localized: BookingIntentError(error).localizedStringResource)
        }
    }

    /// Pins a shuttle as the usual every day, or unpins with nil.
    public func pinUsual(shuttleId: Int?) async {
        guard let updated = try? await apiClient.pinUsual(shuttleId: shuttleId, userId: 1) else { return }
        habits = updated
        await HabitReminders.schedule(updated)
    }

    /// The first request after launch can fail while iOS brings up Wi-Fi or
    /// the local network permission, so retry a connection failure once.
    private func fetchWithRetry() async throws -> [BookingDetailDTO] {
        do {
            return try await apiClient.fetchUpcomingBookings(userId: 1)
        } catch BookingAPIError.networkError {
            try await Task.sleep(for: .seconds(1))
            return try await apiClient.fetchUpcomingBookings(userId: 1)
        }
    }
}
