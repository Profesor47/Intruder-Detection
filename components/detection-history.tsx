'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'

interface Detection {
  detection_id: string
  person_id?: string
  face_confidence: number
  detection_type: string
  timestamp: string
}

export function DetectionHistory() {
  const [detections, setDetections] = useState<Detection[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDetections()
    const interval = setInterval(fetchDetections, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchDetections = async () => {
    try {
      const res = await fetch('/api/detections?limit=50')
      const data = await res.json()
      setDetections(data.detections || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch detections:', error)
    }
  }

  const mockDetections: Detection[] = [
    {
      detection_id: 'd1',
      person_id: 'p1',
      face_confidence: 0.95,
      detection_type: 'known',
      timestamp: new Date().toISOString()
    },
    {
      detection_id: 'd2',
      face_confidence: 0.72,
      detection_type: 'unknown',
      timestamp: new Date(Date.now() - 60000).toISOString()
    },
    {
      detection_id: 'd3',
      person_id: 'p2',
      face_confidence: 0.88,
      detection_type: 'known',
      timestamp: new Date(Date.now() - 120000).toISOString()
    }
  ]

  const displayDetections = detections.length > 0 ? detections : mockDetections

  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader>
        <CardTitle className="text-white">Detection History</CardTitle>
        <CardDescription>All face detection events</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-400" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700">
                  <TableHead className="text-slate-300">Time</TableHead>
                  <TableHead className="text-slate-300">Type</TableHead>
                  <TableHead className="text-slate-300">Confidence</TableHead>
                  <TableHead className="text-slate-300">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {displayDetections.map((detection) => (
                  <TableRow key={detection.detection_id} className="border-slate-700/50 hover:bg-slate-800/50">
                    <TableCell className="text-slate-200 text-sm">
                      {formatTime(detection.timestamp)}
                    </TableCell>
                    <TableCell>
                      <Badge variant={detection.detection_type === 'known' ? 'default' : 'destructive'}>
                        {detection.detection_type === 'known' ? 'Known Face' : 'Unknown/Intruder'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-200">
                      <div className="flex items-center gap-2">
                        <div className="w-20 h-2 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${
                              detection.face_confidence > 0.8 ? 'bg-green-500' :
                              detection.face_confidence > 0.6 ? 'bg-yellow-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${detection.face_confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-400">
                          {(detection.face_confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className={`text-sm font-medium ${
                        detection.detection_type === 'known'
                          ? 'text-green-400'
                          : 'text-red-400'
                      }`}>
                        {detection.detection_type === 'known' ? 'Authorized' : 'Alert'}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function formatTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
