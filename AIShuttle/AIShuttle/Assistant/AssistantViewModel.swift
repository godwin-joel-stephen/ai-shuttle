//
//  AssistantViewModel.swift
//  AIShuttle
//

import Foundation
import Observation
import OSLog

@MainActor
@Observable
final class AssistantViewModel {
    struct Message: Identifiable, Equatable {
        enum Role {
            case user
            case assistant
        }

        let id = UUID()
        let role: Role
        let text: String
        var actions: [AssistantActionDTO] = []
        var sources: [String] = []
        /// Answered by Apple's on-device model, not the cloud agent.
        var onDevice = false
    }

    static let suggestions = [
        "Book my usual shuttle for tomorrow",
        "Make it 30 minutes earlier",
        "Book Friday, the latest shuttle",
        "Why can't I book Saturday?",
        "What do I have booked?"
    ]

    private(set) var messages: [Message] = []
    private(set) var isSending = false
    var draft = ""
    var errorMessage: String?

    private let apiClient: BookingAPIClient
    private let store: ConversationStore
    private let onBookingsChanged: () async -> Void
    /// Answers simple requests on the phone; nil sends everything to the
    /// cloud agent (tests, or no Apple Intelligence).
    private let onDevice: OnDeviceAssistant?

    init(
        apiClient: BookingAPIClient = .forAssistant(),
        store: ConversationStore = ConversationStore(),
        onDevice: OnDeviceAssistant? = nil,
        onBookingsChanged: @escaping () async -> Void = {}
    ) {
        self.apiClient = apiClient
        self.store = store
        self.onDevice = onDevice
        self.onBookingsChanged = onBookingsChanged
    }

    var canSend: Bool {
        !isSending && !draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    /// Shows the current conversation, including requests made via Siri.
    func loadConversation() async {
        guard messages.isEmpty, let id = store.currentConversationId else { return }

        guard let conversation = try? await apiClient.fetchConversation(id: id) else { return }
        messages = conversation.messages.map {
            Message(
                role: $0.role == "user" ? .user : .assistant,
                text: $0.text,
                actions: $0.actions,
                sources: $0.sources ?? [],
                onDevice: $0.onDevice ?? false
            )
        }
    }

    func send(_ text: String? = nil) async {
        let message = (text ?? draft).trimmingCharacters(in: .whitespacesAndNewlines)
        guard !message.isEmpty, !isSending else { return }

        draft = ""
        errorMessage = nil
        messages.append(Message(role: .user, text: message))
        isSending = true
        defer { isSending = false }

        if let onDevice, let answer = await onDevice.answer(message) {
            messages.append(
                Message(role: .assistant, text: answer.reply, actions: answer.actions, onDevice: true)
            )
            await OnDeviceTurns.record(message: message, answer: answer, apiClient: apiClient, store: store)
            if answer.bookingsChanged {
                await onBookingsChanged()
            }
            return
        }

        do {
            let response = try await apiClient.sendAssistantMessage(
                message,
                conversationId: store.currentConversationId
            )
            store.save(response.conversationId)
            messages.append(
                Message(
                    role: .assistant,
                    text: response.reply,
                    actions: response.actions,
                    sources: response.sources ?? []
                )
            )

            if response.bookingsChanged {
                await onBookingsChanged()
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func startNewConversation() {
        store.reset()
        messages = []
        errorMessage = nil
    }
}

/// Shared by the chat and "Ask Clear Path" after an on-device answer.
enum OnDeviceTurns {
    /// Best effort: the answer has already been given, so a failure here
    /// only means the cloud agent won't see this turn.
    static func record(
        message: String,
        answer: OnDeviceAnswer,
        apiClient: BookingAPIClient,
        store: ConversationStore
    ) async {
        if let date = answer.bookedDate, answer.bookingsChanged {
            HabitReminderID.withdraw(for: date)
        }
        do {
            let id = try await apiClient.recordOnDeviceTurn(
                message: message,
                reply: answer.reply,
                actions: answer.actions,
                conversationId: store.currentConversationId
            )
            store.save(id)
        } catch {
            Logger.onDevice.error("Couldn't record the on-device turn: \(error.localizedDescription, privacy: .public)")
        }
    }
}
