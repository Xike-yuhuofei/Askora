#!/usr/bin/env swift
import Cocoa
import ScreenCaptureKit

@available(macOS 12.3, *)
func listWindows() async throws {
    let content = try await SCShareableContent.current
    let windows = content.windows
        .filter { $0.owningApplication != nil }
        .sorted { ($0.owningApplication?.applicationName ?? "") < ($1.owningApplication?.applicationName ?? "") }

    for w in windows {
        guard let app = w.owningApplication else { continue }
        let name = app.applicationName ?? "?"
        let pid = app.processID
        let wid = w.windowID
        let title = w.title ?? ""
        print("WID=\(wid) PID=\(pid) APP=\"\(name)\" TITLE=\"\(title)\" FRAME=\(w.frame)")
    }
}

if #available(macOS 12.3, *) {
    let sema = DispatchSemaphore(value: 0)
    Task {
        do {
            try await listWindows()
        } catch {
            fputs("ERROR: \(error)\n", stderr)
        }
        sema.signal()
    }
    sema.wait()
} else {
    fputs("ERROR: requires macOS 12.3+\n", stderr)
}
