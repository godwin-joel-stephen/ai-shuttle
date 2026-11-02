//
//  BookingSnippet.swift
//  AIShuttle
//
//  Interactive Siri card shown after booking. Its buttons run
//  RescheduleBookingIntent in place, so the user can adjust the ride
//  without opening the app.
//

import AppIntents
import SwiftUI
import WidgetKit

struct BookingSnippetIntent: SnippetIntent {
    static var title: LocalizedStringResource = "Shuttle Booking"
    static var isDiscoverable = false

    @Parameter(title: "Booking ID")
    var bookingId: Int

    init() {}

    init(bookingId: Int) {
        self.bookingId = bookingId
    }

    func perform() async throws -> some IntentResult & ShowsSnippetView {
        // Re-run after every button tap, so always show the latest state.
        let booking: BookingDetailDTO
        do {
            booking = try await BookingAPIClient.withTimeouts().fetchBooking(id: bookingId)
        } catch {
            throw BookingIntentError(error)
        }
        return .result(view: BookingSnippetView(booking: booking))
    }
}

enum RescheduleDirection: String, AppEnum {
    case earlier
    case later

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Direction"

    static let caseDisplayRepresentations: [RescheduleDirection: DisplayRepresentation] = [
        .earlier: "Earlier",
        .later: "Later"
    ]
}

struct RescheduleBookingIntent: AppIntent {
    static var title: LocalizedStringResource = "Move Shuttle Booking"
    static var isDiscoverable = false

    @Parameter(title: "Booking ID")
    var bookingId: Int

    @Parameter(title: "Direction")
    var direction: RescheduleDirection

    init() {}

    init(bookingId: Int, direction: RescheduleDirection) {
        self.bookingId = bookingId
        self.direction = direction
    }

    func perform() async throws -> some IntentResult {
        do {
            _ = try await BookingAPIClient.withTimeouts().rescheduleBooking(
                id: bookingId,
                direction: RescheduleDirectionDTO(rawValue: direction.rawValue)!
            )
        } catch {
            throw BookingIntentError(error)
        }
        BookingSnippetIntent.reload()
        WidgetCenter.shared.reloadAllTimelines()
        return .result()
    }
}

struct BookingSnippetView: View {
    let booking: BookingDetailDTO

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Label(booking.formattedDate, systemImage: "checkmark.circle.fill")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.green)

                Spacer()

                Text(booking.shuttleName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            HStack(alignment: .firstTextBaseline) {
                Text(booking.formattedPickupTime)
                    .font(.system(.largeTitle, design: .rounded))
                    .fontWeight(.bold)
                    .contentTransition(.numericText())

                if let arrival = booking.formattedArrivalTime {
                    Image(systemName: "arrow.right")
                        .foregroundStyle(.secondary)
                    Text(arrival)
                        .font(.title3)
                        .fontWeight(.semibold)
                        .foregroundStyle(.secondary)
                }
            }

            Label(booking.tripTitle, systemImage: "bus.fill")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack(spacing: 12) {
                Button(intent: RescheduleBookingIntent(bookingId: booking.id, direction: .earlier)) {
                    Label("Earlier", systemImage: "backward.fill")
                        .frame(maxWidth: .infinity)
                }
                .disabled(booking.earlierAvailable == false)

                Button(intent: RescheduleBookingIntent(bookingId: booking.id, direction: .later)) {
                    Label("Later", systemImage: "forward.fill")
                        .frame(maxWidth: .infinity)
                }
                .disabled(booking.laterAvailable == false)
            }
            .buttonStyle(.bordered)
            .controlSize(.large)
        }
        .padding()
    }
}
