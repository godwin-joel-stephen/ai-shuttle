//
//  HomeView.swift
//  AIShuttle
//

import SwiftUI
import WidgetKit

public struct HomeView: View {
    @Bindable var viewModel: RidesViewModel
    @State private var showingAssistant = false
    @State private var showingTracking = false

    public init(viewModel: RidesViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Header
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Good morning")
                            .font(.subheadline)
                            .fontWeight(.medium)
                            .foregroundStyle(.secondary)

                        Text("Clear Path")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundStyle(.primary)
                    }
                    .padding(.top, 8)

                    askClearPathButton

                    trackShuttleButton

                    // Upcoming Ride Section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Upcoming Ride")
                            .font(.headline)
                            .foregroundStyle(.primary)

                        switch viewModel.state {
                        case .idle, .loading:
                            HStack {
                                Spacer()
                                VStack(spacing: 12) {
                                    ProgressView()
                                        .controlSize(.regular)
                                    Text("Checking for rides…")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                .padding(.vertical, 36)
                                Spacer()
                            }
                            .frame(maxWidth: .infinity)
                            .background(
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .fill(Color(.secondarySystemGroupedBackground))
                            )

                        case .error(let message):
                            VStack(spacing: 12) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.title2)
                                    .foregroundStyle(.orange)

                                Text("Unable to load your rides.")
                                    .font(.subheadline)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(.primary)

                                Text(message)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 16)

                                Button {
                                    Task {
                                        await viewModel.loadBookings()
                                    }
                                } label: {
                                    Label("Retry", systemImage: "arrow.clockwise")
                                        .font(.subheadline)
                                        .fontWeight(.semibold)
                                }
                                .buttonStyle(.borderedProminent)
                                .padding(.top, 4)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 24)
                            .background(
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .fill(Color(.secondarySystemGroupedBackground))
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .stroke(Color.primary.opacity(0.06), lineWidth: 1)
                            )

                        case .loaded:
                            if let upcoming = viewModel.upcomingBooking {
                                NavigationLink(destination: RideDetailsView(booking: upcoming)) {
                                    UpcomingRideCard(booking: upcoming)
                                }
                                .buttonStyle(PlainButtonStyle())
                            } else {
                                // Deliberate Empty State
                                VStack(spacing: 14) {
                                    ZStack {
                                        Circle()
                                            .fill(Color(.tertiarySystemFill))
                                            .frame(width: 56, height: 56)

                                        Image(systemName: "bus")
                                            .font(.system(size: 24))
                                            .foregroundStyle(.secondary)
                                    }

                                    VStack(spacing: 4) {
                                        Text("No upcoming rides")
                                            .font(.headline)
                                            .fontWeight(.semibold)
                                            .foregroundStyle(.primary)

                                        Text("Your next shuttle will appear here.")
                                            .font(.subheadline)
                                            .foregroundStyle(.secondary)
                                            .multilineTextAlignment(.center)
                                    }

                                    Button {
                                        // Future booking flow action
                                    } label: {
                                        Text("Book Shuttle")
                                            .font(.subheadline)
                                            .fontWeight(.semibold)
                                            .padding(.horizontal, 16)
                                            .padding(.vertical, 8)
                                    }
                                    .buttonStyle(.bordered)
                                    .tint(.accentColor)
                                    .padding(.top, 4)
                                    .disabled(true)
                                }
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 36)
                                .padding(.horizontal, 20)
                                .background(
                                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                                        .fill(Color(.secondarySystemGroupedBackground))
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                                        .stroke(Color.primary.opacity(0.06), lineWidth: 1)
                                )
                            }
                        }
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 24)
            }
            .background(Color(.systemGroupedBackground))
            .refreshable {
                await viewModel.loadBookings()
            }
            .task {
                await viewModel.loadBookings()
            }
            .sheet(isPresented: $showingTracking) {
                TrackingView()
            }
            .sheet(isPresented: $showingAssistant) {
                AssistantView(
                    viewModel: AssistantViewModel(onBookingsChanged: { [viewModel] in
                        await viewModel.loadBookings()
                        WidgetCenter.shared.reloadAllTimelines()
                    })
                )
            }
        }
    }

    private var trackShuttleButton: some View {
        Button {
            showingTracking = true
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "location.fill")
                    .font(.title3)
                    .foregroundStyle(.tint)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Where's my shuttle?")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text("Live map and Lock Screen tracking")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundStyle(.tertiary)
            }
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(Color(.secondarySystemGroupedBackground))
            )
        }
        .buttonStyle(.plain)
    }

    private var askClearPathButton: some View {
        Button {
            showingAssistant = true
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "sparkles")
                    .font(.title3)
                    .foregroundStyle(.tint)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Ask Clear Path")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text("Book, change or check rides in your own words")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Image(systemName: "mic.fill")
                    .foregroundStyle(.secondary)
            }
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(Color(.secondarySystemGroupedBackground))
            )
        }
        .buttonStyle(.plain)
    }
}
