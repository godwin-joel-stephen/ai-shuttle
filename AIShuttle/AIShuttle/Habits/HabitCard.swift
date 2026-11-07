//
//  HabitCard.swift
//  AIShuttle
//
//  Home screen card for the learned commute habit (F10): the next day the
//  rider usually rides but hasn't booked, why that shuttle is "usual", and
//  the habit for each weekday. Booking is always the rider's choice.
//

import SwiftUI

struct HabitCard: View {
    let habits: HabitsDTO
    let onBook: (UpcomingHabitDayDTO) async -> String
    let onPin: (Int?) async -> Void

    @State private var isBooking = false
    @State private var result: String?
    @State private var showingWeek = false

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            header

            if let next = habits.nextUnbooked {
                suggestion(next)
            } else {
                Label("Your usual days this week are booked.", systemImage: "checkmark.circle.fill")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            if let result {
                Text(result)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .transition(.opacity)
            }

            DisclosureGroup("Your usual week", isExpanded: $showingWeek) {
                VStack(spacing: 10) {
                    ForEach(habits.days, id: \.weekday) { day in
                        weekRow(day)
                    }
                }
                .padding(.top, 8)
            }
            .font(.subheadline)
            .tint(.primary)
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(Color(.secondarySystemGroupedBackground))
        )
        .animation(.default, value: result)
    }

    private var header: some View {
        HStack {
            Label("Your commute", systemImage: "sparkles")
                .font(.headline)

            Spacer()

            Menu {
                if habits.pinnedShuttleId != nil {
                    Button("Learn from my rides again", systemImage: "pin.slash") {
                        Task { await onPin(nil) }
                    }
                } else if let next = habits.nextUnbooked {
                    Button("Always use the \(next.habit.formattedDeparture)", systemImage: "pin") {
                        Task { await onPin(next.habit.shuttleId) }
                    }
                }
                #if DEBUG
                if let next = habits.nextUnbooked {
                    Button("Preview reminder", systemImage: "bell.badge") {
                        Task { await HabitReminders.preview(next) }
                    }
                }
                #endif
            } label: {
                Image(systemName: "ellipsis.circle")
                    .font(.title3)
                    .foregroundStyle(.secondary)
            }
            .accessibilityLabel("Habit options")
        }
    }

    private func suggestion(_ day: UpcomingHabitDayDTO) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(day.weekday) isn't booked yet")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Text("\(day.habit.formattedDeparture) → arrives \(day.habit.formattedArrival)")
                    .font(.title3)
                    .fontWeight(.semibold)

                Text(sentence(day.habit.reason))
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }

            Button {
                Task {
                    isBooking = true
                    result = await onBook(day)
                    isBooking = false
                }
            } label: {
                HStack {
                    if isBooking {
                        ProgressView().controlSize(.small)
                    }
                    Text("Book \(day.weekday) \(day.habit.formattedDeparture)")
                        .fontWeight(.semibold)
                }
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(isBooking)
        }
    }

    private func weekRow(_ day: HabitDayDTO) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 10) {
            Image(systemName: icon(for: day.source))
                .foregroundStyle(day.isLearned || day.source == .pinned ? Color.accentColor : .secondary)
                .frame(width: 18)

            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(day.weekday)
                    Spacer()
                    Text(day.formattedDeparture)
                        .fontWeight(.semibold)
                        .monospacedDigit()
                }
                Text(day.regular ? sentence(day.reason) : "You rarely ride this day")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .opacity(day.regular ? 1 : 0.6)
        .accessibilityElement(children: .combine)
    }

    private func icon(for source: HabitSourceDTO) -> String {
        switch source {
        case .pinned: "pin.fill"
        case .weekday, .overall: "sparkles"
        case .default: "circle"
        }
    }

    /// "you took it on 4 of …" → "You took it on 4 of …"
    private func sentence(_ clause: String) -> String {
        clause.prefix(1).uppercased() + clause.dropFirst()
    }
}
