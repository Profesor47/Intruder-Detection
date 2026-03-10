'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Square } from 'lucide-react'

export function MotorControl() {
  const [autoTrack, setAutoTrack] = useState(false)
  const [motorSpeed, setMotorSpeed] = useState(128)

  const handleMove = async (direction: string) => {
    try {
      await fetch(`/api/motor/move?direction=${direction}&speed=${motorSpeed}`, {
        method: 'POST'
      })
    } catch (error) {
      console.error('Motor control error:', error)
    }
  }

  const handleAutoTrack = async (enabled: boolean) => {
    try {
      await fetch(`/api/motor/auto-track?enabled=${enabled}`, {
        method: 'POST'
      })
      setAutoTrack(enabled)
    } catch (error) {
      console.error('Auto-track error:', error)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Manual Control */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Manual Control</CardTitle>
          <CardDescription>Control camera position and movement</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* D-Pad */}
          <div className="flex flex-col items-center gap-4">
            <div className="grid grid-cols-3 gap-2 w-48 h-48">
              {/* Empty top-left */}
              <div />
              {/* Up */}
              <Button
                onClick={() => handleMove('up')}
                size="lg"
                className="bg-slate-700 hover:bg-blue-600 text-white rounded-full"
              >
                <ChevronUp className="w-6 h-6" />
              </Button>
              {/* Empty top-right */}
              <div />

              {/* Left */}
              <Button
                onClick={() => handleMove('left')}
                size="lg"
                className="bg-slate-700 hover:bg-blue-600 text-white rounded-full"
              >
                <ChevronLeft className="w-6 h-6" />
              </Button>
              {/* Center - Stop */}
              <Button
                onClick={() => handleMove('stop')}
                size="lg"
                className="bg-red-600 hover:bg-red-700 text-white rounded-full"
              >
                <Square className="w-6 h-6 fill-current" />
              </Button>
              {/* Right */}
              <Button
                onClick={() => handleMove('right')}
                size="lg"
                className="bg-slate-700 hover:bg-blue-600 text-white rounded-full"
              >
                <ChevronRight className="w-6 h-6" />
              </Button>

              {/* Empty bottom-left */}
              <div />
              {/* Down */}
              <Button
                onClick={() => handleMove('down')}
                size="lg"
                className="bg-slate-700 hover:bg-blue-600 text-white rounded-full"
              >
                <ChevronDown className="w-6 h-6" />
              </Button>
              {/* Empty bottom-right */}
              <div />
            </div>
          </div>

          {/* Speed Control */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Speed</label>
            <input
              type="range"
              min="0"
              max="255"
              value={motorSpeed}
              onChange={(e) => setMotorSpeed(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-slate-400">
              <span>Slow</span>
              <span className="font-semibold text-slate-300">{motorSpeed}</span>
              <span>Fast</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Auto-Tracking */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Auto-Tracking</CardTitle>
          <CardDescription>Automatic intruder following system</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className={`p-6 rounded-lg border-2 transition-all ${
            autoTrack
              ? 'bg-green-500/10 border-green-500/50'
              : 'bg-slate-800/50 border-slate-700'
          }`}>
            <div className="text-center space-y-2">
              <p className="text-sm text-slate-400">Automatic Tracking Status</p>
              <p className={`text-2xl font-bold ${autoTrack ? 'text-green-400' : 'text-slate-400'}`}>
                {autoTrack ? 'ENABLED' : 'DISABLED'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={() => handleAutoTrack(true)}
              disabled={autoTrack}
              className={`${
                autoTrack
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-700 hover:bg-green-600 text-slate-300'
              }`}
            >
              Enable
            </Button>
            <Button
              onClick={() => handleAutoTrack(false)}
              disabled={!autoTrack}
              className={`${
                !autoTrack
                  ? 'bg-slate-700 text-slate-400'
                  : 'bg-red-600 hover:bg-red-700 text-white'
              }`}
            >
              Disable
            </Button>
          </div>

          <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <h4 className="text-sm font-semibold text-slate-300 mb-2">How it works:</h4>
            <ul className="text-xs text-slate-400 space-y-1">
              <li>• System detects unknown faces</li>
              <li>• Motors automatically pan/tilt to track</li>
              <li>• Keeps intruder centered in frame</li>
              <li>• Smooth movement for better video</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
