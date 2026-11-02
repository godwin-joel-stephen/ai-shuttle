//
//  VoiceInput.swift
//  AIShuttle
//
//  On-device speech-to-text with iOS 26's SpeechAnalyzer. Audio never
//  leaves the phone; only the final text is sent to the agent.
//

@preconcurrency import AVFoundation
import Foundation
import Observation
import Speech

@MainActor
@Observable
final class VoiceInput {
    private(set) var transcript = ""
    private(set) var isListening = false
    var errorMessage: String?

    static var isSupported: Bool {
        SpeechTranscriber.isAvailable
    }

    private var analyzer: SpeechAnalyzer?
    private var audioEngine: AVAudioEngine?
    private var inputContinuation: AsyncStream<AnalyzerInput>.Continuation?
    private var resultsTask: Task<Void, Never>?
    private var finalizedText = ""

    func start() async {
        guard !isListening else { return }
        transcript = ""
        finalizedText = ""
        errorMessage = nil

        do {
            guard await AVAudioApplication.requestRecordPermission() else {
                errorMessage = "Allow microphone access in Settings to talk to Clear Path."
                return
            }

            guard let locale = await SpeechTranscriber.supportedLocale(equivalentTo: .current) else {
                errorMessage = "Voice input isn't available in your language yet."
                return
            }

            let transcriber = SpeechTranscriber(locale: locale, preset: .progressiveTranscription)

            // The speech model is downloaded on first use.
            if let installation = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
                try await installation.downloadAndInstall()
            }

            let analyzer = SpeechAnalyzer(modules: [transcriber])

            // Bias recognition toward this app's vocabulary ("Clear Path"
            // was otherwise heard as "clear pass" or "clear footpath").
            let context = AnalysisContext()
            context.contextualStrings[.general] = ["Clear Path", "shuttle", "usual shuttle", "earlier", "later"]
            try await analyzer.setContext(context)

            guard let analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber]) else {
                errorMessage = "Voice input isn't available on this device."
                return
            }

            let (inputSequence, continuation) = AsyncStream.makeStream(of: AnalyzerInput.self)

            resultsTask = Task { [weak self] in
                do {
                    for try await result in transcriber.results {
                        self?.receive(String(result.text.characters), isFinal: result.isFinal)
                    }
                } catch {
                    self?.errorMessage = "Voice input stopped unexpectedly."
                }
            }

            try await analyzer.start(inputSequence: inputSequence)
            let engine = try Self.startAudioEngine(feeding: continuation, convertingTo: analyzerFormat)

            self.analyzer = analyzer
            self.audioEngine = engine
            self.inputContinuation = continuation
            isListening = true
        } catch {
            errorMessage = "Couldn't start voice input: \(error.localizedDescription)"
            await stop()
        }
    }

    /// Stops listening and returns the final transcript.
    @discardableResult
    func stop() async -> String {
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        inputContinuation?.finish()

        try? await analyzer?.finalizeAndFinishThroughEndOfInput()
        await resultsTask?.value

        audioEngine = nil
        inputContinuation = nil
        analyzer = nil
        resultsTask = nil
        isListening = false
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)

        return transcript
    }

    private func receive(_ text: String, isFinal: Bool) {
        if isFinal {
            finalizedText += text
            transcript = finalizedText
        } else {
            // Volatile results are revised as more audio arrives.
            transcript = finalizedText + text
        }
    }

    /// Runs on the audio render thread via the tap, so it must not inherit
    /// the main actor isolation that is this module's default.
    nonisolated private static func startAudioEngine(
        feeding continuation: AsyncStream<AnalyzerInput>.Continuation,
        convertingTo analyzerFormat: AVAudioFormat
    ) throws -> AVAudioEngine {
        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement, options: .duckOthers)
        try session.setActive(true, options: .notifyOthersOnDeactivation)

        let engine = AVAudioEngine()
        let inputNode = engine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)
        let converter = AVAudioConverter(from: inputFormat, to: analyzerFormat)

        inputNode.installTap(onBus: 0, bufferSize: 4096, format: inputFormat) { buffer, _ in
            guard let converter,
                  let converted = convert(buffer, with: converter, to: analyzerFormat) else {
                return
            }
            continuation.yield(AnalyzerInput(buffer: converted))
        }

        engine.prepare()
        try engine.start()
        return engine
    }

    nonisolated private static func convert(
        _ buffer: AVAudioPCMBuffer,
        with converter: AVAudioConverter,
        to format: AVAudioFormat
    ) -> AVAudioPCMBuffer? {
        let ratio = format.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount((Double(buffer.frameLength) * ratio).rounded(.up))

        guard let output = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: capacity) else {
            return nil
        }

        // The input block runs synchronously inside convert(to:), so the
        // buffer never actually crosses threads.
        nonisolated(unsafe) let input = buffer
        nonisolated(unsafe) var consumed = false
        var error: NSError?
        converter.convert(to: output, error: &error) { _, status in
            if consumed {
                status.pointee = .noDataNow
                return nil
            }
            consumed = true
            status.pointee = .haveData
            return input
        }

        return error == nil ? output : nil
    }
}
