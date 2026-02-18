import client from './client'
import type { PricingGap, UpsellOpportunity, RevenueOpportunityReport, DashboardSummary, MultiStoreComparison } from '../types'

export const getPricingGaps = async (params?: {
  store_id?: number
  category?: string
  direction?: string
  period_days?: number
}): Promise<PricingGap[]> => {
  const res = await client.get('/analysis/gaps', { params })
  return res.data
}

export const getUpsells = async (params?: {
  store_id?: number
  category?: string
  priority?: string
}): Promise<UpsellOpportunity[]> => {
  const res = await client.get('/analysis/upsells', { params })
  return res.data
}

export const dismissUpsell = async (id: number) => {
  const res = await client.post(`/analysis/upsells/${id}/dismiss`)
  return res.data
}

export const getRevenueOpportunity = async (store_id: number, period_days = 30): Promise<RevenueOpportunityReport> => {
  const res = await client.get('/analysis/revenue-opportunity', { params: { store_id, period_days } })
  return res.data
}

export const runAnalysis = async (store_id: number) => {
  const res = await client.post('/analysis/run', null, { params: { store_id } })
  return res.data
}

export const getDashboard = async (store_id: number, period_days = 30): Promise<DashboardSummary> => {
  const res = await client.get('/dashboard', { params: { store_id, period_days } })
  return res.data
}

export const getMultiStore = async (period_days = 30): Promise<MultiStoreComparison[]> => {
  const res = await client.get('/analysis/multistore', { params: { period_days } })
  return res.data
}
