//
//  BookShuttleControl.swift
//  ClearPathWidgets
//
//  Control Center / Lock Screen / Action button control. One press books
//  tomorrow's usual shuttle; the result arrives as a notification.
//

import AppIntents
import SwiftUI
import WidgetKit

struct BookShuttleControl: ControlWidget {
    static let kind = "com.yourcompany.AIShuttle.BookShuttleControl"

    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(kind: Self.kind) {
            ControlWidgetButton(action: BookTomorrowIntent()) {
                Label("Book Shuttle", systemImage: "bus.fill")
            }
        }
        .displayName("Book Usual Shuttle")
        .description("Books your usual Clear Path shuttle for tomorrow.")
    }
}
