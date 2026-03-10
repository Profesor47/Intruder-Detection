'use client'

import { useState, useEffect } from 'react'
import { VideoFeed } from '@/components/dashboard/video-feed'
import { SystemStatus } from '@/components/dashboard/system-status'
import { DetectionHistory } from '@/components/dashboard/detection-history'
import { MotorControl } from '@/components/dashboard/motor-control'
import { FaceEnrollment } from '@/components/dashboard/face-enrollment'
import { AlertTimeline } from '@/components/dashboard/alert-timeline'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('monitoring')
  const [systemStatus, setSystemStatus] = useState({
    status: 'loading',
    fps: 0,
    last_detection: null
  })

  useEffect(() => {
    // Poll system status
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/status')
        const data = await res.json()
        setSystemStatus(data)
      } catch (error) {
        console.error('Status fetch error:', error)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <main className="min-h-screen bg-slate-950 text-slate-50">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">GUARDZILLA</h1>
              <p className="text-sm text-slate-400 mt-1">AI-Powered Security System</p>
            </div>
            <SystemStatus status={systemStatus} />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 bg-slate-800">
            <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
            <TabsTrigger value="enrollment">Enrollment</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger>
            <TabsTrigger value="control">Motor Control</TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
          </TabsList>

          {/* Monitoring Tab */}
          <TabsContent value="monitoring" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <VideoFeed />
              </div>
              <div>
                <AlertTimeline />
              </div>
            </div>
          </TabsContent>

          {/* Enrollment Tab */}
          <TabsContent value="enrollment">
            <FaceEnrollment />
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <DetectionHistory />
          </TabsContent>

          {/* Motor Control Tab */}
          <TabsContent value="control">
            <MotorControl />
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts">
            <AlertTimeline fullPage={true} />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}
