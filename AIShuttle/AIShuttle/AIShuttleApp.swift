import SwiftUI
import AppIntents
import UserNotifications

@main
struct AIShuttleApp: App {
    init() {
        AIShuttleShortcuts.updateAppShortcutParameters()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .task {
                    // Widget and Control Center bookings confirm by notification.
                    _ = try? await UNUserNotificationCenter.current()
                        .requestAuthorization(options: [.alert, .sound])
                }
        }
    }
}
