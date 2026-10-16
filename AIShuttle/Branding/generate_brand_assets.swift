#!/usr/bin/env swift
//
// Clear Path brand asset generator.
//
// Draws the app icon (default, dark, tinted) and the launch-screen logo
// with CoreGraphics so the artwork is vector-defined and reproducible.
//
// Usage (from the AIShuttle/ directory that contains AIShuttle.xcodeproj):
//     swift Branding/generate_brand_assets.swift
//

import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

// MARK: - Palette

func rgb(_ hex: UInt32, _ alpha: CGFloat = 1) -> CGColor {
    CGColor(
        srgbRed: CGFloat((hex >> 16) & 0xFF) / 255,
        green: CGFloat((hex >> 8) & 0xFF) / 255,
        blue: CGFloat(hex & 0xFF) / 255,
        alpha: alpha
    )
}

struct Palette {
    var backgroundTop: CGColor?
    var backgroundBottom: CGColor?
    var glow: CGColor
    var roadNear: CGColor
    var roadFar: CGColor
    var dash: CGColor
    var body: CGColor
    var bodyLower: CGColor
    var windshieldTop: CGColor
    var windshieldBottom: CGColor
    var accent: CGColor
    var grille: CGColor
    var wheel: CGColor
    var shadow: CGColor
    var fadeRoad: Bool

    static let standard = Palette(
        backgroundTop: rgb(0x0A1F3D),
        backgroundBottom: rgb(0x14407A),
        glow: rgb(0xFFFFFF, 0.10),
        roadNear: rgb(0x3DD6C6),
        roadFar: rgb(0x1FA89F),
        dash: rgb(0xF2FFFD),
        body: rgb(0xF7FBFD),
        bodyLower: rgb(0xDCE8F0),
        windshieldTop: rgb(0x1E5A9C),
        windshieldBottom: rgb(0x0E2B52),
        accent: rgb(0x2EC4B6),
        grille: rgb(0xC3D3DF),
        wheel: rgb(0x061427),
        shadow: rgb(0x000000, 0.30),
        fadeRoad: false
    )

    static let dark: Palette = {
        var p = standard
        p.backgroundTop = rgb(0x040B17)
        p.backgroundBottom = rgb(0x0B2342)
        p.glow = rgb(0xFFFFFF, 0.06)
        return p
    }()

    static let tinted = Palette(
        backgroundTop: rgb(0x000000),
        backgroundBottom: rgb(0x000000),
        glow: rgb(0xFFFFFF, 0.0),
        roadNear: rgb(0x8C8C8C),
        roadFar: rgb(0x6A6A6A),
        dash: rgb(0xFFFFFF),
        body: rgb(0xFFFFFF),
        bodyLower: rgb(0xE2E2E2),
        windshieldTop: rgb(0x3A3A3A),
        windshieldBottom: rgb(0x1E1E1E),
        accent: rgb(0xB4B4B4),
        grille: rgb(0xC8C8C8),
        wheel: rgb(0x000000),
        shadow: rgb(0x000000, 0.45),
        fadeRoad: false
    )

    static let launch: Palette = {
        var p = standard
        p.backgroundTop = nil
        p.backgroundBottom = nil
        p.glow = rgb(0xFFFFFF, 0.0)
        p.fadeRoad = true
        return p
    }()
}

// MARK: - Drawing (1024 x 1024 design space, y grows downward)

func roundedRect(_ rect: CGRect, _ radius: CGFloat) -> CGPath {
    CGPath(roundedRect: rect, cornerWidth: radius, cornerHeight: radius, transform: nil)
}

func fillVertical(_ ctx: CGContext, path: CGPath, top: CGColor, bottom: CGColor, from y0: CGFloat, to y1: CGFloat) {
    ctx.saveGState()
    ctx.addPath(path)
    ctx.clip()
    let gradient = CGGradient(colorsSpace: CGColorSpace(name: CGColorSpace.sRGB), colors: [top, bottom] as CFArray, locations: [0, 1])!
    ctx.drawLinearGradient(gradient, start: CGPoint(x: 0, y: y0), end: CGPoint(x: 0, y: y1), options: [.drawsBeforeStartLocation, .drawsAfterEndLocation])
    ctx.restoreGState()
}

