import type React from "react"
import type { Metadata, Viewport } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "TraeWork — Code",
  description: "Pixel-fidelity replica of the TraeWork macOS AI IDE home screen.",
}

export const viewport: Viewport = {
  themeColor: "#222222",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body className="antialiased">{children}</body>
    </html>
  )
}
