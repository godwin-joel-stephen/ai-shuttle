//
//  ClearPathWidgetsBundle.swift
//  ClearPathWidgets
//

import SwiftUI
import WidgetKit

@main
struct ClearPathWidgetsBundle: WidgetBundle {
    var body: some Widget {
        NextRideWidget()
        BookShuttleControl()
        ShuttleLiveActivity()
    }
}
