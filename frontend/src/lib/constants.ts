export const SERVICE_CATEGORIES = [
  { value: 'shipping', label: 'Shipping' },
  { value: 'printing', label: 'Printing & Copying' },
  { value: 'mailbox', label: 'Mailbox Rentals' },
  { value: 'packing', label: 'Packing' },
  { value: 'supplies', label: 'Supplies' },
]

export const COMPETITORS = ['FedEx', 'USPS', 'Staples', 'Office Depot']

export const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-700',
}

export const GAP_DIRECTION_COLORS: Record<string, string> = {
  underpriced: 'bg-red-100 text-red-800',
  overpriced: 'bg-blue-100 text-blue-800',
  competitive: 'bg-green-100 text-green-800',
}

export const CATEGORY_COLORS: Record<string, string> = {
  shipping: '#FFB500',
  printing: '#4B1600',
  mailbox: '#1D4ED8',
  packing: '#059669',
  supplies: '#7C3AED',
}
