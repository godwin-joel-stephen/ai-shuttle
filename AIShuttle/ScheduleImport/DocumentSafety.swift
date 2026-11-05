//
//  DocumentSafety.swift
//  Prompt-injection screening for imported documents (F13).
//
//  An imported document is untrusted. Defence in depth:
//  1. Lines that read like instructions to an AI are removed here, before
//     any model sees the text, and shown to the user as "ignored".
//  2. The on-device model is told the document is data, has no tools,
//     and can only produce the typed schedule schema (guided generation).
//  3. Output is validated (dates, horizon, weekday cross-check).
//  4. Only typed {date, kind} days reach the backend; it applies the same
//     booking rules as every other client.
//  5. Nothing changes until the user reviews the days and taps Apply.
//

import Foundation

nonisolated enum DocumentSafety {
    struct Report: Equatable, Sendable {
        /// The document without flagged lines.
        let cleanedText: String
        /// Lines removed because they look like instructions.
        let flaggedLines: [String]
    }

    static func scan(_ text: String) -> Report {
        var kept: [String] = []
        var flagged: [String] = []

        for line in text.components(separatedBy: .newlines) {
            if looksLikeInstruction(line) {
                flagged.append(line.trimmingCharacters(in: .whitespaces))
            } else {
                kept.append(line)
            }
        }

        return Report(cleanedText: kept.joined(separator: "\n"), flaggedLines: flagged)
    }

    static func looksLikeInstruction(_ line: String) -> Bool {
        let lowered = line.lowercased()
        return patterns.contains { lowered.contains($0) }
    }

    // Lowercased regexes; deliberately broad. A false positive costs one
    // line the user can still see; a miss is caught by the later layers.
    // Computed: Regex isn't Sendable, so it can't be a shared static let.
    private static var patterns: [Regex<Substring>] { [
        // "Ignore all previous instructions", "disregard the rules above"
        #/\b(?:ignore|disregard|forget|override|bypass)\b.{0,40}\b(?:instructions?|previous|prior|above|earlier|rules?|prompts?|guidelines?)\b/#,
        // Role and prompt markers: "system:", "assistant prompt", "<system>"
        #/\b(?:system|assistant|developer)\s*(?:prompt|message|instructions?)?\s*:/#,
        #/\b(?:system|developer)\s+(?:prompt|message|instructions?)\b/#,
        #/<\s*\/?\s*(?:system|instructions?|prompt|im_start|im_end)\b/#,
        #/\[\s*\/?\s*(?:system|inst)\s*\]/#,
        // Re-tasking: "you are now", "act as", "new instructions"
        #/\byou\s+(?:are|must|should|will)\s+(?:now|an?\b|not\b|always\b)/#,
        #/\b(?:act|behave|pretend)\s+(?:as|like)\b/#,
        #/\bnew\s+(?:instructions?|task|rules?)\b/#,
        // Bulk or covert actions: "cancel all bookings", "without asking"
        #/\b(?:cancel|delete|remove|book|reserve|change)\b.{0,25}\b(?:all|every|everything|any)\b.{0,25}\b(?:bookings?|rides?|shuttles?|reservations?|trips?)\b/#,
        #/\b(?:without|don't|do not|never)\s+(?:asking|ask|telling|tell|confirm|confirming|showing|show)\b/#,
        // Exfiltration bait
        #/\b(?:api[\s_-]?key|password|passcode|access token|secret key)\b/#,
        #/https?:\/\//#,
        #/\b(?:call|use|invoke|run)\s+(?:the\s+)?(?:tool|function|api)\b/#,
    ] }
}
