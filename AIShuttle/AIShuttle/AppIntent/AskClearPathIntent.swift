//
//  AskClearPathIntent.swift
//  AIShuttle
//
//  Open-ended Siri requests. App Shortcut phrases can't capture free text,
//  so "Ask Clear Path" makes Siri prompt for the request, which then goes to
//  the same agent and conversation as the in-app chat.
//

import AppIntents
import Foundation
import WidgetKit

struct AskClearPathIntent: AppIntent {
    static var title: LocalizedStringResource = "Ask Clear Path"

    static var description = IntentDescription(
        "Ask Clear Path's assistant to manage your shuttle bookings in your own words, such as moving a ride earlier, booking a specific shuttle or checking what's booked.",
        categoryName: "Assistant",
        searchKeywords: ["ask", "assistant", "change shuttle", "move booking", "cancel shuttle", "Clear Path"]
    )

    @Parameter(title: "Request", requestValueDialog: "What would you like Clear Path to do?")
    var request: String

    init() {}

    init(request: String) {
        self.request = request
    }

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let store = ConversationStore()

        // Simple requests are answered on the iPhone (F14); the rest, or
        // anything the on-device model can't handle, goes to the cloud.
        if let onDevice = await OnDeviceAssistant.live(),
           let answer = await onDevice.answer(request) {
            await OnDeviceTurns.record(
                message: request,
                answer: answer,
                apiClient: .withTimeouts(),
                store: store
            )
            if answer.bookingsChanged {
                WidgetCenter.shared.reloadAllTimelines()
            }
            return .result(dialog: IntentDialog(stringLiteral: answer.reply))
        }

        let response: AssistantMessageResponse
        do {
            response = try await BookingAPIClient.forAssistant().sendAssistantMessage(
                request,
                conversationId: store.currentConversationId
            )
        } catch {
            throw BookingIntentError(error)
        }

        store.save(response.conversationId)
        if response.bookingsChanged {
            WidgetCenter.shared.reloadAllTimelines()
        }

        return .result(dialog: IntentDialog(stringLiteral: response.reply))
    }
}
