//
//  RidesView.swift
//  AIShuttle
//

import SwiftUI

public struct RidesView: View {
    @Bindable var viewModel: RidesViewModel

    public init(viewModel: RidesViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            Group {
                switch viewModel.state {
                case .idle, .loading:
                    VStack(spacing: 12) {
                        ProgressView()
                            .controlSize(.regular)
                        Text("Loading your rides…")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                case .error(let message):
                    VStack(spacing: 14) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.largeTitle)
                            .foregroundStyle(.orange)

                        Text("Unable to load your rides.")
                            .font(.headline)
                            .fontWeight(.semibold)

                        Text(message)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 24)

                        Button {
                            Task {
                                await viewModel.loadBookings()
                            }
                        } label: {
                            Label("Retry", systemImage: "arrow.clockwise")
                                .fontWeight(.semibold)
                        }
                        .buttonStyle(.borderedProminent)
                        .padding(.top, 4)
                    }
                    .padding()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                case .loaded:
                    if viewModel.bookings.isEmpty {
                        VStack(spacing: 14) {
                            ZStack {
                                Circle()
                                    .fill(Color(.tertiarySystemFill))
                                    .frame(width: 64, height: 64)

                                Image(systemName: "bus")
                                    .font(.system(size: 28))
                                    .foregroundStyle(.secondary)
                            }

                            Text("No upcoming rides")
                                .font(.headline)
                                .fontWeight(.semibold)
                                .foregroundStyle(.primary)

                            Text("Your scheduled rides will appear here once booked.")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.center)
                                .padding(.horizontal, 32)
                        }
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 16) {
                                ForEach(viewModel.bookings) { booking in
                                    NavigationLink(destination: RideDetailsView(booking: booking)) {
                                        UpcomingRideCard(booking: booking)
                                    }
                                    .buttonStyle(PlainButtonStyle())
                                }
                            }
                            .padding(.horizontal, 20)
                            .padding(.vertical, 16)
                        }
                    }
                }
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Rides")
            .refreshable {
                await viewModel.loadBookings()
            }
            .task {
                await viewModel.loadBookings()
            }
        }
    }
}
