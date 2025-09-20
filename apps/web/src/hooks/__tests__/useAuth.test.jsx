/**
 * useAuth Hook 測試
 */

import { renderHook, act, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { useAuth } from '../useAuth'
import { AuthProvider } from '../../contexts/AuthContext'

// Mock API
const mockApi = {
  post: vi.fn(),
  get: vi.fn(),
  delete: vi.fn()
}

vi.mock('../../lib/api', () => ({
  api: mockApi
}))

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage
})

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>

describe('useAuth Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.getItem.mockReturnValue(null)
  })

  it('initializes with no user when no token in localStorage', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.user).toBeNull()
    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('loads user from localStorage token on initialization', async () => {
    const mockToken = 'mock-jwt-token'
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com'
    }

    mockLocalStorage.getItem.mockReturnValue(mockToken)
    mockApi.get.mockResolvedValue({ data: mockUser })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
      expect(result.current.loading).toBe(false)
    })

    expect(mockApi.get).toHaveBeenCalledWith('/profile')
  })

  it('handles login successfully', async () => {
    const mockCredentials = {
      email: 'test@example.com',
      password: 'password123'
    }

    const mockResponse = {
      access_token: 'new-token',
      user: {
        id: '1',
        username: 'testuser',
        email: 'test@example.com'
      }
    }

    mockApi.post.mockResolvedValue({ data: mockResponse })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      await result.current.login(mockCredentials)
    })

    expect(mockApi.post).toHaveBeenCalledWith('/login', mockCredentials)
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith('token', 'new-token')
    expect(result.current.user).toEqual(mockResponse.user)
  })

  it('handles login failure', async () => {
    const mockCredentials = {
      email: 'test@example.com',
      password: 'wrongpassword'
    }

    const mockError = new Error('Invalid credentials')
    mockApi.post.mockRejectedValue(mockError)

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      try {
        await result.current.login(mockCredentials)
      } catch (error) {
        // Expected to throw
      }
    })

    expect(result.current.user).toBeNull()
    expect(result.current.error).toBe('Invalid credentials')
  })

  it('handles logout successfully', async () => {
    // Setup initial logged-in state
    const mockToken = 'mock-jwt-token'
    const mockUser = {
      id: '1',
      username: 'testuser',
      email: 'test@example.com'
    }

    mockLocalStorage.getItem.mockReturnValue(mockToken)
    mockApi.get.mockResolvedValue({ data: mockUser })
    mockApi.delete.mockResolvedValue({})

    const { result } = renderHook(() => useAuth(), { wrapper })

    // Wait for initial load
    await waitFor(() => {
      expect(result.current.user).toEqual(mockUser)
    })

    // Perform logout
    await act(async () => {
      await result.current.logout()
    })

    expect(mockApi.delete).toHaveBeenCalledWith('/auth/logout')
    expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token')
    expect(result.current.user).toBeNull()
  })

  it('handles register successfully', async () => {
    const mockUserData = {
      username: 'newuser',
      email: 'new@example.com',
      password: 'password123'
    }

    const mockResponse = {
      message: 'User created successfully',
      user: {
        id: '2',
        username: 'newuser',
        email: 'new@example.com'
      }
    }

    mockApi.post.mockResolvedValue({ data: mockResponse })

    const { result } = renderHook(() => useAuth(), { wrapper })

    let registerResult
    await act(async () => {
      registerResult = await result.current.register(mockUserData)
    })

    expect(mockApi.post).toHaveBeenCalledWith('/register', mockUserData)
    expect(registerResult).toEqual(mockResponse)
  })

  it('handles register failure', async () => {
    const mockUserData = {
      username: 'existinguser',
      email: 'existing@example.com',
      password: 'password123'
    }

    const mockError = new Error('Email already exists')
    mockApi.post.mockRejectedValue(mockError)

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      try {
        await result.current.register(mockUserData)
      } catch (error) {
        // Expected to throw
      }
    })

    expect(result.current.error).toBe('Email already exists')
  })

  it('clears error when clearError is called', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })

    // Set an error first
    act(() => {
      result.current.setError('Test error')
    })

    expect(result.current.error).toBe('Test error')

    // Clear the error
    act(() => {
      result.current.clearError()
    })

    expect(result.current.error).toBeNull()
  })

  it('handles token expiration gracefully', async () => {
    const mockToken = 'expired-token'
    mockLocalStorage.getItem.mockReturnValue(mockToken)
    
    const mockError = new Error('Token expired')
    mockError.response = { status: 401 }
    mockApi.get.mockRejectedValue(mockError)

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.user).toBeNull()
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token')
    })
  })
})
