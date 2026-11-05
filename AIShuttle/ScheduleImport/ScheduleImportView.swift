//
//  ScheduleImportView.swift
//  Review screen shared by the share extension and the app.
//

import SwiftUI

struct ScheduleImportView: View {
    @State var model: ScheduleImportModel
    let onClose: () -> Void

    var body: some View {
        NavigationStack {
            content
                .navigationTitle("Import Schedule")
                .navigationBarTitleDisplayMode(.inline)
                .toolbar {
                    ToolbarItem(placement: .cancellationAction) {
                        if model.phase != .done {
                            Button("Cancel", action: onClose)
                                .disabled(model.phase == .applying)
                        }
                    }
                    ToolbarItem(placement: .confirmationAction) {
                        if model.phase == .done {
                            Button("Done", action: onClose)
                        }
                    }
                }
        }
        .task { await model.start() }
    }

    @ViewBuilder
    private var content: some View {
        switch model.phase {
        case .reading, .understanding, .planning, .applying:
            progress
        case .review:
            review
        case .done:
            done
        case .failed(let message):
            failure(message)
        }
    }

    // MARK: - Progress

    private var progress: some View {
        VStack(spacing: 14) {
            ProgressView()
                .controlSize(.large)
            Text(model.phase.progressText ?? "")
                .font(.headline)
            Label("Your document never leaves this iPhone", systemImage: "lock.iphone")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Review

    private var review: some View {
        List {
            if let plan = model.plan {
                Section {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(plan.summary)
                            .font(.title3.weight(.semibold))
                        methodLabel
                    }
                    .padding(.vertical, 4)
                }

                safetySection

                Section {
                    ForEach(plan.days) { day in
                        DayRow(
                            day: day,
                            isSelected: model.selectedDates.contains(day.date),
                            toggle: { model.toggle(day.date) }
                        )
                    }
                } header: {
                    Text("From your schedule")
                } footer: {
                    skippedFooter
                }

                Section {
                    DisclosureGroup("Text read from your document") {
                        Text(model.documentText)
                            .font(.caption.monospaced())
                            .foregroundStyle(.secondary)
                            .textSelection(.enabled)
                    }
                }
            }
        }
        .safeAreaInset(edge: .bottom) {
            applyBar
        }
    }

    private var methodLabel: some View {
        Group {
            if let extraction = model.extraction {
                switch extraction.method {
                case .onDevice:
                    Label("Read on this iPhone with Apple Intelligence", systemImage: "sparkles")
                case .rules:
                    Label(
                        "Read on this iPhone with text rules (\(extraction.fallbackReason ?? "model unavailable"))",
                        systemImage: "text.magnifyingglass"
                    )
                }
            }
        }
        .font(.caption)
        .foregroundStyle(.secondary)
    }

    @ViewBuilder
    private var safetySection: some View {
        if let ignored = model.extraction?.ignoredLines, !ignored.isEmpty {
            Section {
                VStack(alignment: .leading, spacing: 8) {
                    Label(
                        ignored.count == 1
                            ? "Ignored 1 line that looked like instructions to an AI"
                            : "Ignored \(ignored.count) lines that looked like instructions to an AI",
                        systemImage: "exclamationmark.shield.fill"
                    )
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.orange)

                    ForEach(Array(ignored.prefix(5).enumerated()), id: \.offset) { _, line in
                        Text("“\(line)”")
                            .font(.caption.monospaced())
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }

                    Text("Only the days below were read. Check them before applying.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
    }

    @ViewBuilder
    private var skippedFooter: some View {
        if let extraction = model.extraction {
            let notes = [
                extraction.pastDays > 0
                    ? "\(extraction.pastDays) earlier day\(extraction.pastDays == 1 ? "" : "s") skipped." : nil,
                extraction.discarded > 0
                    ? "\(extraction.discarded) entr\(extraction.discarded == 1 ? "y" : "ies") couldn't be matched to a date." : nil,
            ].compactMap { $0 }
            if !notes.isEmpty {
                Text(notes.joined(separator: " "))
            }
        }
    }

    private var applyBar: some View {
        let count = model.selectedChangeCount
        return VStack {
            if model.changes.isEmpty {
                Button(action: onClose) {
                    Text("Done").frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
            } else {
                Button {
                    Task { await model.apply() }
                } label: {
                    Text(count == 1 ? "Apply 1 Change" : "Apply \(count) Changes")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(count == 0)
            }
        }
        .controlSize(.large)
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(.bar)
    }

    // MARK: - Done

    private var done: some View {
        List {
            if let result = model.result {
                Section {
                    Label(result.summary, systemImage: "checkmark.circle.fill")
                        .font(.title3.weight(.semibold))
                        .foregroundStyle(.green)
                        .padding(.vertical, 4)
                }
                Section("Changes") {
                    ForEach(result.days.filter { $0.action.changesBookings }) { day in
                        DayRow(day: day, isSelected: false, toggle: nil)
                    }
                }
            }
        }
    }

    // MARK: - Failure

    private func failure(_ message: String) -> some View {
        VStack(spacing: 14) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.largeTitle)
                .foregroundStyle(.orange)
            Text(message)
                .multilineTextAlignment(.center)
            if model.result == nil {
                Button("Try Again") {
                    Task { await model.retry() }
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(32)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

private struct DayRow: View {
    let day: ScheduleDayResultDTO
    let isSelected: Bool
    /// nil once applied (rows show the outcome instead of a toggle).
    let toggle: (() -> Void)?

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: day.kind.symbolName)
                .font(.title3)
                .foregroundStyle(.tint)
                .frame(width: 28)

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text(Self.displayDate(day.date))
                        .font(.headline)
                    Text(day.kind.label)
                        .font(.caption.weight(.medium))
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Capsule().fill(Color(.tertiarySystemFill)))
                }
                Text(day.message)
                    .font(.subheadline)
                    .foregroundStyle(day.action == .blocked ? .orange : .secondary)
            }

            Spacer(minLength: 8)

            trailing
        }
        .contentShape(Rectangle())
        .onTapGesture { if day.action.changesBookings { toggle?() } }
        .accessibilityElement(children: .combine)
    }

    @ViewBuilder
    private var trailing: some View {
        if let succeeded = day.succeeded {
            Image(systemName: succeeded ? "checkmark.circle.fill" : "xmark.circle.fill")
                .foregroundStyle(succeeded ? .green : .red)
        } else if day.action.changesBookings, let toggle {
            Toggle("", isOn: Binding(get: { isSelected }, set: { _ in toggle() }))
                .labelsHidden()
        } else if day.action == .keep {
            Image(systemName: "checkmark.circle")
                .foregroundStyle(.green)
        }
    }

    static func displayDate(_ iso: String) -> String {
        let parser = DateFormatter()
        parser.locale = Locale(identifier: "en_US_POSIX")
        parser.dateFormat = "yyyy-MM-dd"
        guard let date = parser.date(from: iso) else { return iso }
        let formatter = DateFormatter()
        formatter.dateFormat = "EEE, MMM d"
        return formatter.string(from: date)
    }
}
