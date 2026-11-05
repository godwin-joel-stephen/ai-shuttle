//
//  ScheduleTextReader.swift
//  Turns a shared photo, PDF or text into plain text, on-device.
//

import CoreGraphics
import Foundation
import ImageIO
import PDFKit
import Vision

nonisolated enum ScheduleSource: Sendable {
    case image(Data)
    case pdf(Data)
    case text(String)
}

enum ScheduleTextReader {
    /// The on-device model's context is ~4k tokens, shared with the
    /// instructions, calendar and output; a weekly schedule is far shorter.
    static let maxCharacters = 3_000
    /// Long side for OCR; full-resolution photos waste memory (share
    /// extensions are limited to ~120 MB).
    static let maxImageDimension = 2_400
    static let maxPDFPages = 3

    static func read(_ source: ScheduleSource) async throws -> String {
        let text: String
        switch source {
        case .text(let string):
            text = string
        case .image(let data):
            guard let image = downscaledImage(from: data) else {
                throw ScheduleImportError.unreadableDocument
            }
            text = try await recognizeText(in: image)
        case .pdf(let data):
            text = try await readPDF(data)
        }

        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { throw ScheduleImportError.noText }
        return String(trimmed.prefix(maxCharacters))
    }

    // MARK: - Images

    static func recognizeText(in image: CGImage) async throws -> String {
        var request = RecognizeTextRequest()
        request.recognitionLevel = .accurate
        request.usesLanguageCorrection = true
        request.customWords = ["WFH", "WFO", "PTO", "OOO", "Offsite", "Hybrid"]

        let observations = try await request.perform(on: image)
        let pieces = observations.map { observation in
            TextPiece(
                text: observation.topCandidates(1).first?.string ?? observation.transcript,
                box: observation.boundingBox.cgRect
            )
        }
        return rows(from: pieces).joined(separator: "\n")
    }

    struct TextPiece: Equatable {
        let text: String
        /// Normalized, origin at the bottom left (Vision's convention).
        let box: CGRect
    }

    /// Vision returns table cells separately; put cells that share a line
    /// back together ("Mon 9 Nov | Office") so a row keeps its meaning.
    static func rows(from pieces: [TextPiece]) -> [String] {
        let sorted = pieces.sorted { $0.box.midY > $1.box.midY }
        var rows: [[TextPiece]] = []

        for piece in sorted {
            if let last = rows.last, let anchor = last.first,
               abs(anchor.box.midY - piece.box.midY) < min(anchor.box.height, piece.box.height) * 0.6 {
                rows[rows.count - 1].append(piece)
            } else {
                rows.append([piece])
            }
        }

        return rows.map { row in
            row.sorted { $0.box.minX < $1.box.minX }
                .map(\.text)
                .joined(separator: " | ")
        }
    }

    static func downscaledImage(from data: Data) -> CGImage? {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil) else { return nil }
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,  // apply EXIF orientation
            kCGImageSourceThumbnailMaxPixelSize: maxImageDimension,
        ]
        return CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary)
    }

    // MARK: - PDFs

    static func readPDF(_ data: Data) async throws -> String {
        guard let document = PDFDocument(data: data), document.pageCount > 0 else {
            throw ScheduleImportError.unreadableDocument
        }
        let pages = (0..<min(document.pageCount, maxPDFPages)).compactMap(document.page(at:))

        // Text PDFs (exported from a calendar or HR tool) have a text layer.
        let embedded = pages.compactMap(\.string).joined(separator: "\n")
        if embedded.filter({ $0.isLetter }).count >= 20 {
            return embedded
        }

        // Scanned PDFs: render each page and read it like a photo.
        var recognized: [String] = []
        for page in pages {
            if let image = render(page) {
                recognized.append(try await recognizeText(in: image))
            }
        }
        return recognized.joined(separator: "\n")
    }

    static func render(_ page: PDFPage) -> CGImage? {
        let bounds = page.bounds(for: .mediaBox)
        guard bounds.width > 0, bounds.height > 0 else { return nil }
        let scale = CGFloat(maxImageDimension) / max(bounds.width, bounds.height)
        let width = Int(bounds.width * scale)
        let height = Int(bounds.height * scale)

        guard let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }

        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        context.scaleBy(x: scale, y: scale)
        page.draw(with: .mediaBox, to: context)
        return context.makeImage()
    }
}
