import client from './client'
import type { Store } from '../types'

export const getStores = async (): Promise<Store[]> => {
  const res = await client.get('/stores')
  return res.data
}
