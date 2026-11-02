//
//  AIShuttleShortcuts.swift
//  AIShuttle
//

import AppIntents

public struct AIShuttleShortcuts: AppShortcutsProvider {
    public static var appShortcuts: [AppShortcut] {
        // Siri only runs an intent directly when the spoken words match one
        // of these phrases (plus the app name or an INAlternativeAppNames
        // synonym). Anything else is left to Siri's own model, which may
        // answer that the app "doesn't support that". Cover the natural
        // variations people actually say, and avoid "ride", which Siri
        // associates with its built-in ride-booking domain.
        AppShortcut(
            intent: BookMyUsualShuttleIntent(),
            phrases: [
                "Book my usual shuttle with \(.applicationName)",
                "Book my usual shuttle for \(\.$day) with \(.applicationName)",
                "Book my usual shuttle \(\.$day) with \(.applicationName)",
                "Book my usual shuttle in \(.applicationName)",
                "Book my shuttle with \(.applicationName)",
                "Book my shuttle for \(\.$day) with \(.applicationName)",
                "\(.applicationName) book my usual shuttle",
                "\(.applicationName) book my shuttle for \(\.$day)",
                "Use \(.applicationName) to book my usual shuttle"
            ],
            shortTitle: "Book My Usual Shuttle",
            systemImageName: "bus"
        )

        AppShortcut(
            intent: AskClearPathIntent(),
            phrases: [
                "Ask \(.applicationName)",
                "Talk to \(.applicationName)",
                "Open \(.applicationName) assistant",
                "I need help from \(.applicationName)"
            ],
            shortTitle: "Ask Clear Path",
            systemImageName: "sparkles"
        )
    }
}
