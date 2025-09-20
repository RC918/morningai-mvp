/**
 * Dashboard 組件測試
 */

import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import Dashboard from '../Dashboard'
import { AuthProvider } from '../../contexts/AuthContext'

// Mock useAuth hook
const mockUser = {
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  role: 'user'
}

const mockAuthContext = {
  user: mockUser,
  loading: false,
  error: null,
  logout: vi.fn()
}

vi.mock('../../hooks/useAuth', () => ({
  useAuth: () => mockAuthContext
}))

// Mock API calls
vi.mock('../../lib/api', () => ({
  api: {
    get: vi.fn()
  }
}))

const DashboardWrapper = ({ children }) => (
  <BrowserRouter>
    <AuthProvider>
      {children}
    </AuthProvider>
  </BrowserRouter>
)

describe('Dashboard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders dashboard correctly for authenticated user', () => {
    render(
      <DashboardWrapper>
        <Dashboard />
      </DashboardWrapper>
    )

    expect(screen.getByText(/welcome/i)).toBeInTheDocument()
    expect(screen.getByText(mockUser.username)).toBeInTheDocument()
  })

  it('displays user statistics', async () => {
    const mockStats = {
      totalUsers: 150,
      activeUsers: 120,
      totalTenants: 25,
      activeTenants: 20
    }

    const { api } = await import('../../lib/api')
    api.get.mockResolvedValue({ data: mockStats })

    render(
      <DashboardWrapper>
        <Dashboard />
      </DashboardWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument()
      expect(screen.getByText('120')).toBeInTheDocument()
      expect(screen.getByText('25')).toBeInTheDocument()
      expect(screen.getByText('20')).toBeInTheDocument()
    })
  })

  it('handles API error gracefully', async () => {
    const { api } = await import('../../lib/api')
    api.get.mockRejectedValue(new Error('API Error'))

    render(
      <DashboardWrapper>
        <Dashboard />
      </DashboardWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText(/error loading data/i)).toBeInTheDocument()
    })
  })

  it('shows loading state initially', () => {
    mockAuthContext.loading = true

    render(
      <DashboardWrapper>
        <Dashboard />
      </DashboardWrapper>
    )

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('displays admin-specific content for admin users', () => {
    mockAuthContext.user = { ...mockUser, role: 'admin' }

    render(
      <DashboardWrapper>
        <Dashboard />
      </DashboardWrapper>
    )

    expect(screen.getByText(/admin panel/i)).toBeInTheDocument()
    expect(screen.getByText(/user management/i)).toBeInTheDocument()
  })
})
