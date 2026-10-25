import {
  ProfileResponse,
  RecommendationRunResponse,
  ComparisonResponse,
  Product,
} from '../types';

const API_BASE = '/api/v1';

export const api = {
  async parseProfile(message: string, category?: string): Promise<ProfileResponse> {
    const res = await fetch(`${API_BASE}/profile/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, category }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async chatProfile(profileId: string, message: string): Promise<ProfileResponse> {
    const res = await fetch(`${API_BASE}/profile/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_id: profileId, message }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateProfile(profileId: string, updates: Record<string, any>): Promise<ProfileResponse> {
    const res = await fetch(`${API_BASE}/profile/${profileId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async generateRecommendations(profileId: string, category?: string): Promise<RecommendationRunResponse> {
    const res = await fetch(`${API_BASE}/recommendations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_id: profileId, category }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async compareProducts(productIds: string[], profileId?: string): Promise<ComparisonResponse> {
    const res = await fetch(`${API_BASE}/recommendations/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_ids: productIds, profile_id: profileId }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getProducts(params?: { product_type?: string; issuer?: string; search?: string }): Promise<Product[]> {
    const query = new URLSearchParams();
    if (params?.product_type) query.set('product_type', params.product_type);
    if (params?.issuer) query.set('issuer', params.issuer);
    if (params?.search) query.set('search', params.search);
    const res = await fetch(`${API_BASE}/products?${query.toString()}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getProductDetails(productId: string): Promise<Product> {
    const res = await fetch(`${API_BASE}/products/${productId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getIngestionStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/ingestion/status`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async triggerIngestion(): Promise<any> {
    const res = await fetch(`${API_BASE}/ingestion/run?force_fixture=true`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};
