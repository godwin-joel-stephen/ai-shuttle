//
//  AIShuttleShortcuts.swift
//  AIShuttle
//

import AppIntents

public struct AIShuttleShortcuts: AppShortcutsProvider {
    public static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: BookMyUsualShuttleIntent(),
            phrases: [
                "Book my usual shuttle with \(.applicationName)"
            ],
            shortTitle: "Book My Usual Shuttle",
            systemImageName: "bus"
        )
    }
}
