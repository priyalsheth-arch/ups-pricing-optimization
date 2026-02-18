import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadCsv, confirmUpload, getUploadHistory } from '../api/uploads'
import { getStores } from '../api/stores'
import { useAuthStore } from '../store/authStore'
import { Upload, CheckCircle, AlertCircle, FileText } from 'lucide-react'
import type { UploadPreviewRow, ValidationReport } from '../types'

export default function UploadPage() {
  const qc = useQueryClient()
  const authStoreId = useAuthStore((s) => s.store_id)
  const isManager = useAuthStore((s) => s.isManager())

  const [storeId, setStoreId] = useState<number | null>(authStoreId)
  const [dragOver, setDragOver] = useState(false)
  const [staged, setStaged] = useState<{
    batchId: number
    preview: UploadPreviewRow[]
    report: ValidationReport
    filename: string
  } | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: stores = [] } = useQuery({ queryKey: ['stores'], queryFn: getStores, enabled: isManager })
  const { data: history = [] } = useQuery({
    queryKey: ['upload-history', storeId],
    queryFn: () => getUploadHistory(storeId ?? undefined),
    enabled: !!storeId,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file, sid }: { file: File; sid: number }) => uploadCsv(file, sid),
    onSuccess: (data) => {
      setStaged({
        batchId: data.batch_id,
        preview: data.preview_rows,
        report: data.validation_report,
        filename: data.batch.filename,
      })
    },
  })

  const confirmMutation = useMutation({
    mutationFn: () => confirmUpload(staged!.batchId),
    onSuccess: () => {
      setConfirmed(true)
      setStaged(null)
      qc.invalidateQueries({ queryKey: ['upload-history'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['gaps'] })
      qc.invalidateQueries({ queryKey: ['upsells'] })
    },
  })

  const handleFile = (file: File) => {
    if (!storeId) { alert('Please select a store first'); return }
    setConfirmed(false)
    uploadMutation.mutate({ file, sid: storeId })
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-xl font-bold">Upload ConnectSuite Data</h1>

      {/* Store selector */}
      {isManager && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Store</label>
          <select
            value={storeId ?? ''}
            onChange={(e) => setStoreId(parseInt(e.target.value))}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white w-full max-w-xs"
          >
            <option value="">Select store...</option>
            {stores.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
      )}

      {/* Success state */}
      {confirmed && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-5 flex items-center gap-3">
          <CheckCircle size={20} className="text-green-600" />
          <div>
            <p className="font-medium text-green-800">Upload complete!</p>
            <p className="text-sm text-green-600">Pricing analysis has been updated. Check the Dashboard for new insights.</p>
          </div>
        </div>
      )}

      {/* Dropzone */}
      {!staged && !uploadMutation.isPending && (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
            dragOver ? 'border-brand-gold bg-brand-gold/5' : 'border-gray-300 hover:border-brand-brown hover:bg-gray-50'
          }`}
        >
          <Upload size={32} className="mx-auto text-gray-400 mb-3" />
          <p className="font-medium text-gray-700">Drop ConnectSuite CSV here</p>
          <p className="text-sm text-gray-400 mt-1">or click to browse</p>
          <p className="text-xs text-gray-300 mt-3">Supported format: ConnectSuite daily/weekly export (.csv)</p>
          <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={(e) => {
            const f = e.target.files?.[0]; if (f) handleFile(f)
          }} />
        </div>
      )}

      {uploadMutation.isPending && (
        <div className="border-2 border-dashed border-brand-gold rounded-xl p-12 text-center">
          <div className="text-brand-brown font-medium">Parsing file...</div>
        </div>
      )}

      {/* Validation report */}
      {staged && (
        <div className="space-y-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-4">
              <FileText size={20} className="text-brand-brown" />
              <div>
                <p className="font-medium">{staged.filename}</p>
                <p className="text-xs text-gray-400">{staged.report.total_rows} total rows • {staged.report.valid_rows} valid • {staged.report.error_rows} skipped</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm mb-4">
              <div className="bg-green-50 rounded-lg p-3">
                <p className="text-green-800 font-medium">✓ Valid rows</p>
                <p className="text-2xl font-bold text-green-700">{staged.report.valid_rows}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-gray-600 font-medium">Date range</p>
                <p className="text-sm font-bold">{staged.report.date_range_start ?? '—'} → {staged.report.date_range_end ?? '—'}</p>
              </div>
            </div>

            {staged.report.warnings.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-3">
                <p className="text-xs font-semibold text-yellow-700 mb-1">Warnings ({staged.report.warnings.length})</p>
                {staged.report.warnings.slice(0, 5).map((w, i) => <p key={i} className="text-xs text-yellow-600">{w}</p>)}
                {staged.report.warnings.length > 5 && <p className="text-xs text-yellow-500">...and {staged.report.warnings.length - 5} more</p>}
              </div>
            )}

            {staged.report.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-3">
                <p className="text-xs font-semibold text-red-700 mb-1">Errors ({staged.report.errors.length} rows skipped)</p>
                {staged.report.errors.slice(0, 5).map((e, i) => <p key={i} className="text-xs text-red-600">{e}</p>)}
              </div>
            )}

            {/* Preview table */}
            <div className="overflow-x-auto border border-gray-100 rounded-lg">
              <table className="w-full text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    {['#', 'Date', 'Category', 'Service Code', 'Description', 'Qty', 'Net Revenue', 'Carrier', 'Level'].map((h) => (
                      <th key={h} className="text-left px-3 py-2 text-gray-500 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {staged.preview.slice(0, 10).map((row) => (
                    <tr key={row.row_number}>
                      <td className="px-3 py-1.5 text-gray-400">{row.row_number}</td>
                      <td className="px-3 py-1.5">{row.transaction_date}</td>
                      <td className="px-3 py-1.5 capitalize">{row.service_category}</td>
                      <td className="px-3 py-1.5 font-mono">{row.service_code}</td>
                      <td className="px-3 py-1.5 max-w-32 truncate">{row.service_description}</td>
                      <td className="px-3 py-1.5">{row.quantity}</td>
                      <td className="px-3 py-1.5 font-medium">${row.net_revenue?.toFixed(2)}</td>
                      <td className="px-3 py-1.5">{row.carrier}</td>
                      <td className="px-3 py-1.5">{row.service_level}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {staged.preview.length > 10 && (
              <p className="text-xs text-gray-400 mt-2">Showing first 10 of {staged.preview.length} preview rows</p>
            )}

            <div className="flex gap-3 mt-5">
              <button
                onClick={() => confirmMutation.mutate()}
                disabled={confirmMutation.isPending}
                className="bg-brand-brown text-white px-6 py-2.5 rounded-lg font-medium text-sm hover:bg-opacity-90 disabled:opacity-60"
              >
                {confirmMutation.isPending ? 'Importing...' : `Confirm Import (${staged.report.valid_rows} rows)`}
              </button>
              <button onClick={() => setStaged(null)} className="border border-gray-300 px-4 py-2.5 rounded-lg text-sm">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload history */}
      {history.length > 0 && (
        <div>
          <h2 className="font-semibold text-sm text-gray-700 mb-3">Upload History</h2>
          <div className="space-y-2">
            {history.map((batch) => (
              <div key={batch.id} className="bg-white border border-gray-200 rounded-lg px-4 py-3 flex items-center justify-between text-sm">
                <div className="flex items-center gap-3">
                  <FileText size={16} className="text-gray-400" />
                  <div>
                    <p className="font-medium">{batch.filename}</p>
                    <p className="text-xs text-gray-400">{batch.date_range_start ?? '—'} → {batch.date_range_end ?? '—'} • {batch.row_count ?? 0} rows</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    batch.status === 'complete' ? 'bg-green-100 text-green-700' :
                    batch.status === 'error' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-500'
                  }`}>{batch.status}</span>
                  <span className="text-xs text-gray-400">{batch.uploaded_at.split('T')[0]}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
