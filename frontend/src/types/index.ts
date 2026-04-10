export type Category = '부산물' | '폐기물'
export type UnitType = 'per_unit' | 'fixed'

export interface Item {
  id: number
  name: string
  report_name: string | null
  unit: string
  spec: string | null
  category: Category
}

export interface Company {
  id: number
  name: string
}

export interface ItemCompany {
  id: number
  item_id: number
  company_id: number
  sort_order: number
  item: Item
  company: Company
}

export interface Contract {
  id: number
  item_id: number
  company_id: number
  unit_price: number
  unit_type: UnitType
  effective_date: string
  note: string | null
  item: Item
  company: Company
}

export interface Transaction {
  id: number
  date: string
  item_id: number
  company_id: number
  quantity: number
  unit_price: number
  total_amount: number
  vehicle_count: number | null
  note: string | null
  ledger_number: number | null
  item: Item
  company: Company
}

export interface ExitPassTransaction {
  id: number
  exit_pass_id: number
  transaction_id: number
  transaction: Transaction
}

export interface ExitPass {
  id: number
  number: number
  date: string
  company_id: number
  photo_path: string | null
  created_at: string
  company: Company
  transactions: ExitPassTransaction[]
}

export interface ReportRow {
  company_name: string
  item_name: string
  unit_price: number
  current_quantity: number
  current_amount: number
  prev_amount: number
  note: string | null
}

export interface MonthlySummary {
  year: number
  month: number
  byproducts: ReportRow[]
  wastes: ReportRow[]
  total_current_byproduct: number
  total_prev_byproduct: number
  total_current_waste: number
  total_prev_waste: number
}

export interface AnnualRow {
  date: string
  item_name: string
  company_name: string
  quantity: number
  unit_price: number
  total_amount: number
  note: string | null
}

export interface ImportPreviewRow {
  date: string
  item_name: string
  company_name: string
  quantity: number
  unit_price: number
  total_amount: number
  note: string | null
  is_duplicate: boolean
}

export interface MonthlyTrendItem {
  month: number
  byproduct: number
  waste: number
}

export interface ImportPreview {
  new_count: number
  duplicate_count: number
  unknown_items: string[]
  rows: ImportPreviewRow[]
}
