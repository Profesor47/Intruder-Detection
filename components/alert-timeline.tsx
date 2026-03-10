'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertCircle, CheckCircle2, Clock } from 'lucide-react'

interface Alert {
  alert_id: string
  detection_id: string
  alert_type: string
  status: string
  created_at: string
}

interface AlertTimelineProps {
  fullPage?: boolean
}

export function AlertTimeline({ fullPage = false }: AlertTimelineProps) {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchAlerts = async () => {
    try {
      const res = await fetch('/api/alerts?limit=10')
      const data = await res.json()
      setAlerts(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    }
  }

  const mockAlerts: Alert[] = [
    {
      alert_id: '1',
      detection_id: 'd1',
      alert_type: 'intruder',
      status: 'active',
      created_at: new Date(Date.now() - 5 * 60000).toISOString()
    },
    {
      alert_id: '2',
      detection_id: 'd2',
      alert_type: 'known_face',
      status: 'resolved',
      created_at: new Date(Date.now() - 30 * 60000).toISOString()
    },
    {
      alert_id: '3',
      detection_id: 'd3',
      alert_type: 'intruder',
      status: 'active',
      created_at: new Date(Date.now() - 2 * 3600000).toISOString()
    }
  ]

  const displayAlerts = alerts.length > 0 ? alerts : mockAlerts

  return (
    <Card className={`bg-slate-900 border-slate-800 ${fullPage ? 'w-full' : ''}`}>
      <CardHeader>
        <CardTitle className="text-white">Recent Alerts</CardTitle>
        <CardDescription>Security events and detections</CardDescription>
      </CardHeader>
      <CardContent>
        <div className={`space-y-3 ${fullPage ? 'max-h-[600px] overflow-y-auto' : 'max-h-[400px] overflow-y-auto'}`}>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-400" />
            </div>
          ) : displayAlerts.length === 0 ? (
            <p className="text-center text-slate-400 py-8">No alerts yet</p>
          ) : (
            displayAlerts.map((alert) => (
              <div key={alert.alert_id} className="flex gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-slate-700 transition-colors">
                <div className="flex-shrink-0 mt-1">
                  {alert.status === 'active' ? (
                    <AlertCircle className="w-5 h-5 text-red-500 animate-pulse" />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium text-slate-50 capitalize">
                        {alert.alert_type.replace('_', ' ')}
                      </p>
                      <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(alert.created_at)}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${
                      alert.status === 'active'
                        ? 'bg-red-500/20 text-red-300'
                        : 'bg-green-500/20 text-green-300'
                    }`}>
                      {alert.status}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function formatTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}