func fill(_ ctx: CGContext, _ path: CGPath, _ color: CGColor) {
    ctx.addPath(path)
    ctx.setFillColor(color)
    ctx.fillPath()
}

func drawMark(in ctx: CGContext, palette p: Palette) {
    let canvas = CGRect(x: 0, y: 0, width: 1024, height: 1024)

    // Background
    if let top = p.backgroundTop, let bottom = p.backgroundBottom {
        fillVertical(ctx, path: CGPath(rect: canvas, transform: nil), top: top, bottom: bottom, from: 0, to: 1024)
        let glow = CGGradient(colorsSpace: CGColorSpace(name: CGColorSpace.sRGB), colors: [p.glow, p.glow.copy(alpha: 0)!] as CFArray, locations: [0, 1])!
        ctx.drawRadialGradient(glow, startCenter: CGPoint(x: 512, y: 430), startRadius: 0, endCenter: CGPoint(x: 512, y: 430), endRadius: 460, options: [])
    }

    // Road: a perspective path whose vanishing point is hidden behind the
    // shuttle, so the vehicle appears to travel toward the viewer.
    let road = CGMutablePath()
    road.move(to: CGPoint(x: 512, y: 300))
    road.addLine(to: CGPoint(x: 940, y: 1024))
    road.addLine(to: CGPoint(x: 84, y: 1024))
    road.closeSubpath()
    let roadEnd: CGColor = p.fadeRoad ? p.roadNear.copy(alpha: 0)! : p.roadNear
    fillVertical(ctx, path: road, top: p.roadFar, bottom: roadEnd, from: 590, to: p.fadeRoad ? 900 : 1024)

    // Centre-line dashes, scaled for perspective.
    let dashes: [(y: CGFloat, h: CGFloat, w: CGFloat)] = [
        (668, 40, 16), (742, 58, 22), (836, 80, 30), (954, 110, 40),
    ]
    for d in dashes {
        let alpha: CGFloat = p.fadeRoad ? max(0, 1 - (d.y - 640) / 240) : 0.95
        guard alpha > 0 else { continue }
        fill(ctx, roundedRect(CGRect(x: 512 - d.w / 2, y: d.y, width: d.w, height: d.h), d.w / 2), p.dash.copy(alpha: alpha)!)
    }

    // Ground shadow under the shuttle, kept on the road surface.
    ctx.saveGState()
    ctx.addPath(road)
    ctx.clip()
    ctx.addEllipse(in: CGRect(x: 312, y: 604, width: 400, height: 44))
    ctx.setFillColor(p.shadow)
    ctx.fillPath()
    ctx.restoreGState()

    // Wheels, mirrors and roof light sit behind the body.
    fill(ctx, roundedRect(CGRect(x: 370, y: 556, width: 62, height: 76), 20), p.wheel)
    fill(ctx, roundedRect(CGRect(x: 592, y: 556, width: 62, height: 76), 20), p.wheel)
    fill(ctx, roundedRect(CGRect(x: 314, y: 344, width: 40, height: 64), 14), p.bodyLower)
    fill(ctx, roundedRect(CGRect(x: 670, y: 344, width: 40, height: 64), 14), p.bodyLower)
    fill(ctx, roundedRect(CGRect(x: 456, y: 258, width: 112, height: 48), 16), p.accent)

    // Body with a subtly shaded lower panel.
    let body = roundedRect(CGRect(x: 342, y: 284, width: 340, height: 306), 66)
    fill(ctx, body, p.body)
    ctx.saveGState()
    ctx.addPath(body)
    ctx.clip()
    ctx.setFillColor(p.bodyLower)
    ctx.fill(CGRect(x: 342, y: 494, width: 340, height: 96))
    ctx.restoreGState()

    // Windshield with a soft diagonal sheen.
    let windshield = roundedRect(CGRect(x: 376, y: 318, width: 272, height: 140), 36)
    fillVertical(ctx, path: windshield, top: p.windshieldTop, bottom: p.windshieldBottom, from: 318, to: 458)
    ctx.saveGState()
    ctx.addPath(windshield)
    ctx.clip()
    let sheen = CGMutablePath()
    sheen.move(to: CGPoint(x: 470, y: 318))
    sheen.addLine(to: CGPoint(x: 540, y: 318))
    sheen.addLine(to: CGPoint(x: 450, y: 458))
    sheen.addLine(to: CGPoint(x: 380, y: 458))
    sheen.closeSubpath()
    fill(ctx, sheen, rgb(0xFFFFFF, 0.10))
    ctx.restoreGState()

    // Headlights and grille.
    ctx.setFillColor(p.accent)
    ctx.addEllipse(in: CGRect(x: 384, y: 508, width: 48, height: 48))
    ctx.addEllipse(in: CGRect(x: 592, y: 508, width: 48, height: 48))
    ctx.fillPath()
    fill(ctx, roundedRect(CGRect(x: 466, y: 520, width: 92, height: 24), 12), p.grille)
}

