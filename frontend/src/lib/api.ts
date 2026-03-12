const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface Transaction {
  id: string;
  type: 'send' | 'receive' | 'recharge' | 'bill_payment' | 'savings' | 'deposit' | 'withdraw';
  amount: number;
  fee: number;
  status: 'pending' | 'completed' | 'failed';
  recipient_phone?: string;
  recipient_name?: string;
  sender_phone?: string;
  sender_name?: string;
  note?: string;
  category?: string;
  operator?: string;
  provider?: string;
  reference?: string;
  method?: string;
  phone_number?: string;
  created_at: string;
}

export interface Contact {
  id: string;
  name: string;
  phone: string;
  is_favorite: boolean;
  created_at: string;
}

// CORRECTION: Interface simple avec data optionnel
// Cela permet au catch() de page.tsx de fonctionner sans erreur TypeScript
interface ApiResponse {
  success: boolean;
  message?: string;
  data?: T;
}

// Helper function to get auth header
const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

// Transfers API
export const transfersApi = {
  create: async (data: {
    recipient_phone: string;
    amount: number;
    pin: string;
    source: string;
    note?: string;
  }): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/transfers`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return response.json();
    } catch (error) {
      console.error('Transfer error:', error);
      return { success: false, message: 'Erreur lors du transfert' };
    }
  },

  getHistory: async (params?: {
    page?: number;
    page_size?: number;
    tx_type?: string;
  }): Promise<ApiResponse<{ transactions: Transaction[]; total: number }>> => {
    try {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      if (params?.tx_type) searchParams.set('tx_type', params.tx_type);

      const response = await fetch(`${API_URL}/transfers?${searchParams.toString()}`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get history error:', error);
      return { success: false };
    }
  },
};

// Contacts API
export const contactsApi = {
  getAll: async (): Promise<ApiResponse<{ contacts: Contact[] }>> => {
    try {
      const response = await fetch(`${API_URL}/contacts`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get contacts error:', error);
      return { success: false };
    }
  },

  create: async (data: {
    name: string;
    phone: string;
    is_favorite?: boolean;
  }): Promise<ApiResponse<{ contact: Contact }>> => {
    try {
      const response = await fetch(`${API_URL}/contacts`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return response.json();
    } catch (error) {
      console.error('Create contact error:', error);
      return { success: false, message: 'Erreur lors de la création du contact' };
    }
  },

  delete: async (id: string): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/contacts/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Delete contact error:', error);
      return { success: false, message: 'Erreur lors de la suppression' };
    }
  },
};

// Services API
export const servicesApi = {
  recharge: async (data: {
    phone: string;
    amount: number;
    operator: 'orange' | 'mtn' | 'moov' | 'telecel';
    pin?: string;
  }): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/services/recharge`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return response.json();
    } catch (error) {
      console.error('Recharge error:', error);
      return { success: false, message: 'Erreur lors de la recharge' };
    }
  },

  payBill: async (data: {
    category: string;
    provider: string;
    reference: string;
    amount: number;
    pin?: string;
  }): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/services/bills`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return response.json();
    } catch (error) {
      console.error('Bill payment error:', error);
      return { success: false, message: 'Erreur lors du paiement' };
    }
  },
};

// Analytics API
export const analyticsApi = {
  getSummary: async (
    period: 'week' | 'month' | 'year'
  ): Promise<ApiResponse<{
    income: number;
    expenses: number;
    breakdown: Array<{ category: string; amount: number; percentage: number }>;
  }>> => {
    try {
      const response = await fetch(`${API_URL}/analytics?period=${period}`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Analytics error:', error);
      return { success: false };
    }
  },
};

// Wallet API
export const walletApi = {
  getBalance: async (): Promise<ApiResponse<{ balance: number; savings: number; currency: string }>> => {
    try {
      const response = await fetch(`${API_URL}/wallet/balance`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get balance error:', error);
      return { success: false };
    }
  },

  getLimits: async (): Promise<ApiResponse<{
    deposit: { daily_limit: number; daily_used: number; auto_limit: number };
    withdraw: { daily_limit: number; daily_used: number; auto_limit: number };
  }>> => {
    try {
      const response = await fetch(`${API_URL}/wallet/limits`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get limits error:', error);
      return { success: false };
    }
  },

  deposit: async (data: {
    amount: number;
    method: string;
    phone_number: string;
  }): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/wallet/deposit`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return response.json();
    } catch (error) {
      console.error('Deposit error:', error);
      return { success: false, message: 'Erreur lors du dépôt' };
    }
  },

  withdraw: async (data: {
    amount: number;
    method: string;
    phone_number: string;
    pin?: string;
  }): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/wallet/withdraw`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return response.json();
    } catch (error) {
      console.error('Withdraw error:', error);
      return { success: false, message: 'Erreur lors du retrait' };
    }
  },

  getTransactions: async (params?: {
    page?: number;
    page_size?: number;
    transaction_type?: string;
  }): Promise<ApiResponse<{ data: Transaction[]; total: number }>> => {
    try {
      const searchParams = new URLSearchParams();
      if (params?.page) searchParams.set('page', params.page.toString());
      if (params?.page_size) searchParams.set('page_size', params.page_size.toString());
      if (params?.transaction_type) searchParams.set('transaction_type', params.transaction_type);

      const response = await fetch(`${API_URL}/wallet/transactions?${searchParams.toString()}`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get wallet transactions error:', error);
      return { success: false };
    }
  },
};

// Admin API
export const adminApi = {
  getDashboard: async (): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/admin/dashboard`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get dashboard error:', error);
      return { success: false };
    }
  },

  getPendingTransactions: async (params?: {
    urgent_only?: boolean;
    transaction_type?: string;
    page?: number;
  }): Promise<ApiResponse> => {
    try {
      const searchParams = new URLSearchParams();
      if (params?.urgent_only) searchParams.set('urgent_only', 'true');
      if (params?.transaction_type) searchParams.set('transaction_type', params.transaction_type);
      if (params?.page) searchParams.set('page', params.page.toString());

      const response = await fetch(`${API_URL}/admin/transactions/pending?${searchParams.toString()}`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get pending transactions error:', error);
      return { success: false };
    }
  },

  validateTransaction: async (transactionId: string, action: 'approve' | 'reject', notes?: string): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/admin/transactions/${transactionId}/validate?action=${action}`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ notes }),
      });
      return response.json();
    } catch (error) {
      console.error('Validate transaction error:', error);
      return { success: false };
    }
  },

  getUsers: async (params?: { search?: string; page?: number }): Promise<ApiResponse> => {
    try {
      const searchParams = new URLSearchParams();
      if (params?.search) searchParams.set('search', params.search);
      if (params?.page) searchParams.set('page', params.page.toString());

      const response = await fetch(`${API_URL}/admin/users?${searchParams.toString()}`, {
        headers: getAuthHeaders(),
      });
      return response.json();
    } catch (error) {
      console.error('Get users error:', error);
      return { success: false };
    }
  },

  updateUser: async (userId: string, data: {
    is_active?: boolean;
    is_verified?: boolean;
    balance?: number;
  }): Promise<ApiResponse> => {
    try {
      const response = await fetch(`${API_URL}/admin/users/${userId}`, {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(data),
      });
      return response.json();
    } catch (error) {
      console.error('Update user error:', error);
      return { success: false };
    }
  },
};