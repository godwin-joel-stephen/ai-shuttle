//
//  AssistantView.swift
//  AIShuttle
//
//  "Ask Clear Path": a secondary way in for requests that don't fit a
//  fixed Siri phrase or button. Shows which tools the agent used.
//

import SwiftUI

struct AssistantView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var viewModel: AssistantViewModel
    @State private var voice = VoiceInput()
    @FocusState private var inputFocused: Bool

    init(viewModel: AssistantViewModel) {
        _viewModel = State(initialValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 14) {
                        if viewModel.messages.isEmpty {
                            emptyState
                        }

                        ForEach(viewModel.messages) { message in
                            MessageRow(message: message)
                                .id(message.id)
                        }

                        if viewModel.isSending {
                            HStack(spacing: 8) {
                                ProgressView()
                                Text("Working on it…")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                            .id("progress")
                        }

                        if let error = viewModel.errorMessage {
                            Label(error, systemImage: "exclamationmark.triangle.fill")
                                .font(.footnote)
                                .foregroundStyle(.orange)
                        }
                    }
                    .padding(16)
                }
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: viewModel.messages.count) {
                    withAnimation {
                        proxy.scrollTo(viewModel.messages.last?.id, anchor: .bottom)
                    }
                }
                .onChange(of: viewModel.isSending) {
                    if viewModel.isSending {
                        withAnimation { proxy.scrollTo("progress", anchor: .bottom) }
                    }
                }
            }
            .safeAreaInset(edge: .bottom) {
                inputBar
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("Ask Clear Path")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        viewModel.startNewConversation()
                    } label: {
                        Label("New conversation", systemImage: "square.and.pencil")
                    }
                    .disabled(viewModel.messages.isEmpty || viewModel.isSending)
                }
            }
            .task {
                await viewModel.loadConversation()
            }
            .onDisappear {
                if voice.isListening {
                    Task { await voice.stop() }
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: 14) {
            Image(systemName: "sparkles")
                .font(.title)
                .foregroundStyle(.tint)

            Text("Book, change or check your rides in your own words.")
                .font(.headline)

            ForEach(AssistantViewModel.suggestions, id: \.self) { suggestion in
                Button {
                    Task { await viewModel.send(suggestion) }
                } label: {
                    Text(suggestion)
                        .font(.subheadline)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 10)
                        .background(Color(.secondarySystemGroupedBackground), in: Capsule())
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.top, 24)
    }

    private var inputBar: some View {
        VStack(spacing: 6) {
            if let voiceError = voice.errorMessage {
                Text(voiceError)
                    .font(.caption)
                    .foregroundStyle(.orange)
            }

            HStack(alignment: .bottom, spacing: 10) {
                TextField(
                    voice.isListening ? "Listening…" : "Ask Clear Path",
                    text: voice.isListening ? .constant(voice.transcript) : $viewModel.draft,
                    axis: .vertical
                )
                .lineLimit(1...4)
                .focused($inputFocused)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20))
                .disabled(voice.isListening)
                .onSubmit {
                    Task { await viewModel.send() }
                }

                if VoiceInput.isSupported {
                    Button {
                        Task { await toggleVoice() }
                    } label: {
                        Image(systemName: voice.isListening ? "stop.circle.fill" : "mic.circle.fill")
                            .font(.system(size: 34))
                            .symbolEffect(.pulse, isActive: voice.isListening)
                    }
                    .disabled(viewModel.isSending)
                    .accessibilityLabel(voice.isListening ? "Stop and send" : "Speak")
                }

                Button {
                    Task { await viewModel.send() }
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 34))
                }
                .disabled(!viewModel.canSend || voice.isListening)
                .accessibilityLabel("Send")
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(.bar)
    }

    /// Tap to talk, tap again to stop and send what was heard.
    private func toggleVoice() async {
        if voice.isListening {
            let spoken = await voice.stop()
            await viewModel.send(spoken)
        } else {
            inputFocused = false
            await voice.start()
        }
    }
}

private struct MessageRow: View {
    let message: AssistantViewModel.Message

    var body: some View {
        switch message.role {
        case .user:
            HStack {
                Spacer(minLength: 48)
                Text(message.text)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color.accentColor, in: RoundedRectangle(cornerRadius: 18))
                    .foregroundStyle(.white)
            }
        case .assistant:
            VStack(alignment: .leading, spacing: 8) {
                if !message.actions.isEmpty {
                    VStack(alignment: .leading, spacing: 4) {
                        ForEach(Array(message.actions.enumerated()), id: \.offset) { _, action in
                            Label {
                                Text(action.succeeded ? action.label : "\(action.label): \(action.error ?? "failed")")
                            } icon: {
                                Image(systemName: action.succeeded ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    .foregroundStyle(action.succeeded ? .green : .orange)
                            }
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                    }
                }

                Text(message.text)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 18))
            }
            .padding(.trailing, 48)
        }
    }
}
