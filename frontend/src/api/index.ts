import client from './client'
import type {
  Item, Company, ItemCompany, Contract, Transaction,
  ExitPass, MonthlySummary, AnnualRow, ImportPreview, MonthlyTrendItem,
} from '../types'

// ── Items ──────────────────────────────────────────────────────────────────

export const api = {
  // Items
  getItems: (category?: string) =>
    client.get<Item[]>('/items', { params: { category } }).then(r => r.data),
  createItem: (data: Omit<Item, 'id'>) =>
    client.post<Item>('/items', data).then(r => r.data),
  updateItem: (id: number, data: Partial<Omit<Item, 'id'>>) =>
    client.put<Item>(`/items/${id}`, data).then(r => r.data),
  deleteItem: (id: number) =>
    client.delete(`/items/${id}`),

  // Companies
  getCompanies: () =>
    client.get<Company[]>('/companies').then(r => r.data),
  createCompany: (data: { name: string }) =>
    client.post<Company>('/companies', data).then(r => r.data),
  updateCompany: (id: number, data: { name: string }) =>
    client.put<Company>(`/companies/${id}`, data).then(r => r.data),
  deleteCompany: (id: number) =>
    client.delete(`/companies/${id}`),

  // ItemCompanies
  getItemCompanies: (params?: { item_id?: number; company_id?: number }) =>
    client.get<ItemCompany[]>('/item-companies', { params }).then(r => r.data),
  createItemCompany: (data: { item_id: number; company_id: number; sort_order: number }) =>
    client.post<ItemCompany>('/item-companies', data).then(r => r.data),
  updateItemCompany: (id: number, sort_order: number) =>
    client.put<ItemCompany>(`/item-companies/${id}`, { sort_order }).then(r => r.data),
  deleteItemCompany: (id: number) =>
    client.delete(`/item-companies/${id}`),

  // Contracts
  getContracts: (params?: { item_id?: number; company_id?: number }) =>
    client.get<Contract[]>('/contracts', { params }).then(r => r.data),
  getActiveContract: (item_id: number, company_id: number, on_date?: string) =>
    client.get<Contract | null>('/contracts/active', { params: { item_id, company_id, on_date } }).then(r => r.data),
  createContract: (data: Omit<Contract, 'id' | 'item' | 'company'>) =>
    client.post<Contract>('/contracts', data).then(r => r.data),
  updateContract: (id: number, data: Partial<Omit<Contract, 'id' | 'item' | 'company'>>) =>
    client.put<Contract>(`/contracts/${id}`, data).then(r => r.data),
  deleteContract: (id: number) =>
    client.delete(`/contracts/${id}`),

  // Transactions
  getTransactions: (params?: {
    start?: string; end?: string; company_id?: number;
    item_id?: number; page?: number; size?: number
  }) =>
    client.get<Transaction[]>('/transactions', { params }).then(r => r.data),
  getGroupedTransactions: (params?: { start?: string; end?: string }) =>
    client.get<any[]>('/transactions/grouped', { params }).then(r => r.data),
  createTransaction: (data: Omit<Transaction, 'id' | 'item' | 'company'>) =>
    client.post<Transaction>('/transactions', data).then(r => r.data),
  batchCreateTransactions: (transactions: Omit<Transaction, 'id' | 'item' | 'company'>[]) =>
    client.post<Transaction[]>('/transactions/batch', { transactions }).then(r => r.data),
  updateTransaction: (id: number, data: Partial<Omit<Transaction, 'id' | 'item' | 'company'>>) =>
    client.put<Transaction>(`/transactions/${id}`, data).then(r => r.data),
  deleteTransaction: (id: number) =>
    client.delete(`/transactions/${id}`),
  importPreview: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post<ImportPreview>('/transactions/import/preview', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  importConfirm: (rows: Omit<Transaction, 'id' | 'item' | 'company'>[]) =>
    client.post<Transaction[]>('/transactions/import/confirm', rows).then(r => r.data),

  // Reports
  getMonthlyReport: (year: number, month: number) =>
    client.get<MonthlySummary>('/reports/monthly', { params: { year, month } }).then(r => r.data),
  downloadMonthlyReport: (year: number, month: number) =>
    client.get('/reports/monthly/excel', { params: { year, month }, responseType: 'blob' }).then(r => r.data as Blob),
  getMonthlyTrend: (year: number) =>
    client.get<MonthlyTrendItem[]>('/reports/monthly-trend', { params: { year } }).then(r => r.data),
  getAnnualReport: (params: { year: number; company_id?: number; item_id?: number }) =>
    client.get<AnnualRow[]>('/reports/annual', { params }).then(r => r.data),

  // Exit Passes
  getExitPasses: (params?: { company_id?: number; start?: string; end?: string }) =>
    client.get<ExitPass[]>('/exit-passes', { params }).then(r => r.data),
  getExitPass: (id: number) =>
    client.get<ExitPass>(`/exit-passes/${id}`).then(r => r.data),
  createExitPass: (data: { date: string; company_id: number; transaction_ids: number[] }) =>
    client.post<ExitPass>('/exit-passes', data).then(r => r.data),
  uploadExitPassPhoto: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post(`/exit-passes/${id}/photo`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data)
  },
  downloadExitPass: (id: number) =>
    client.get(`/exit-passes/${id}/download`, { responseType: 'blob' }).then(r => r.data),
  deleteExitPass: (id: number) =>
    client.delete(`/exit-passes/${id}`),
}
