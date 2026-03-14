'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { AlertCircle, Camera, CheckCircle2, User } from 'lucide-react'



export function FaceEnrollment() {
  const [step, setStep] = useState<'form' | 'preview' | 'complete'>('form')
  const [name, setName] = useState('')
  const [enrollmentId, setEnrollmentId] = useState('')
  const [samples, setSamples] = useState(0)
  const [isCapturing, setIsCapturing] = useState(false)
  const [capturedImages, setCapturedImages] = useState<string[]>([])

  const handleStartEnrollment = async () => {
    if (!name.trim()) {
      alert('Please enter a name')
      return
    }

    try {
      const res = await fetch(`/api/enrollment/start?person_name=${encodeURIComponent(name)}`, {
        method: 'POST'
      })
      const data = await res.json()
      setEnrollmentId(data.enrollment_id)
      setStep('preview')
      setSamples(0)
      setCapturedImages([])
    } catch (error) {
      console.error('Enrollment start error:', error)
      alert('Failed to start enrollment. Ensure backend is running on port 8000')
    }
  }

  const handleCaptureSample = async () => {
    setIsCapturing(true)
    try {
      const res = await fetch(`/api/enrollment/capture?enrollment_id=${encodeURIComponent(enrollmentId)}`, { method: 'POST' })
      const data = await res.json()
      if (data.status === 'captured') {
        setSamples(data.images_collected)
        // Take a snapshot from the stream to show as thumbnail
        const snapshotUrl = `/api/video/snapshot?t=${Date.now()}`
        setCapturedImages(prev => [...prev, snapshotUrl])
      } else if (data.status === 'no_face') {
        alert('No face detected. Please position yourself in front of the camera.')
      }
    } catch (error) {
      console.error('Sample capture error:', error)
      alert('Failed to capture sample')
    } finally {
      setIsCapturing(false)
    }
  }

  const handleCompleteEnrollment = async () => {
    try {
      const res = await fetch(`/api/enrollment/complete?enrollment_id=${encodeURIComponent(enrollmentId)}`, { method: 'POST' })
      const data = await res.json()
      setStep('complete')
      setTimeout(() => {
        setName('')
        setSamples(0)
        setCapturedImages([])
        setStep('form')
      }, 3000)
    } catch (error) {
      console.error('Enrollment complete error:', error)
      alert('Failed to complete enrollment')
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Input Form */}
      <Card className="lg:col-span-1 bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">New Enrollment</CardTitle>
          <CardDescription>Register authorized person</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {step === 'form' && (
            <>
              <div className="space-y-2">
                <label htmlFor="name" className="text-sm font-medium text-slate-300">
                  Person Name
                </label>
                <Input
                  id="name"
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                  onKeyPress={(e) => e.key === 'Enter' && handleStartEnrollment()}
                />
              </div>

              <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-xs text-blue-300 flex gap-2">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>You will need to capture 5-10 samples from different angles for best accuracy.</span>
                </p>
              </div>

              <Button
                onClick={handleStartEnrollment}
                disabled={!name.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              >
                <User className="w-4 h-4 mr-2" />
                Start Enrollment
              </Button>
            </>
          )}

          {step === 'preview' && (
            <>
              <div className="space-y-2">
                <p className="text-sm font-medium text-slate-300">Enrolled Person</p>
                <p className="text-lg font-semibold text-slate-50">{name}</p>
              </div>

              <div className="p-3 bg-slate-800 rounded-lg border border-slate-700">
                <p className="text-xs text-slate-400">Samples Collected</p>
                <p className="text-2xl font-bold text-blue-400 mt-1">{samples}/5</p>
              </div>

              <Button
                onClick={handleCaptureSample}
                disabled={isCapturing}
                className="w-full bg-green-600 hover:bg-green-700 text-white"
              >
                <Camera className="w-4 h-4 mr-2" />
                {isCapturing ? 'Capturing...' : 'Capture Sample'}
              </Button>

              <Button
                onClick={handleCompleteEnrollment}
                disabled={samples < 5}
                className="w-full bg-slate-700 hover:bg-slate-600 text-white disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Complete Enrollment
              </Button>

              <Button
                onClick={() => {
                  setStep('form')
                  setName('')
                  setSamples(0)
                  setEnrollmentId('')
                  setCapturedImages([])
                }}
                variant="outline"
                className="w-full border-slate-700 text-slate-300 hover:bg-slate-800"
              >
                Cancel
              </Button>
            </>
          )}

          {step === 'complete' && (
            <div className="text-center space-y-3 py-4">
              <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto" />
              <div>
                <p className="font-semibold text-slate-50">Enrollment Successful!</p>
                <p className="text-sm text-slate-400 mt-1">{name} has been added to known faces.</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Live Preview */}
      <Card className="lg:col-span-2 bg-slate-900 border-slate-800">
        <CardHeader>
          <CardTitle className="text-white">Live Preview</CardTitle>
          <CardDescription>Real-time face detection during enrollment</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative w-full bg-slate-950 aspect-video rounded-lg border border-slate-800 overflow-hidden">
            {step === 'preview' ? (
              /* Live MJPEG stream — same feed as Monitoring tab */
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={`/api/video/stream`}
                alt="Live camera feed"
                className="w-full h-full object-cover"
                onError={(e) => {
                  const target = e.currentTarget
                  target.style.display = 'none'
                  target.nextElementSibling?.removeAttribute('hidden')
                }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center w-full h-full gap-2 text-slate-400">
                <div className="animate-pulse w-16 h-16 bg-slate-700 rounded-full" />
                <p className="text-sm">Start enrollment to see live feed</p>
              </div>
            )}
            {/* Fallback shown if stream fails */}
            <div hidden className="flex flex-col items-center justify-center w-full h-full gap-2 text-slate-400 absolute inset-0">
              <Camera className="w-10 h-10 opacity-40" />
              <p className="text-sm">Stream unavailable — check backend</p>
            </div>
            <div className="absolute top-4 right-4 px-3 py-2 bg-slate-900/80 rounded-lg border border-slate-700">
              <span className="text-xs text-slate-300">
                {step === 'preview' ? '🔴 Live' : 'Face detection: Ready'}
              </span>
            </div>
          </div>

          {/* Captured image thumbnails */}
          <div className="mt-4 grid grid-cols-5 gap-2">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={`aspect-square rounded-lg border-2 overflow-hidden ${
                  i < capturedImages.length
                    ? 'border-green-500'
                    : 'border-slate-700 bg-slate-800/50'
                }`}
              >
                {capturedImages[i] ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={capturedImages[i]}
                    alt={`Capture ${i + 1}`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-600 text-xs">
                    {i + 1}
                  </div>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {capturedImages.length > 0
              ? `${capturedImages.length} of 5 samples captured`
              : 'Capture samples from different angles for best accuracy'}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
