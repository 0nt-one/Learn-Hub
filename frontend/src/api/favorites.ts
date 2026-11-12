import { request } from './client'
import type { Page } from '../types/api'
import type { Resource } from '../types/resource'
export interface Favorite { id: number; resource_id: number; created_at: string }
export interface FavoriteItem extends Favorite { resource: Resource | null }
export function listFavorites(page = 1, pageSize = 20) {
  return request<Page<FavoriteItem>>(`/users/me/favorites?page=${page}&page_size=${pageSize}`)
}
export function addFavorite(id: number) { return request<Favorite>(`/users/me/favorites/${id}`, { method: 'PUT' }) }
export function removeFavorite(id: number) { return request<{ resource_id: number; favorited: false }>(`/users/me/favorites/${id}`, { method: 'DELETE' }) }
