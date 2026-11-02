//
//  NextRideWidget.swift
//  ClearPathWidgets
//
//  Home Screen and Lock Screen widget: the next ride at a glance, with a
//  one-tap "Book tomorrow" button when tomorrow isn't booked yet.
//

import AppIntents
import SwiftUI
import WidgetKit

struct NextRideEntry: TimelineEntry {
    enum Content {
        case ride(BookingDetailDTO)
        case noRide
        case unavailable
    }

    let date: Date
    let content: Content
    let tomorrowBooked: Bool

    static let preview = NextRideEntry(
        date: .now,
        content: .ride(
            BookingDetailDTO(
                id: 0,
                bookingDate: BookingAPIClient.isoDay(Calendar.current.date(byAdding: .day, value: 1, to: .now)!),
                pickupTime: "07:30:00",
                arrivalTime: "08:15:00",
                status: "confirmed",
                shuttleName: "Morning Shuttle C",
                routeName: "Home → Office Morning Route",
                pickupLocation: "Home",
                destination: "Office"
            )
        ),
        tomorrowBooked: true
    )

    static func load() async -> NextRideEntry {
        let tomorrow = BookingAPIClient.isoDay(Calendar.current.date(byAdding: .day, value: 1, to: .now)!)

        do {
            let bookings = try await BookingAPIClient.withTimeouts().fetchUpcomingBookings(userId: 1)
            return NextRideEntry(
                date: .now,
                content: bookings.first.map(Content.ride) ?? .noRide,
                tomorrowBooked: bookings.contains { $0.bookingDate == tomorrow }
            )
        } catch {
            return NextRideEntry(date: .now, content: .unavailable, tomorrowBooked: false)
        }
    }
}

struct NextRideProvider: TimelineProvider {
    func placeholder(in context: Context) -> NextRideEntry {
        .preview
    }

    func getSnapshot(in context: Context, completion: @escaping (NextRideEntry) -> Void) {
        if context.isPreview {
            completion(.preview)
            return
        }
        Task {
            completion(await NextRideEntry.load())
        }
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<NextRideEntry>) -> Void) {
        Task {
            let entry = await NextRideEntry.load()
            // Booking intents reload timelines immediately; this only
            // catches changes made elsewhere (e.g. the backend).
            let refresh = Calendar.current.date(byAdding: .minute, value: 15, to: .now)!
            completion(Timeline(entries: [entry], policy: .after(refresh)))
        }
    }
}

struct NextRideWidget: Widget {
    static let kind = "com.yourcompany.AIShuttle.NextRideWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: Self.kind, provider: NextRideProvider()) { entry in
            NextRideWidgetView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Next Shuttle")
        .description("Your next ride, with one-tap booking for tomorrow.")
        .supportedFamilies([.systemSmall, .systemMedium, .accessoryRectangular, .accessoryInline])
    }
}

struct NextRideWidgetView: View {
    @Environment(\.widgetFamily) private var family
    let entry: NextRideEntry

    var body: some View {
        switch family {
        case .accessoryInline:
            inline
        case .accessoryRectangular:
            rectangular
        case .systemMedium:
            HStack(alignment: .center, spacing: 16) {
                rideSummary
                if !entry.tomorrowBooked {
                    Spacer(minLength: 0)
                    bookButton
                        .frame(maxWidth: 120)
                }
            }
        default:
            VStack(alignment: .leading, spacing: 8) {
                rideSummary
                if !entry.tomorrowBooked {
                    Spacer(minLength: 0)
                    bookButton
                }
            }
        }
    }

    @ViewBuilder
    private var rideSummary: some View {
        switch entry.content {
        case .ride(let booking):
            VStack(alignment: .leading, spacing: 4) {
                Label(booking.formattedDate, systemImage: "bus.fill")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.tint)
                    .lineLimit(1)

                Text(booking.formattedPickupTime)
                    .font(.system(.title, design: .rounded))
                    .fontWeight(.bold)
                    .minimumScaleFactor(0.7)
                    .lineLimit(1)

                if let arrival = booking.formattedArrivalTime {
                    Text("Arrives \(arrival)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Text(booking.tripTitle)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        case .noRide:
            VStack(alignment: .leading, spacing: 4) {
                Label("Clear Path", systemImage: "bus.fill")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.tint)
                Text("No ride booked")
                    .font(.headline)
            }
        case .unavailable:
            VStack(alignment: .leading, spacing: 4) {
                Label("Clear Path", systemImage: "bus.fill")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.tint)
                Text("Can't reach Clear Path")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var bookButton: some View {
        Button(intent: BookTomorrowIntent()) {
            Label("Book tomorrow", systemImage: "plus.circle.fill")
                .font(.caption)
                .fontWeight(.semibold)
                .frame(maxWidth: .infinity)
        }
        .buttonStyle(.borderedProminent)
    }

    @ViewBuilder
    private var rectangular: some View {
        switch entry.content {
        case .ride(let booking):
            VStack(alignment: .leading) {
                Label(booking.formattedPickupTime, systemImage: "bus.fill")
                    .font(.headline)
                Text(booking.formattedDate)
                    .font(.caption)
                Text(booking.tripTitle)
                    .font(.caption)
            }
        case .noRide:
            Label("No ride booked", systemImage: "bus")
        case .unavailable:
            Label("Clear Path offline", systemImage: "bus")
        }
    }

    @ViewBuilder
    private var inline: some View {
        switch entry.content {
        case .ride(let booking):
            Label("\(booking.formattedPickupTime) · \(booking.tripTitle)", systemImage: "bus.fill")
        case .noRide, .unavailable:
            Label("No shuttle booked", systemImage: "bus")
        }
    }
}

#Preview(as: .systemSmall) {
    NextRideWidget()
} timeline: {
    NextRideEntry.preview
    NextRideEntry(date: .now, content: .noRide, tomorrowBooked: false)
}
