import AppKit
import ScreenCaptureKit

@available(macOS 12.3, *)
final class AppDelegate: NSObject, NSApplicationDelegate {
    let windowID: UInt32
    let outputPath: String
    let scaleOverride: CGFloat?
    let sema = DispatchSemaphore(value: 0)

    init(windowID: UInt32, outputPath: String, scaleOverride: CGFloat?) {
        self.windowID = windowID
        self.outputPath = outputPath
        self.scaleOverride = scaleOverride
        super.init()
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        Task {
            do {
                try await run()
            } catch {
                fputs("ERROR: \(error)\n", stderr)
            }
            sema.signal()
            NSApp.terminate(nil)
        }
    }

    func run() async throws {
        let content = try await SCShareableContent.current
        guard let targetWindow = content.windows.first(where: { $0.windowID == windowID }) else {
            fputs("ERROR: window \(windowID) not found\n", stderr)
            exit(1)
        }

        let filter = SCContentFilter(desktopIndependentWindow: targetWindow)
        let config = SCStreamConfiguration()

        let requestedScale: CGFloat
        if let s = scaleOverride {
            requestedScale = s
        } else {
            let scaleFromScreens = NSScreen.screens.map { $0.backingScaleFactor }.max() ?? 2.0
            requestedScale = scaleFromScreens
        }
        let frame = targetWindow.frame
        config.width = Int(frame.width * requestedScale)
        config.height = Int(frame.height * requestedScale)
        config.showsCursor = false
        config.capturesAudio = false
        config.scalesToFit = true

        let screenshotImage = try await SCScreenshotManager.captureImage(
            contentFilter: filter,
            configuration: config
        )
        let rep = NSBitmapImageRep(cgImage: screenshotImage)
        guard let pngData = rep.representation(using: .png, properties: [:]) else {
            fputs("ERROR: PNG encode failed\n", stderr)
            exit(1)
        }
        let url = URL(fileURLWithPath: outputPath)
        try pngData.write(to: url)
        print("OK: scale=\(requestedScale) saved to \(outputPath) (size=\(screenshotImage.width)x\(screenshotImage.height))")
    }
}

let args = CommandLine.arguments
guard args.count >= 3, let wid = UInt32(args[1]) else {
    fputs("Usage: \(args[0]) <windowID> <outputPath> [scaleFactor]\n", stderr)
    exit(1)
}
let outputPath = args[2]
let scaleOverride: CGFloat? = args.count >= 4 ? CGFloat(Double(args[3]) ?? 0) : nil
if let s = scaleOverride, s <= 0 {
    fputs("ERROR: invalid scale \(args[3])\n", stderr)
    exit(1)
}

if #available(macOS 12.3, *) {
    let app = NSApplication.shared
    let delegate = AppDelegate(windowID: wid, outputPath: outputPath, scaleOverride: scaleOverride)
    app.delegate = delegate
    app.setActivationPolicy(.accessory)
    app.run()
} else {
    fputs("ERROR: requires macOS 12.3+\n", stderr)
}
