//
//  AppShellView.swift
//  AIShuttle
//

import SwiftUI

public enum AppTab: Hashable, CaseIterable {
    case home
    case rides
    // Future extensible tabs: emma, assistant

    public var title: String {
        switch self {
        case .home: return "Home"
        case .rides: return "Rides"
        }
    }

    public var iconName: String {
        switch self {
        case .home: return "house.fill"
        case .rides: return "bus.fill"
        }
    }
}

@MainActor
public struct AppShellView: View {
    @State private var selectedTab: AppTab = .home
    @State private var viewModel: RidesViewModel

    public init(viewModel: RidesViewModel? = nil) {
        _viewModel = State(initialValue: viewModel ?? RidesViewModel())
    }


    public var body: some View {
        TabView(selection: $selectedTab) {
            HomeView(viewModel: viewModel)
                .tabItem {
                    Label(AppTab.home.title, systemImage: AppTab.home.iconName)
                }
                .tag(AppTab.home)

            RidesView(viewModel: viewModel)
                .tabItem {
                    Label(AppTab.rides.title, systemImage: AppTab.rides.iconName)
                }
                .tag(AppTab.rides)
        }
    }
}
