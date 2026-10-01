import SwiftUI
import AppIntents

@main
struct AIShuttleApp: App {
    init() {
        AIShuttleShortcuts.updateAppShortcutParameters()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
