import client from './client'
import type { UploadBatch } from '../types'

export const uploadCsv = async (file: File, store_id: number) => {
  const form = new FormData()
  form.append('file', file)
  form.append('store_id', String(store_id))
  const res = await client.post('/uploads/csv', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export const confirmUpload = async (batchId: number) => {
  const res = await client.post(`/uploads/${batchId}/confirm`)
  return res.data
}

export const getUploadHistory = async (store_id?: number): Promise<UploadBatch[]> => {
  const res = await client.get('/uploads/history', { params: { store_id } })
  return res.data
}
