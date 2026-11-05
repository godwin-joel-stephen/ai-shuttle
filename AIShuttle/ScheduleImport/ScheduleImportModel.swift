//
//  ScheduleImportModel.swift
//  read → understand (on-device) → plan (server rules) → review → apply.
//

import Foundation
import Observation
import WidgetKit

@Observable
final class ScheduleImportModel {
    enum Phase: Equatable {
        case reading
        case understanding
        case planning
        case review
        case applying
        case done
        case failed(String)

        var progressText: String? {
            switch self {
            case .reading: "Reading your schedule…"
            case .understanding: "Understanding it on this iPhone…"
            case .planning: "Checking your bookings…"
            case .applying: "Updating your bookings…"
            default: nil
            }
        }
    }

    private(set) var phase: Phase = .reading
    private(set) var documentText = ""
    private(set) var extraction: ScheduleExtraction?
    private(set) var plan: SchedulePlanDTO?
    private(set) var result: ScheduleApplyDTO?
    /// Dates the user wants changed; starts with every proposed change.
    var selectedDates: Set<String> = []

    private let loadSource: () async throws -> ScheduleSource
    private let client: BookingAPIClient
    private let extractor: ScheduleExtractor
    private let onApplied: () async -> Void

    init(
        client: BookingAPIClient = .withTimeouts(),
        extractor: ScheduleExtractor = ScheduleExtractor(),
        loadSource: @escaping () async throws -> ScheduleSource,
        onApplied: @escaping () async -> Void = {}
    ) {
        self.client = client
        self.extractor = extractor
        self.loadSource = loadSource
        self.onApplied = onApplied
    }

    var changes: [ScheduleDayResultDTO] {
        plan?.days.filter { $0.action.changesBookings } ?? []
    }

    var selectedChangeCount: Int {
        changes.filter { selectedDates.contains($0.date) }.count
    }

    func start() async {
        do {
            phase = .reading
            documentText = try await ScheduleTextReader.read(try await loadSource())

            phase = .understanding
            let extraction = await extractor.extract(from: documentText)
            self.extraction = extraction
            guard !extraction.days.isEmpty else {
                throw ScheduleImportError.noDays
            }

            try await makePlan()
        } catch {
            phase = .failed(Self.message(for: error))
        }
    }

    /// After a network failure, retry without re-reading the document.
    func retry() async {
        guard let extraction, !extraction.days.isEmpty else {
            await start()
            return
        }
        do {
            try await makePlan()
        } catch {
            phase = .failed(Self.message(for: error))
        }
    }

    private func makePlan() async throws {
        guard let extraction else { return }
        phase = .planning
        let plan = try await client.planSchedule(extraction.days)
        self.plan = plan
        selectedDates = Set(plan.days.filter { $0.action.changesBookings }.map(\.date))
        phase = .review
    }

    func toggle(_ date: String) {
        if selectedDates.contains(date) {
            selectedDates.remove(date)
        } else {
            selectedDates.insert(date)
        }
    }

    func apply() async {
        guard let extraction else { return }
        let approved = extraction.days.filter { selectedDates.contains($0.date) }
        guard !approved.isEmpty else { return }

        phase = .applying
        do {
            let result = try await client.applySchedule(approved)
            self.result = result
            phase = .done
            if result.bookingsChanged {
                WidgetCenter.shared.reloadAllTimelines()
                await onApplied()
            }
        } catch {
            // The server may have changed some days before failing;
            // say so rather than imply nothing happened.
            phase = .failed(
                "\(Self.message(for: error)) Some days may have changed; check Rides before trying again."
            )
        }
    }

    static func message(for error: Error) -> String {
        if case BookingAPIError.networkError = error {
            return "Clear Path couldn't reach the booking server."
        }
        return (error as? LocalizedError)?.errorDescription ?? error.localizedDescription
    }
}
