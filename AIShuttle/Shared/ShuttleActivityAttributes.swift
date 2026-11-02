//
//  ShuttleActivityAttributes.swift
//  AIShuttle
//
//  Live Activity data shared by the app (starts and updates it) and the
//  widget extension (draws it on the Lock Screen and Dynamic Island).
//

import ActivityKit
import Foundation

nonisolated struct ShuttleActivityAttributes: ActivityAttributes {
    nonisolated struct ContentState: Codable, Hashable {
        /// scheduled, approaching, boarding, in_transit or arrived.
        var phase: String
        var message: String
        var pickupETA: Date
        var arrivalETA: Date
        var delayMinutes: Int
        /// When the tracked part of the trip began (shuttle leaving the
        /// depot). With arrivalETA it drives a progress bar that advances
        /// on its own, so the Lock Screen stays live without updates.
        var windowStart: Date

        /// What the countdown counts to: pickup, then arrival.
        var countdownTarget: Date {
            phase == "scheduled" || phase == "approaching" ? pickupETA : arrivalETA
        }

        var countdownCaption: String {
            switch phase {
            case "scheduled", "approaching": return "to pickup"
            case "boarding": return "boarding"
            case "arrived": return "arrived"
            default: return "to arrival"
            }
        }
    }

    var bookingId: Int
    var shuttleName: String
    var pickupName: String
    var destinationName: String
}
