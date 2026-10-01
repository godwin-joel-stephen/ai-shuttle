//
//  UpcomingRideCard.swift
//  AIShuttle
//

import SwiftUI

public struct UpcomingRideCard: View {
    public let booking: BookingDetailDTO

    public init(booking: BookingDetailDTO) {
        self.booking = booking
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Header: Date & Status Badge
            HStack {
                Text(booking.formattedDate)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.secondary)

                Spacer()

                HStack(spacing: 4) {
                    Image(systemName: "checkmark")
                        .font(.system(size: 11, weight: .bold))
                    Text(booking.status.capitalized)
                        .font(.caption)
                        .fontWeight(.semibold)
                }
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(Color.green.opacity(0.15))
                .foregroundStyle(Color.green)
                .clipShape(Capsule())
            }

            // Main child & shuttle info
            HStack(alignment: .center) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(booking.childName)
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundStyle(.primary)

                    Text(booking.shuttleName)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                // Pickup Time
                VStack(alignment: .trailing, spacing: 2) {
                    Text(booking.formattedPickupTime)
                        .font(.title3)
                        .fontWeight(.bold)
                        .foregroundStyle(.primary)

                    Text("Pickup")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }

            Divider()

            // Route / Location hint
            HStack(spacing: 8) {
                Image(systemName: "mappin.and.ellipse")
                    .font(.caption)
                    .foregroundStyle(.tint)
                Text(booking.routeName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)

                Spacer()

                Image(systemName: "chevron.right")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
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
        .shadow(color: Color.black.opacity(0.04), radius: 8, x: 0, y: 4)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(booking.childName), \(booking.shuttleName), pickup at \(booking.formattedPickupTime) on \(booking.formattedDate), status \(booking.status)")
    }
}
