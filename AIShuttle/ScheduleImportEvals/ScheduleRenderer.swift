//
//  ScheduleRenderer.swift
//  Draws a schedule as a PNG or PDF: demo samples and OCR eval inputs.
//

import CoreGraphics
import CoreText
import Foundation
import ImageIO
import UniformTypeIdentifiers

enum ScheduleRenderer {
    static let size = CGSize(width: 1240, height: 1100)

    /// Lines containing "|" are drawn as table rows (one column per cell).
    /// A line starting with "~" is drawn small and grey (fine print).
    static func draw(title: String, lines: [String], in context: CGContext) {
        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        context.fill(CGRect(origin: .zero, size: size))

        var y = size.height - 110
        text(title, at: CGPoint(x: 80, y: y), size: 44, bold: true, in: context)
        y -= 90

        for line in lines {
            if line.hasPrefix("~") {
                text(String(line.dropFirst()), at: CGPoint(x: 80, y: 70), size: 17, grey: true, in: context)
                continue
            }
            let cells = line.split(separator: "|").map { $0.trimmingCharacters(in: .whitespaces) }
            for (column, cell) in cells.enumerated() {
                text(cell, at: CGPoint(x: 80 + CGFloat(column) * 330, y: y), size: 30, bold: column == 0 && cells.count > 1, in: context)
            }
            if cells.count > 1 {
                context.setStrokeColor(CGColor(gray: 0.85, alpha: 1))
                context.setLineWidth(2)
                context.stroke(CGRect(x: 70, y: y - 22, width: size.width - 140, height: 0.5))
            }
            y -= 72
        }
    }

    static func png(title: String, lines: [String]) -> CGImage? {
        guard let context = CGContext(
            data: nil, width: Int(size.width), height: Int(size.height),
            bitsPerComponent: 8, bytesPerRow: 0,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        draw(title: title, lines: lines, in: context)
        return context.makeImage()
    }

    static func writePNG(_ image: CGImage, to url: URL) throws {
        guard let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CocoaError(.fileWriteUnknown)
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { throw CocoaError(.fileWriteUnknown) }
    }

    static func writePDF(title: String, lines: [String], to url: URL) throws {
        var box = CGRect(origin: .zero, size: size)
        guard let context = CGContext(url as CFURL, mediaBox: &box, nil) else {
            throw CocoaError(.fileWriteUnknown)
        }
        context.beginPDFPage(nil)
        draw(title: title, lines: lines, in: context)
        context.endPDFPage()
        context.closePDF()
    }

    private static func text(
        _ string: String, at point: CGPoint, size: CGFloat,
        bold: Bool = false, grey: Bool = false, in context: CGContext
    ) {
        let font = CTFontCreateWithName((bold ? "Helvetica-Bold" : "Helvetica") as CFString, size, nil)
        let colour = grey ? CGColor(gray: 0.55, alpha: 1) : CGColor(gray: 0.1, alpha: 1)
        let attributed = NSAttributedString(string: string, attributes: [
            NSAttributedString.Key(kCTFontAttributeName as String): font,
            NSAttributedString.Key(kCTForegroundColorAttributeName as String): colour,
        ])
        let line = CTLineCreateWithAttributedString(attributed)
        context.textPosition = point
        CTLineDraw(line, context)
    }
}
