//
//  RideDetailsView.swift
//  AIShuttle
//

import SwiftUI

public struct RideDetailsView: View {
    public let booking: BookingDetailDTO

    public init(booking: BookingDetailDTO) {
        self.booking = booking
    }

    public var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Top Hero Card
                VStack(spacing: 12) {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(booking.childName)
                                .font(.title)
                                .fontWeight(.bold)
                                .foregroundStyle(.primary)

                            Text(booking.shuttleName)
                                .font(.headline)
                                .foregroundStyle(.secondary)
                        }

                        Spacer()

                        VStack(alignment: .trailing, spacing: 6) {
                            HStack(spacing: 4) {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 11, weight: .bold))
                                Text(booking.status.capitalized)
                                    .font(.caption)
                                    .fontWeight(.semibold)
                            }
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(Color.green.opacity(0.15))
                            .foregroundStyle(Color.green)
                            .clipShape(Capsule())

                            Text("ID #\(booking.id)")
                                .font(.caption2)
                                .foregroundStyle(.tertiary)
                        }
                    }

                    Divider()
                        .padding(.vertical, 4)

                    HStack {
                        Label(booking.formattedDate, systemImage: "calendar")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)

                        Spacer()

                        Label(booking.formattedPickupTime, systemImage: "clock")
                            .font(.subheadline)
                            .fontWeight(.semibold)
                            .foregroundStyle(.primary)
                    }
                }
                .padding(20)
                .background(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .fill(Color(.secondarySystemGroupedBackground))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color.primary.opacity(0.06), lineWidth: 1)
                )

                // Route & Locations Card
                VStack(alignment: .leading, spacing: 16) {
                    Text("Route Details")
                        .font(.headline)
                        .foregroundStyle(.primary)

                    VStack(alignment: .leading, spacing: 16) {
                        // Route name
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: "point.topleft.down.to.point.bottomright.curvepath")
                                .font(.system(size: 16))
                                .foregroundStyle(.tint)
                                .frame(width: 24)

                            VStack(alignment: .leading, spacing: 2) {
                                Text("Route")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Text(booking.routeName)
                                    .font(.subheadline)
                                    .fontWeight(.medium)
                            }
                        }

                        // Pickup location
                        if let pickup = booking.pickupLocation, !pickup.isEmpty {
                            HStack(alignment: .top, spacing: 12) {
                                Image(systemName: "figure.walk")
                                    .font(.system(size: 16))
                                    .foregroundStyle(.tint)
                                    .frame(width: 24)

                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Pickup Location")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                    Text(pickup)
                                        .font(.subheadline)
                                        .fontWeight(.medium)
                                }
                            }
                        }

                        // Destination
                        if let destination = booking.destination, !destination.isEmpty {
                            HStack(alignment: .top, spacing: 12) {
                                Image(systemName: "building.2")
                                    .font(.system(size: 16))
                                    .foregroundStyle(.tint)
                                    .frame(width: 24)

                                VStack(alignment: .leading, spacing: 2) {
                                    Text("Destination")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                    Text(destination)
                                        .font(.subheadline)
                                        .fontWeight(.medium)
                                }
                            }
                        }
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .fill(Color(.secondarySystemGroupedBackground))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color.primary.opacity(0.06), lineWidth: 1)
                )

                // Passenger Card
                VStack(alignment: .leading, spacing: 12) {
                    Text("Passenger")
                        .font(.headline)
                        .foregroundStyle(.primary)

                    HStack(spacing: 12) {
                        Circle()
                            .fill(Color.accentColor.opacity(0.15))
                            .frame(width: 44, height: 44)
                            .overlay(
                                Text(String(booking.childName.prefix(1)))
                                    .font(.headline)
                                    .foregroundStyle(.tint)
                            )

                        VStack(alignment: .leading, spacing: 2) {
                            Text(booking.childName)
                                .font(.subheadline)
                                .fontWeight(.semibold)
                            Text("Scheduled Rider")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        Spacer()
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .fill(Color(.secondarySystemGroupedBackground))
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                        .stroke(Color.primary.opacity(0.06), lineWidth: 1)
                )
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("Ride Details")
        .navigationBarTitleDisplayMode(.inline)
    }
}
