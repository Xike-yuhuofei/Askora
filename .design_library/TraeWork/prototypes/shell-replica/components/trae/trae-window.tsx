/*
  Window chrome — measured from the reference PNG (1326×1299):
  - window bg #222222, 1px top highlight line #595959
  - sidebar sits directly on the frame (301px + 1px divider)
  - main card #171717: inset top 3px / right 8px / bottom 4px,
    1px border #2c2c2c, radius ~10px
*/

import { Sidebar } from "./sidebar"
import { ChatWorkspace } from "./chat-workspace"

export function TraeWindow() {
  return (
    <div className="flex h-dvh w-full flex-col overflow-hidden bg-frame">
      {/* 1px window top highlight */}
      <div className="h-px shrink-0 bg-edge-top" />
      <div className="flex min-h-0 flex-1">
        <Sidebar />
        <main className="mb-2 mr-2 mt-[8px] flex min-w-0 flex-1 flex-col overflow-hidden rounded-[10px] border border-border-card bg-main">
          <ChatWorkspace />
        </main>
      </div>
    </div>
  )
}
