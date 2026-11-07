//
//  KeyboardPrewarmer.swift
//  AIShuttle
//
//  The first text field focused in a process makes iOS load the keyboard
//  system (layouts, predictions, dictation, Writing Tools). That blocks the
//  main thread for a moment, and for several seconds when Xcode's debugger
//  is attached, which looked like the chat input "hanging" on the first
//  tap. Paying that cost once, invisibly, while the rider is looking at
//  Home makes the first tap in the chat as quick as later ones.
//

import UIKit

enum KeyboardPrewarmer {
    private static var done = false

    /// Focuses and immediately unfocuses an off-screen field, in the same
    /// run-loop turn, so no keyboard is ever drawn. Once per launch.
    static func prewarm() {
        guard !done else { return }

        let window = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .filter { $0.activationState == .foregroundActive }
            .flatMap(\.windows)
            .first(where: \.isKeyWindow)
        guard let window else { return }

        // Something already has focus (the rider is typing): nothing to do.
        if window.findFirstResponder() != nil { done = true; return }

        done = true
        let field = UITextField(frame: CGRect(x: -1000, y: -1000, width: 10, height: 10))
        field.isAccessibilityElement = false
        // Same traits as the chat field, so the same input features load.
        field.autocorrectionType = .default
        field.spellCheckingType = .default
        window.addSubview(field)
        field.becomeFirstResponder()
        field.resignFirstResponder()
        field.removeFromSuperview()
    }
}

private extension UIView {
    func findFirstResponder() -> UIResponder? {
        if isFirstResponder { return self }
        for subview in subviews {
            if let responder = subview.findFirstResponder() { return responder }
        }
        return nil
    }
}
