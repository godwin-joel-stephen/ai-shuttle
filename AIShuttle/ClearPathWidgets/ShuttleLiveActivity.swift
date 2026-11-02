//
//  ShuttleLiveActivity.swift
//  ClearPathWidgets
//
//  Lock Screen and Dynamic Island presentation of a tracked trip. The
//  countdown and progress bar run off absolute dates, so they keep moving
//  without the app sending updates.
//

import ActivityKit
import SwiftUI
import WidgetKit

struct ShuttleLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: ShuttleActivityAttributes.self) { context in
            LockScreenTripView(attributes: context.attributes, state: context.state)
                .padding(16)
                .activityBackgroundTint(Color.black.opacity(0.75))
                .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Label(context.attributes.pickupName, systemImage: "bus.fill")
                        .font(.caption)
                        .foregroundStyle(.tint)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Countdown(state: context.state)
                        .font(.title3.monospacedDigit())
                        .frame(maxWidth: 80, alignment: .trailing)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(context.state.message)
                            .font(.caption)
                            .lineLimit(2)
                        TripProgressBar(state: context.state)
                    }
                }
            } compactLeading: {
                Image(systemName: "bus.fill")
                    .foregroundStyle(.tint)
            } compactTrailing: {
                Countdown(state: context.state)
                    .font(.caption.monospacedDigit())
                    .frame(maxWidth: 48)
            } minimal: {
                Image(systemName: "bus.fill")
                    .foregroundStyle(.tint)
            }
        }
    }
}

private struct LockScreenTripView: View {
    let attributes: ShuttleActivityAttributes
    let state: ShuttleActivityAttributes.ContentState

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Label("\(attributes.pickupName) → \(attributes.destinationName)", systemImage: "bus.fill")
                    .font(.subheadline.weight(.semibold))
                Spacer()
                if state.delayMinutes > 0 {
                    Text("\(state.delayMinutes) min late")
                        .font(.caption.weight(.semibold))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(.orange.opacity(0.25), in: Capsule())
                        .foregroundStyle(.orange)
                }
            }

            HStack(alignment: .firstTextBaseline) {
                Countdown(state: state)
                    .font(.system(.largeTitle, design: .rounded).weight(.bold).monospacedDigit())
                Text(state.countdownCaption)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Spacer()
            }

            Text(state.message)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .lineLimit(2)

            TripProgressBar(state: state)
        }
        .foregroundStyle(.white)
    }
}

/// Counts down to pickup, then arrival, entirely on-device.
private struct Countdown: View {
    let state: ShuttleActivityAttributes.ContentState

    var body: some View {
        switch state.phase {
        case "boarding":
            Text("Now")
        case "arrived":
            Text("Done")
        default:
            // A closed range must not end before it starts.
            let end = max(state.countdownTarget, .now)
            Text(timerInterval: Date.now...end, countsDown: true)
                .multilineTextAlignment(.trailing)
        }
    }
}

private struct TripProgressBar: View {
    let state: ShuttleActivityAttributes.ContentState

    var body: some View {
        let end = max(state.arrivalETA, state.windowStart.addingTimeInterval(1))
        ProgressView(timerInterval: state.windowStart...end, countsDown: false) {
            EmptyView()
        } currentValueLabel: {
            EmptyView()
        }
        .tint(state.delayMinutes > 0 ? .orange : .green)
    }
}
