import client from './client'
import type { OurPrice, CompetitorPrice } from '../types'

export const getOurPrices = async (store_id?: number, category?: string): Promise<OurPrice[]> => {
  const res = await client.get('/pricing/our', { params: { store_id, category } })
  return res.data
}

export const upsertOurPrice = async (data: Partial<OurPrice>) => {
  const res = await client.post('/pricing/our', data)
  return res.data
}

export const getCompetitorPrices = async (category?: string, competitor?: string): Promise<CompetitorPrice[]> => {
  const res = await client.get('/pricing/competitors', { params: { category, competitor } })
  return res.data
}

export const upsertCompetitorPrice = async (data: Partial<CompetitorPrice>) => {
  const res = await client.post('/pricing/competitors', data)
  return res.data
}

export const deleteCompetitorPrice = async (id: number) => {
  const res = await client.delete(`/pricing/competitors/${id}`)
  return res.data
}
