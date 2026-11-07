//
//  HomeView.swift
//  AIShuttle
//

import PhotosUI
import SwiftUI
import UniformTypeIdentifiers
import WidgetKit

public struct HomeView: View {
    @Bindable var viewModel: RidesViewModel
    @State private var showingAssistant = false
    @State private var showingTracking = false
    @State private var showingPhotoPicker = false
    @State private var showingFilePicker = false
    @State private var pickedPhoto: PhotosPickerItem?
    @State private var scheduleImport: ScheduleImportRequest?

    public init(viewModel: RidesViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Header
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Good morning")
                            .font(.subheadline)
                            .fontWeight(.medium)
                            .foregroundStyle(.secondary)

                        Text("Clear Path")
                            .font(.largeTitle)
                            .fontWeight(.bold)
                            .foregroundStyle(.primary)
                    }
                    .padding(.top, 8)

                    askClearPathButton

                    trackShuttleButton

                    importScheduleButton

                    // Upcoming Ride Section
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Upcoming Ride")
                            .font(.headline)
                            .foregroundStyle(.primary)

                        switch viewModel.state {
                        case .idle, .loading:
                            HStack {
                                Spacer()
                                VStack(spacing: 12) {
                                    ProgressView()
                                        .controlSize(.regular)
                                    Text("Checking for rides…")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                .padding(.vertical, 36)
                                Spacer()
                            }
                            .frame(maxWidth: .infinity)
                            .background(
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .fill(Color(.secondarySystemGroupedBackground))
                            )

                        case .error(let message):
                            VStack(spacing: 12) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .font(.title2)
                                    .foregroundStyle(.orange)

                                Text("Unable to load your rides.")
                                    .font(.subheadline)
                                    .fontWeight(.semibold)
                                    .foregroundStyle(.primary)

                                Text(message)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .multilineTextAlignment(.center)
                                    .padding(.horizontal, 16)

                                Button {
                                    Task {
                                        await viewModel.loadBookings()
                                    }
                                } label: {
                                    Label("Retry", systemImage: "arrow.clockwise")
                                        .font(.subheadline)
                                        .fontWeight(.semibold)
                                }
                                .buttonStyle(.borderedProminent)
                                .padding(.top, 4)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 24)
                            .background(
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .fill(Color(.secondarySystemGroupedBackground))
                            )
                            .overlay(
                                RoundedRectangle(cornerRadius: 18, style: .continuous)
                                    .stroke(Color.primary.opacity(0.06), lineWidth: 1)
                            )

                        case .loaded:
                            if let upcoming = viewModel.upcomingBooking {
                                NavigationLink(destination: RideDetailsView(booking: upcoming)) {
                                    UpcomingRideCard(booking: upcoming)
                                }
                                .buttonStyle(PlainButtonStyle())
                            } else {
                                // Deliberate Empty State
                                VStack(spacing: 14) {
                                    ZStack {
                                        Circle()
                                            .fill(Color(.tertiarySystemFill))
                                            .frame(width: 56, height: 56)

                                        Image(systemName: "bus")
                                            .font(.system(size: 24))
                                            .foregroundStyle(.secondary)
                                    }

                                    VStack(spacing: 4) {
                                        Text("No upcoming rides")
                                            .font(.headline)
                                            .fontWeight(.semibold)
                                            .foregroundStyle(.primary)

                                        Text("Your next shuttle will appear here.")
                                            .font(.subheadline)
                                            .foregroundStyle(.secondary)
                                            .multilineTextAlignment(.center)
                                    }

                                    Button {
                                        // Future booking flow action
                                    } label: {
                                        Text("Book Shuttle")
                                            .font(.subheadline)
                                            .fontWeight(.semibold)
                                            .padding(.horizontal, 16)
                                            .padding(.vertical, 8)
                                    }
                                    .buttonStyle(.bordered)
                                    .tint(.accentColor)
                                    .padding(.top, 4)
                                    .disabled(true)
                                }
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 36)
                                .padding(.horizontal, 20)
                                .background(
                                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                                        .fill(Color(.secondarySystemGroupedBackground))
                                )
                                .overlay(
                                    RoundedRectangle(cornerRadius: 18, style: .continuous)
                                        .stroke(Color.primary.opacity(0.06), lineWidth: 1)
                                )
                            }
                        }
                    }

                    if let habits = viewModel.habits {
                        HabitCard(
                            habits: habits,
                            onBook: { [viewModel] day in await viewModel.bookUsual(on: day) },
                            onPin: { [viewModel] shuttleId in await viewModel.pinUsual(shuttleId: shuttleId) }
                        )
                    }
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 24)
            }
            .background(Color(.systemGroupedBackground))
            .refreshable {
                await viewModel.loadBookings()
            }
            .task {
                await viewModel.loadBookings()
            }
            .photosPicker(isPresented: $showingPhotoPicker, selection: $pickedPhoto, matching: .images)
            .onChange(of: pickedPhoto) { _, item in
                guard let item else { return }
                pickedPhoto = nil
                scheduleImport = ScheduleImportRequest {
                    guard let data = try await item.loadTransferable(type: Data.self) else {
                        throw ScheduleImportError.unreadableDocument
                    }
                    return .image(data)
                }
            }
            .fileImporter(
                isPresented: $showingFilePicker,
                allowedContentTypes: [.pdf, .image, .plainText]
            ) { result in
                guard case .success(let url) = result else { return }
                scheduleImport = ScheduleImportRequest { try Self.scheduleSource(from: url) }
            }
            .sheet(item: $scheduleImport) { request in
                ScheduleImportView(
                    model: ScheduleImportModel(
                        loadSource: request.loadSource,
                        onApplied: { [viewModel] in await viewModel.loadBookings() }
                    ),
                    onClose: { scheduleImport = nil }
                )
            }
            .sheet(isPresented: $showingTracking) {
                TrackingView()
            }
            .sheet(isPresented: $showingAssistant) {
                AssistantView(
                    viewModel: AssistantViewModel(onDevice: .live(), onBookingsChanged: { [viewModel] in
                        await viewModel.loadBookings()
                        WidgetCenter.shared.reloadAllTimelines()
                    })
                )
            }
        }
    }

    private var importScheduleButton: some View {
        Menu {
            Button("Choose Photo", systemImage: "photo") { showingPhotoPicker = true }
            Button("Choose File", systemImage: "doc") { showingFilePicker = true }
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "calendar.badge.plus")
                    .font(.title3)
                    .foregroundStyle(.tint)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Import work schedule")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text("Or share a photo or PDF to Clear Path")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundStyle(.tertiary)
            }
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(Color(.secondarySystemGroupedBackground))
            )
        }
        .buttonStyle(.plain)
    }

    private static func scheduleSource(from url: URL) throws -> ScheduleSource {
        let accessing = url.startAccessingSecurityScopedResource()
        defer { if accessing { url.stopAccessingSecurityScopedResource() } }

        let data = try Data(contentsOf: url)
        let type = UTType(filenameExtension: url.pathExtension)
        if type?.conforms(to: .pdf) == true {
            return .pdf(data)
        }
        if type?.conforms(to: .image) == true {
            return .image(data)
        }
        return .text(String(decoding: data, as: UTF8.self))
    }

    private var trackShuttleButton: some View {
        Button {
            showingTracking = true
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "location.fill")
                    .font(.title3)
                    .foregroundStyle(.tint)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Where's my shuttle?")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text("Live map and Lock Screen tracking")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundStyle(.tertiary)
            }
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(Color(.secondarySystemGroupedBackground))
            )
        }
        .buttonStyle(.plain)
    }

    private var askClearPathButton: some View {
        Button {
            showingAssistant = true
        } label: {
            HStack(spacing: 12) {
                Image(systemName: "sparkles")
                    .font(.title3)
                    .foregroundStyle(.tint)

                VStack(alignment: .leading, spacing: 2) {
                    Text("Ask Clear Path")
                        .font(.headline)
                        .foregroundStyle(.primary)
                    Text("Book, change or check rides in your own words")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Image(systemName: "mic.fill")
                    .foregroundStyle(.secondary)
            }
            .padding(16)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(Color(.secondarySystemGroupedBackground))
            )
        }
        .buttonStyle(.plain)
    }
}

/// One import sheet per picked document.
struct ScheduleImportRequest: Identifiable {
    let id = UUID()
    let loadSource: () async throws -> ScheduleSource
}
