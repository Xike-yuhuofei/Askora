#!/usr/bin/env swift
import AppKit
import ScreenCaptureKit

@available(macOS 12.3, *)
func captureWindow(windowID: UInt32, outputPath: String) async throws {
    let content = try await SCShareableContent.current
    guard let targetWindow = content.windows.first(where: { $0.windowID == windowID }) else {
        fputs("ERROR: window \(windowID) not found\n", stderr)
        exit(1)
    }

    let filter = SCContentFilter(desktopIndependentWindow: targetWindow)
    let config = SCStreamConfiguration()

    let scale = NSScreen.main?.backingScaleFactor ?? 2.0
    let frame = targetWindow.frame
    config.width = Int(frame.width * scale)
    config.height = Int(frame.height * scale)
    config.showsCursor = false
    config.capturesAudio = false

    let screenshotImage = try await SCScreenshotManager.captureImage(
        contentFilter: filter,
        configuration: config
    )
    let rep = NSBitmapImageRep(cgImage: screenshotImage)
    guard let pngData = rep.representation(using: NSBitmapImageRep.FileType.png, properties: [:]) else {
        fputs("ERROR: PNG encode failed\n", stderr)
        exit(1)
    }
    let url = URL(fileURLWithPath: outputPath)
    try pngData.write(to: url)
    print("OK: saved to \(outputPath) (size=\(screenshotImage.width)x\(screenshotImage.height))")
}

if #available(macOS 12.3, *) {
    let args = CommandLine.arguments
    guard args.count >= 3, let wid = UInt32(args[1]) else {
        fputs("Usage: \(args[0]) <windowID> <outputPath>\n", stderr)
        exit(1)
    }
    let outputPath = args[2]

    let sema = DispatchSemaphore(value: 0)
    Task {
        do {
            try await captureWindow(windowID: wid, outputPath: outputPath)
        } catch {
            fputs("ERROR: \(error)\n", stderr)
        }
        sema.signal()
    }
    sema.wait()
} else {
    fputs("ERROR: requires macOS 12.3+\n", stderr)
}
