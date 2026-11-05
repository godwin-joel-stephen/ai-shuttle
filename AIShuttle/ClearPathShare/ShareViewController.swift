//
//  ShareViewController.swift
//  ClearPathShare: "Clear Path" in the share sheet for a schedule photo,
//  screenshot, PDF or text. The whole import runs inside the sheet, so
//  the user never has to leave the app they shared from.
//

import SwiftUI
import UIKit
import UniformTypeIdentifiers

@objc(ShareViewController)
final class ShareViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()

        let providers = (extensionContext?.inputItems as? [NSExtensionItem] ?? [])
            .flatMap { $0.attachments ?? [] }

        let model = ScheduleImportModel(loadSource: {
            try await SharedItemLoader.source(from: providers)
        })
        let root = ScheduleImportView(model: model) { [weak self] in
            self?.extensionContext?.completeRequest(returningItems: nil)
        }

        let host = UIHostingController(rootView: root)
        addChild(host)
        host.view.frame = view.bounds
        host.view.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(host.view)
        host.didMove(toParent: self)
    }
}

/// Picks the first usable attachment: PDF, then image, then text.
enum SharedItemLoader {
    static func source(from providers: [NSItemProvider]) async throws -> ScheduleSource {
        if let provider = providers.first(where: { $0.hasItemConformingToTypeIdentifier(UTType.pdf.identifier) }) {
            return .pdf(try await data(from: provider, type: .pdf))
        }
        if let provider = providers.first(where: { $0.hasItemConformingToTypeIdentifier(UTType.image.identifier) }) {
            return .image(try await data(from: provider, type: .image))
        }
        if let provider = providers.first(where: { $0.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) }) {
            let item = try await provider.loadItem(forTypeIdentifier: UTType.plainText.identifier)
            switch item {
            case let text as String:
                return .text(text)
            case let data as Data:
                return .text(String(decoding: data, as: UTF8.self))
            case let url as URL:
                return .text(try String(contentsOf: url, encoding: .utf8))
            default:
                throw ScheduleImportError.unreadableDocument
            }
        }
        throw ScheduleImportError.unsupportedContent
    }

    private static func data(from provider: NSItemProvider, type: UTType) async throws -> Data {
        try await withCheckedThrowingContinuation { continuation in
            _ = provider.loadDataRepresentation(for: type) { data, error in
                if let data {
                    continuation.resume(returning: data)
                } else {
                    continuation.resume(throwing: error ?? ScheduleImportError.unreadableDocument)
                }
            }
        }
    }
}
