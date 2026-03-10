'use client'

import { CheckCircle2, AlertCircle, Clock } from 'lucide-react'

interface SystemStatusProps {
  status: {
    status: string
    fps: number
    last_detection: string | null
  }
}

export function SystemStatus({ status }: SystemStatusProps) {
  const isOnline = status.status === 'ready'

  return (
    <div className="flex items-center gap-6">
      {/* Status */}
      <div className="flex items-center gap-2">
        {isOnline ? (
          <>
            <CheckCircle2 className="w-5 h-5 text-green-500" />
            <div className="text-sm">
              <p className="text-slate-400">System Status</p>
              <p className="font-semibold text-green-500">Online</p>
            </div>
          </>
        ) : (
          <>
            <AlertCircle className="w-5 h-5 text-yellow-500" />
            <div className="text-sm">
              <p className="text-slate-400">System Status</p>
              <p className="font-semibold text-yellow-500">
                {status.status === 'loading' ? 'Loading...' : 'Offline'}
              </p>
            </div>
          </>
        )}
      </div>

      {/* FPS */}
      <div className="border-l border-slate-700 pl-6">
        <div className="text-sm">
          <p className="text-slate-400">Performance</p>
          <p className="font-semibold text-slate-50">{status.fps.toFixed(1)} FPS</p>
        </div>
      </div>

      {/* Last Detection */}
      <div className="border-l border-slate-700 pl-6">
        <div className="text-sm">
          <p className="text-slate-400">Last Detection</p>
          <p className="font-semibold text-slate-50 flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {status.last_detection ? 'Recently' : 'Never'}
          </p>
        </div>
      </div>
    </div>
  )
}
