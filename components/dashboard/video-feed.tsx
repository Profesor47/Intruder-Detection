'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function VideoFeed() {
  const [isStreaming, setIsStreaming] = useState(true)
  const [fps, setFps] = useState(0)

  useEffect(() => {
    // Poll FPS from backend
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/status')
        const data = await res.json()
        setFps(Math.round(data.fps || 0))
      } catch {
        setIsStreaming(false)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return (
    <Card className="bg-slate-900 border-slate-700 overflow-hidden h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <CardTitle className="text-lg">Live Video Feed</CardTitle>
        <div className="flex items-center gap-2">
          {isStreaming && (
            <>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <Badge variant="outline" className="text-xs">LIVE</Badge>
            </>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="relative aspect-video bg-slate-950 flex items-center justify-center">
          <img
            src="/api/video/stream"
            alt="Live video feed"
            className="w-full h-full object-cover"
            onError={() => setIsStreaming(false)}
          />
          
          {!isStreaming && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
              <div className="text-center">
                <p className="text-slate-400 mb-2">Video Feed Unavailable</p>
                <p className="text-xs text-slate-500">Ensure backend is running on port 8000</p>
              </div>
            </div>
          )}

          <div className="absolute bottom-4 right-4 bg-slate-900/80 backdrop-blur px-3 py-1 rounded border border-slate-700">
            <span className="text-xs text-slate-300">{fps} FPS</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