// MARK: - Rendering

func render(size: CGSize, crop: CGRect, opaque: Bool, palette: Palette, to url: URL) {
    let ctx = CGContext(
        data: nil,
        width: Int(size.width),
        height: Int(size.height),
        bitsPerComponent: 8,
        bytesPerRow: 0,
        space: CGColorSpace(name: CGColorSpace.sRGB)!,
        bitmapInfo: opaque ? CGImageAlphaInfo.noneSkipLast.rawValue : CGImageAlphaInfo.premultipliedLast.rawValue
    )!
    ctx.interpolationQuality = .high
    ctx.setShouldAntialias(true)
    // Flip to a top-left origin and map the crop rect onto the output.
    ctx.translateBy(x: 0, y: size.height)
    ctx.scaleBy(x: size.width / crop.width, y: -size.height / crop.height)
    ctx.translateBy(x: -crop.minX, y: -crop.minY)
    drawMark(in: ctx, palette: palette)

    let image = ctx.makeImage()!
    let dest = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil)!
    CGImageDestinationAddImage(dest, image, nil)
    guard CGImageDestinationFinalize(dest) else { fatalError("Failed to write \(url.path)") }
    print("wrote \(url.path)")
}

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let assets = root.appendingPathComponent("AIShuttle/Assets.xcassets")
let iconSet = assets.appendingPathComponent("AppIcon.appiconset")
let logoSet = assets.appendingPathComponent("LaunchLogo.imageset")
try FileManager.default.createDirectory(at: logoSet, withIntermediateDirectories: true)

let full = CGRect(x: 0, y: 0, width: 1024, height: 1024)
let iconSize = CGSize(width: 1024, height: 1024)
render(size: iconSize, crop: full, opaque: true, palette: .standard, to: iconSet.appendingPathComponent("AppIcon.png"))
render(size: iconSize, crop: full, opaque: true, palette: .dark, to: iconSet.appendingPathComponent("AppIcon-Dark.png"))
render(size: iconSize, crop: full, opaque: true, palette: .tinted, to: iconSet.appendingPathComponent("AppIcon-Tinted.png"))

// Launch logo: 240 x 224 pt, cropped tightly around the shuttle and fading road.
let logoCrop = CGRect(x: 152, y: 244, width: 720, height: 672)
render(size: CGSize(width: 480, height: 448), crop: logoCrop, opaque: false, palette: .launch, to: logoSet.appendingPathComponent("LaunchLogo@2x.png"))
render(size: CGSize(width: 720, height: 672), crop: logoCrop, opaque: false, palette: .launch, to: logoSet.appendingPathComponent("LaunchLogo@3x.png"))
