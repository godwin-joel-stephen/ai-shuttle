//
//  TrackingView.swift
//  AIShuttle
//

import MapKit
import SwiftUI

/// Live map of the next trip, refreshed every few seconds while open.
struct TrackingView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var trip: TripStatusDTO?
    @State private var errorMessage: String?
    @State private var camera: MapCameraPosition = .automatic
    @State private var monitor = TripMonitor.shared
    @State private var switching = false

    private let apiClient: BookingAPIClient
    private let refreshInterval: Duration

    init(apiClient: BookingAPIClient = .withTimeouts(), refreshInterval: Duration = .seconds(5)) {
        self.apiClient = apiClient
        self.refreshInterval = refreshInterval
    }

    var body: some View {
        NavigationStack {
            ZStack(alignment: .bottom) {
                map
                    .ignoresSafeArea(edges: .bottom)

                statusCard
                    .padding(16)
            }
            .navigationTitle("Where's my shuttle")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .task {
                await poll()
            }
        }
    }

    private var map: some View {
        Map(position: $camera) {
            if let trip {
                MapPolyline(coordinates: trip.route.map(\.location))
                    .stroke(.blue.opacity(0.7), lineWidth: 5)

                Marker(trip.pickupName, systemImage: "figure.wave", coordinate: trip.pickup.location)
                    .tint(.green)

                Marker(trip.destinationName, systemImage: "building.2.fill", coordinate: trip.destination.location)
                    .tint(.purple)

                Annotation(trip.shuttleName, coordinate: trip.position.location) {
                    Image(systemName: "bus.fill")
                        .font(.headline)
                        .foregroundStyle(.white)
                        .padding(8)
                        .background(trip.delayMinutes > 0 ? .orange : .blue, in: Circle())
                        .shadow(radius: 3)
                }
            }
        }
        .animation(.easeInOut(duration: 1), value: trip?.position)
    }

    @ViewBuilder
    private var statusCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            if let trip {
                HStack {
                    Text(trip.shuttleName)
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Spacer()
                    if trip.delayMinutes > 0 {
                        Text("\(trip.delayMinutes) min late")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.orange)
                    }
                    if trip.simulated {
                        Text("Simulated")
                            .font(.caption2)
                            .foregroundStyle(.tertiary)
                    }
                }

                Text(trip.message)
                    .font(.headline)

                ProgressView(value: trip.progress)
                    .tint(trip.delayMinutes > 0 ? .orange : .green)

                if let advice = trip.departureAdvice {
                    Label(advice, systemImage: "figure.walk")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle((trip.leaveInMinutes ?? 1) <= 0 ? .orange : .primary)
                }

                if let alternative = trip.alternative {
                    Button {
                        Task { await switchTo(alternative, from: trip) }
                    } label: {
                        Label(
                            "Switch to the \(alternative.formattedDeparture) (arrives \(alternative.minutesEarlier) min sooner)",
                            systemImage: "arrow.triangle.swap"
                        )
                        .frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.bordered)
                    .tint(.orange)
                    .disabled(switching)
                }

                if trip.isLive || trip.phase == "scheduled" {
                    tripModeButton
                }
            } else if let errorMessage {
                Label(errorMessage, systemImage: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
            } else {
                ProgressView("Finding your shuttle…")
                    .frame(maxWidth: .infinity)
            }
        }
        .padding(16)
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }

    /// Trip mode keeps following the shuttle with the app closed: Lock
    /// Screen updates and alerts for leaving and delays.
    private var tripModeButton: some View {
        Button {
            if monitor.isActive {
                monitor.stop()
            } else {
                monitor.start()
            }
        } label: {
            Label(
                monitor.isActive ? "Trip mode on · tap to stop" : "Start trip mode",
                systemImage: monitor.isActive ? "location.fill" : "location"
            )
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(.borderedProminent)
        .tint(monitor.isActive ? .green : .accentColor)
    }

    private func switchTo(_ alternative: AlternativeDTO, from trip: TripStatusDTO) async {
        switching = true
        defer { switching = false }

        do {
            self.trip = try await monitor.switchToAlternative(
                bookingId: trip.bookingId,
                shuttleId: alternative.shuttleId
            )
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func poll() async {
        while !Task.isCancelled {
            do {
                let latest = try await apiClient.fetchNextTrip()
                trip = latest
                errorMessage = nil
                // Keep the Lock Screen in step while the app is open, e.g.
                // when a delay is announced.
                await ShuttleActivityController.refresh(latest)
            } catch {
                errorMessage = error.localizedDescription
            }
            try? await Task.sleep(for: refreshInterval)
        }
    }
}
