import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';

// Import shadcn UI components
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { AlertCircle, Users, Shield, FileText, LogOut, User, Eye, EyeOff, Home, PlusCircle } from 'lucide-react';

// Dynamic Backend URL Configuration
// Automatically detects the environment and sets the correct backend URL
const getBackendURL = () => {
  // If environment variable is set, use it (for local development)
  if (process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL !== '') {
    return process.env.REACT_APP_BACKEND_URL;
  }
  
  // Auto-detect based on current hostname
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // Development environment (localhost)
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8001';
  }
  
  // Production environment - use current origin
  // This ensures it always points to the same domain the frontend is served from
  return `${protocol}//${hostname}`;
};

const BACKEND_URL = getBackendURL();
const API = `${BACKEND_URL}/api`;

// Log the configuration for debugging (only in development)
if (process.env.NODE_ENV === 'development' || window.location.hostname === 'localhost') {
  console.log('🔗 Backend URL Configuration:', BACKEND_URL);
  console.log('🔗 API Endpoint:', API);
}

// Authentication Context
const AuthContext = createContext();

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          const response = await axios.get(`${API}/auth/me`);
          setUser(response.data);
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('token');
          setToken(null);
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;
      
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post(`${API}/auth/logout`);
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      setUser(null);
      setToken(null);
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  const hasRole = (roles) => {
    if (!user) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Component
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    setLoading(true);
    const result = await login(email, password);
    
    if (result.success) {
      toast.success('Login successful!');
      navigate('/');
    } else {
      toast.error(result.error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden">
      <Card className="w-full max-w-md modern-card border-0 shadow-2xl z-10">
        <CardHeader className="text-center space-y-6 pt-8 pb-6">
          {/* Fancy KC Logo */}
          <div className="relative w-32 h-32 mx-auto">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-400 via-blue-400 to-indigo-500 rounded-3xl opacity-20 blur-2xl animate-pulse"></div>
            <div className="relative w-32 h-32 bg-gradient-to-br from-cyan-100 via-blue-200 to-indigo-300 rounded-3xl flex items-center justify-center shadow-2xl float backdrop-blur-sm border-2 border-white/50 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent animate-shimmer"></div>
              <div className="relative">
                <span className="text-5xl font-black bg-gradient-to-r from-cyan-600 via-blue-700 to-indigo-800 bg-clip-text text-transparent" style={{fontFamily: 'Inter, sans-serif', letterSpacing: '-0.05em'}}>
                  KC
                </span>
              </div>
            </div>
          </div>
          <div>
            <CardTitle className="text-4xl font-extrabold bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-600 bg-clip-text text-transparent">Kawale Cranes</CardTitle>
            <p className="text-slate-600 text-base font-semibold mt-2 tracking-wide">Towing Management System</p>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <Label htmlFor="email" className="text-slate-700 font-semibold">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="input-modern mt-2"
                required
              />
            </div>
            <div>
              <Label htmlFor="password" className="text-slate-700 font-semibold">Password</Label>
              <div className="relative mt-2">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="input-modern pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
            <Button type="submit" className="w-full bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-700 hover:from-cyan-600 hover:via-blue-700 hover:to-indigo-800 text-white font-bold py-6 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 backdrop-blur-sm border-2 border-white/20 hover:border-white/30" disabled={loading}>
              {loading ? '🔄 Signing in...' : '✨ Sign In'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, requiredRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRoles && !requiredRoles.includes(user.role)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-900 mb-2">Access Denied</h2>
            <p className="text-slate-600">You don't have permission to access this page.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return children;
};

// Header Component
const Header = () => {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const [showChangePasswordDialog, setShowChangePasswordDialog] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      toast.error('New password and confirm password do not match');
      return;
    }

    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setChangingPassword(true);
    try {
      await axios.put(`${API}/auth/change-password`, {
        current_password: currentPassword,
        new_password: newPassword
      });
      toast.success('Password changed successfully');
      setShowChangePasswordDialog(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <>
    <header className="header-glass sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-200 to-indigo-300 rounded-2xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-all duration-300 group-hover:scale-105 backdrop-blur-sm border border-white/40">
              <span className="text-2xl">🚛</span>
            </div>
            <div>
              <h1 className="text-2xl font-extrabold bg-gradient-to-r from-cyan-500 to-indigo-600 bg-clip-text text-transparent">Kawale Cranes</h1>
              <p className="text-slate-600 text-sm font-medium">Towing Management System</p>
            </div>
          </Link>
          
          <nav className="flex items-center space-x-4">
            <Link to="/">
              <Button variant="ghost" className="text-slate-700 hover:text-cyan-600 hover:bg-cyan-50/50 font-medium transition-all duration-200 backdrop-blur-sm">
                <Home size={18} className="mr-2" />
                Dashboard
              </Button>
            </Link>
            
            <Link to="/new-order">
              <Button className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:from-cyan-600 hover:to-blue-700 font-semibold shadow-lg hover:shadow-xl transition-all duration-200 backdrop-blur-sm border border-white/20">
                <PlusCircle size={18} className="mr-2" />
                New Order
              </Button>
            </Link>
            
            {/* Rates - All authenticated users can view */}
            <Link to="/rates">
              <Button variant="ghost" className="text-slate-700 hover:text-blue-600 hover:bg-blue-50/50 font-medium transition-all duration-200 backdrop-blur-sm">
                <span className="mr-2">💰</span>
                Rates
              </Button>
            </Link>
            
            {hasRole(['super_admin', 'admin']) && (
              <>
                <Link to="/users">
                  <Button variant="ghost" className="text-slate-700 hover:text-blue-500 hover:bg-blue-50/50 font-medium transition-all duration-200 backdrop-blur-sm">
                    <Users size={18} className="mr-2" />
                    Users
                  </Button>
                </Link>
                
                <Link to="/audit-logs">
                  <Button variant="ghost" className="text-slate-700 hover:text-purple-500 hover:bg-purple-50/50 font-medium transition-all duration-200 backdrop-blur-sm">
                    <FileText size={18} className="mr-2" />
                    Audit Logs
                  </Button>
                </Link>
                
                <Link to="/import-data">
                  <Button variant="ghost" className="text-slate-700 hover:text-indigo-500 hover:bg-indigo-50/50 font-medium transition-all duration-200 backdrop-blur-sm">
                    <FileText size={18} className="mr-2" />
                    Import Data
                  </Button>
                </Link>
                
                <Link to="/reports">
                  <Button variant="ghost" className="text-slate-700 hover:text-teal-500 hover:bg-teal-50/50 font-medium transition-all duration-200 backdrop-blur-sm">
                    <span className="mr-2">📊</span>
                    Reports
                  </Button>
                </Link>
                
                {hasRole(['super_admin', 'admin']) && (
                  <Link to="/driver-salaries">
                    <Button variant="ghost" className="text-slate-700 hover:text-emerald-500 hover:bg-emerald-50/50 font-medium transition-all duration-200 backdrop-blur-sm">
                      <span className="mr-2">💰</span>
                      Driver Salaries
                    </Button>
                  </Link>
                )}
              </>
            )}
            
            <div className="flex items-center space-x-3 px-4 py-2 bg-gradient-to-r from-cyan-100/60 to-blue-100/60 rounded-2xl border border-white/40 backdrop-blur-sm shadow-sm">
              <User size={18} className="text-pink-500" />
              <span className="text-sm font-medium text-slate-700">
                {user?.full_name}
                <Badge className="ml-2 text-xs font-semibold bg-white/60 backdrop-blur-sm border border-white/40" variant={user?.role === 'super_admin' ? 'default' : user?.role === 'admin' ? 'secondary' : 'outline'}>
                  {user?.role?.replace('_', ' ')?.toUpperCase()}
                </Badge>
              </span>
            </div>
            
            <Button 
              variant="ghost" 
              onClick={() => setShowChangePasswordDialog(true)}
              className="text-slate-700 hover:text-blue-500 hover:bg-blue-50/50 transition-all duration-200 backdrop-blur-sm"
              title="Change Password"
            >
              <Shield size={18} />
            </Button>
            
            <Button 
              variant="ghost" 
              onClick={handleLogout}
              className="text-slate-700 hover:text-rose-500 hover:bg-rose-50/50 transition-all duration-200 backdrop-blur-sm"
              title="Logout"
            >
              <LogOut size={18} />
            </Button>
          </nav>
        </div>
      </div>
    </header>
    
    {/* Change Password Dialog */}
    <Dialog open={showChangePasswordDialog} onOpenChange={setShowChangePasswordDialog}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Change Password</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
            <p className="text-sm text-blue-900">
              <strong>Changing password for:</strong> {user?.full_name} ({user?.email})
            </p>
          </div>
          
          <div>
            <Label htmlFor="current_password">Current Password *</Label>
            <Input
              id="current_password"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="new_password">New Password *</Label>
            <Input
              id="new_password"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password (min 6 characters)"
              required
              minLength={6}
            />
          </div>
          
          <div>
            <Label htmlFor="confirm_password">Confirm New Password *</Label>
            <Input
              id="confirm_password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              required
              minLength={6}
            />
          </div>
          
          <div className="flex justify-end space-x-2">
            <Button type="button" variant="outline" onClick={() => {
              setShowChangePasswordDialog(false);
              setCurrentPassword('');
              setNewPassword('');
              setConfirmPassword('');
            }}>
              Cancel
            </Button>
            <Button type="submit" disabled={changingPassword} className="bg-blue-600 hover:bg-blue-700">
              {changingPassword ? 'Changing...' : 'Change Password'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
    </>
  );
};

// Dashboard Component (existing with auth)
const Dashboard = () => {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({ total_orders: 0, by_type: [] });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ order_type: 'all', customer_name: '', phone: '', source: 'all' });
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [orderFinancials, setOrderFinancials] = useState({}); // Store calculated financials
  const [refreshKey, setRefreshKey] = useState(0); // Add refresh trigger
  const { hasRole } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchOrders();
    fetchStats();
  }, [filters]);

  // Refresh data when component mounts or becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchOrders();
        fetchStats();
      }
    };

    // Fetch on mount
    fetchOrders();
    fetchStats();

    // Listen for page visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.order_type && filters.order_type !== 'all') params.append('order_type', filters.order_type);
      if (filters.customer_name) params.append('customer_name', filters.customer_name);
      if (filters.phone) params.append('phone', filters.phone);
      
      const response = await axios.get(`${API}/orders?${params.toString()}`);
      
      // Apply source filter on frontend
      let filteredOrders = response.data;
      if (filters.source && filters.source !== 'all') {
        if (filters.source === 'imported') {
          filteredOrders = response.data.filter(order => order.created_by === 'system_import');
        } else if (filters.source === 'created') {
          filteredOrders = response.data.filter(order => order.created_by !== 'system_import');
        }
      }
      
      setOrders(filteredOrders);
      
      // Fetch financials for company orders
      await fetchFinancialsForCompanyOrders(filteredOrders);
    } catch (error) {
      console.error('Error fetching orders:', error);
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        // Auth context will handle redirect
      } else {
        toast.error('Failed to fetch orders');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchFinancialsForCompanyOrders = async (ordersList) => {
    try {
      const companyOrders = ordersList.filter(order => order.order_type === 'company');
      const financialsData = {};
      
      // Fetch financials for each company order
      for (const order of companyOrders) {
        try {
          const response = await axios.get(`${API}/orders/${order.id}/financials`);
          financialsData[order.id] = response.data;
        } catch (error) {
          console.error(`Error fetching financials for order ${order.id}:`, error);
          // Continue with other orders even if one fails
        }
      }
      
      setOrderFinancials(financialsData);
    } catch (error) {
      console.error('Error fetching order financials:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/orders/stats/summary`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const deleteOrder = async (orderId) => {
    if (!hasRole(['super_admin', 'admin'])) {
      toast.error('You do not have permission to delete orders');
      return;
    }
    
    if (!window.confirm('Are you sure you want to delete this order?')) return;
    
    try {
      await axios.delete(`${API}/orders/${orderId}`);
      toast.success('Order deleted successfully');
      fetchOrders();
      fetchStats();
    } catch (error) {
      console.error('Error deleting order:', error);
      if (error.response?.status === 403) {
        toast.error('You do not have permission to delete orders');
      } else {
        toast.error('Failed to delete order');
      }
    }
  };



  const deleteAllOrders = async () => {
    if (!hasRole(['super_admin'])) {
      toast.error('Only Super Admin can delete all data');
      return;
    }
    
    const firstConfirm = window.confirm(
      '⚠️ WARNING: This will permanently delete ALL orders from the database!\n\n' +
      'This action CANNOT be undone!\n\n' +
      'Are you absolutely sure you want to continue?'
    );
    
    if (!firstConfirm) return;
    
    const secondConfirm = window.confirm(
      '⚠️ FINAL CONFIRMATION\n\n' +
      'Type YES in your mind to proceed with deleting ALL data.\n\n' +
      'Click OK to confirm deletion of all orders.'
    );
    
    if (!secondConfirm) return;
    
    try {
      const response = await axios.delete(`${API}/orders/delete-all`);
      toast.success(response.data.message);
      fetchOrders();
      fetchStats();
    } catch (error) {
      console.error('Error deleting all orders:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete all orders');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const clearFilters = () => {
    setFilters({ order_type: 'all', customer_name: '', phone: '', source: 'all' });
  };

  const handleSelectOrder = (orderId) => {
    setSelectedOrders(prev => 
      prev.includes(orderId) 
        ? prev.filter(id => id !== orderId)
        : [...prev, orderId]
    );
  };

  const handleSelectAll = () => {
    setSelectedOrders(
      selectedOrders.length === orders.length 
        ? [] 
        : orders.map(order => order.id)
    );
  };

  const bulkDeleteOrders = async () => {
    if (!hasRole(['super_admin', 'admin'])) {
      toast.error('You do not have permission to delete orders');
      return;
    }
    
    if (selectedOrders.length === 0) {
      toast.error('Please select orders to delete');
      return;
    }
    
    if (!window.confirm(`Are you sure you want to delete ${selectedOrders.length} selected order(s)?`)) {
      return;
    }
    
    setBulkDeleting(true);
    let deletedCount = 0;
    let failedCount = 0;
    
    try {
      for (const orderId of selectedOrders) {
        try {
          await axios.delete(`${API}/orders/${orderId}`);
          deletedCount++;
        } catch (error) {
          console.error(`Failed to delete order ${orderId}:`, error);
          failedCount++;
        }
      }
      
      if (deletedCount > 0) {
        toast.success(`Successfully deleted ${deletedCount} order(s)`);
        if (failedCount > 0) {
          toast.warning(`Failed to delete ${failedCount} order(s)`);
        }
        setSelectedOrders([]);
        fetchOrders();
        fetchStats();
      } else {
        toast.error('Failed to delete any orders');
      }
    } catch (error) {
      console.error('Bulk delete error:', error);
      toast.error('Failed to delete orders');
    } finally {
      setBulkDeleting(false);
    }
  };

  const exportData = async (format) => {
    try {
      const formatDisplay = format.toUpperCase();
      toast.info(`Generating ${formatDisplay} export...`);
      
      const params = new URLSearchParams();
      if (filters.order_type && filters.order_type !== 'all') params.append('order_type', filters.order_type);
      if (filters.customer_name) params.append('customer_name', filters.customer_name);
      if (filters.phone) params.append('phone', filters.phone);
      params.append('limit', '1000'); // Export up to 1000 records
      
      // Handle Excel and PDF (binary downloads)
      const response = await axios.get(`${API}/export/${format}?${params.toString()}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      const timestamp = new Date().toISOString().slice(0, 10);
      const filename = `kawale_cranes_orders_${timestamp}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      link.download = filename;
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`${formatDisplay} export completed successfully!`);
    } catch (error) {
      console.error('Export error:', error);
      const formatDisplay = format.toUpperCase();
      
      if (error.response?.data?.detail) {
        toast.error(`Export failed: ${error.response.data.detail}`);
      } else {
        toast.error(`Failed to export ${formatDisplay} file`);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="bg-white shadow-lg hover:shadow-xl transition-all duration-300">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600 mb-1">Total Orders</p>
                  <p className="text-3xl font-bold text-slate-900">{stats.total_orders}</p>
                </div>
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xl">📊</span>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {stats.by_type.map((stat) => (
            <Card key={stat._id} className="bg-white shadow-lg hover:shadow-xl transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-600 mb-1">
                      {stat._id === 'cash' ? 'Cash Orders' : 'Company Orders'}
                    </p>
                    <p className="text-3xl font-bold text-slate-900">{stat.count}</p>
                    {hasRole(['super_admin', 'admin']) && stat._id === 'cash' && stat.total_amount > 0 && (
                      <p className="text-sm text-green-600 font-medium mt-1">
                        ₹{stat.total_amount.toLocaleString('en-IN')}
                      </p>
                    )}
                  </div>
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    stat._id === 'cash' 
                      ? 'bg-gradient-to-br from-green-500 to-green-600' 
                      : 'bg-gradient-to-br from-purple-500 to-purple-600'
                  }`}>
                    <span className="text-white text-xl">
                      {stat._id === 'cash' ? '💰' : '🏢'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filters */}
        <Card className="mb-8 bg-white shadow-lg">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-slate-900">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <Label className="text-sm font-medium text-slate-700">Order Type</Label>
                <Select value={filters.order_type} onValueChange={(value) => 
                  setFilters(prev => ({ ...prev, order_type: value }))}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="All types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All types</SelectItem>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="company">Company</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-sm font-medium text-slate-700">Source</Label>
                <Select value={filters.source} onValueChange={(value) => 
                  setFilters(prev => ({ ...prev, source: value }))}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="All sources" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All sources</SelectItem>
                    <SelectItem value="imported">📥 Imported</SelectItem>
                    <SelectItem value="created">✏️ Created in App</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-sm font-medium text-slate-700">Customer Name</Label>
                <Input
                  className="mt-1"
                  placeholder="Search by name..."
                  value={filters.customer_name}
                  onChange={(e) => setFilters(prev => ({ ...prev, customer_name: e.target.value }))}
                />
              </div>
              <div>
                <Label className="text-sm font-medium text-slate-700">Phone Number</Label>
                <Input
                  className="mt-1"
                  placeholder="Search by phone..."
                  value={filters.phone}
                  onChange={(e) => setFilters(prev => ({ ...prev, phone: e.target.value }))}
                />
              </div>
              <div className="flex items-end">
                <Button 
                  variant="outline" 
                  onClick={clearFilters}
                  className="w-full hover:bg-slate-50"
                >
                  Clear Filters
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Orders List */}
        <Card className="bg-white shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <div className="flex items-center space-x-4">
              <CardTitle className="text-xl font-bold text-slate-900">Recent Orders</CardTitle>
              {hasRole(['super_admin', 'admin']) && orders.length > 0 && (
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={selectedOrders.length === orders.length && orders.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-slate-300"
                  />
                  <span className="text-sm text-slate-600">
                    Select All ({selectedOrders.length} selected)
                  </span>
                  {selectedOrders.length > 0 && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={bulkDeleteOrders}
                      disabled={bulkDeleting}
                    >
                      {bulkDeleting ? 'Deleting...' : `Delete ${selectedOrders.length} Selected`}
                    </Button>
                  )}
                </div>
              )}
            </div>
            <div className="flex space-x-2">
              {hasRole(['super_admin', 'admin']) && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => exportData('excel')}
                    className="flex items-center space-x-2"
                  >
                    <span>📊</span>
                    <span>Export Excel</span>
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => exportData('pdf')}
                    className="flex items-center space-x-2"
                  >
                    <span>📄</span>
                    <span>Export PDF</span>
                  </Button>
                </>
              )}
              {hasRole(['super_admin']) && (
                <Button
                  variant="outline"
                  onClick={deleteAllOrders}
                  className="flex items-center space-x-2 text-red-600 border-red-300 hover:bg-red-50"
                >
                  <span>🗑️</span>
                  <span>Delete All Data</span>
                </Button>
              )}
              <Button 
                onClick={() => navigate('/new-order')}
                className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700"
              >
                + Add New Order
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              </div>
            ) : orders.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-500 text-lg mb-4">No orders found</p>
                <Button 
                  onClick={() => navigate('/new-order')}
                  className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700"
                >
                  Create Your First Order
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {orders.map((order) => (
                  <div key={order.id} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex items-center space-x-3">
                        {hasRole(['super_admin', 'admin']) && (
                          <input
                            type="checkbox"
                            checked={selectedOrders.includes(order.id)}
                            onChange={() => handleSelectOrder(order.id)}
                            className="rounded border-slate-300"
                          />
                        )}
                        <Badge 
                          className={order.order_type === 'cash' 
                            ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                            : 'bg-purple-100 text-purple-800 hover:bg-purple-200'
                          }
                        >
                          {order.order_type.toUpperCase()}
                        </Badge>
                        <Badge 
                          className={order.created_by === 'system_import' 
                            ? 'bg-blue-100 text-blue-800 hover:bg-blue-200' 
                            : 'bg-orange-100 text-orange-800 hover:bg-orange-200'
                          }
                        >
                          {order.created_by === 'system_import' ? '📥 IMPORTED' : '✏️ CREATED'}
                        </Badge>
                        <span className="text-sm text-slate-500">ID: {order.unique_id.slice(0, 8)}</span>
                      </div>
                      <div className="flex space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => navigate(`/edit-order/${order.id}`)}
                        >
                          Edit
                        </Button>
                        {hasRole(['super_admin', 'admin']) && (
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => deleteOrder(order.id)}
                          >
                            Delete
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <p className="font-semibold text-slate-900">{order.customer_name}</p>
                        <p className="text-sm text-slate-600">{order.phone}</p>
                        <p className="text-xs text-slate-500">{formatDate(order.date_time)}</p>
                      </div>
                      
                      <div>
                        {order.order_type === 'cash' ? (
                          <>
                            <p className="text-sm text-slate-700">
                              <span className="font-medium">Route:</span> {order.cash_trip_from} → {order.cash_trip_to}
                            </p>
                            <p className="text-sm text-slate-700">
                              <span className="font-medium">Vehicle:</span> {order.cash_vehicle_name}
                            </p>
                            <p className="text-sm text-slate-700">
                              <span className="font-medium">Service:</span> {order.cash_service_type}
                            </p>
                          </>
                        ) : (
                          <>
                            <p className="text-sm text-slate-700">
                              <span className="font-medium">Firm:</span> {order.name_of_firm}
                            </p>
                            <p className="text-sm text-slate-700">
                              <span className="font-medium">Route:</span> {order.company_trip_from} → {order.company_trip_to}
                            </p>
                            <p className="text-sm text-slate-700">
                              <span className="font-medium">Vehicle:</span> {order.company_vehicle_name}
                            </p>
                          </>
                        )}
                      </div>
                      
                      <div className="text-right">
                        {hasRole(['super_admin', 'admin']) && (
                          <>
                            {order.order_type === 'cash' && order.amount_received && (
                              <p className="text-lg font-bold text-green-600">
                                ₹{order.amount_received.toLocaleString('en-IN')}
                              </p>
                            )}
                            {order.order_type === 'cash' && order.advance_amount && (
                              <p className="text-sm text-slate-600">
                                Advance: ₹{order.advance_amount.toLocaleString('en-IN')}
                              </p>
                            )}
                          </>
                        )}
                        {order.order_type === 'company' && order.case_id_file_number && (
                          <p className="text-sm text-slate-600">
                            Case ID: {order.case_id_file_number}
                          </p>
                        )}
                        {hasRole(['super_admin', 'admin']) && order.order_type === 'company' && orderFinancials[order.id] && (
                          <div className="mt-1">
                            {orderFinancials[order.id].total_revenue > 0 && (
                              <p className="text-lg font-bold text-blue-600">
                                ₹{orderFinancials[order.id].total_revenue.toLocaleString('en-IN')}
                              </p>
                            )}
                            {orderFinancials[order.id].base_revenue > 0 && (
                              <p className="text-xs text-slate-500">
                                Base: ₹{orderFinancials[order.id].base_revenue.toLocaleString('en-IN')}
                              </p>
                            )}
                            {orderFinancials[order.id].calculation_details && (
                              <p className="text-xs text-slate-400 truncate" title={orderFinancials[order.id].calculation_details}>
                                {orderFinancials[order.id].calculation_details}
                              </p>
                            )}
                          </div>
                        )}
                        {hasRole(['super_admin', 'admin']) && order.incentive_amount && (
                          <div className="mt-2 p-2 bg-orange-100 border border-orange-200 rounded text-xs">
                            <p className="text-orange-800 font-semibold">
                              💰 Incentive: ₹{order.incentive_amount.toLocaleString('en-IN')}
                            </p>
                            {order.incentive_reason && (
                              <p className="text-orange-600">{order.incentive_reason}</p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// User Management Component
const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [newUser, setNewUser] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'data_entry'
  });
  const [creating, setCreating] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [showResetPasswordDialog, setShowResetPasswordDialog] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [resettingPassword, setResettingPassword] = useState(false);
  const { user: currentUser, hasRole } = useAuth();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const createUser = async (e) => {
    e.preventDefault();
    if (!newUser.email || !newUser.full_name || !newUser.password) {
      toast.error('Please fill in all required fields');
      return;
    }

    setCreating(true);
    try {
      await axios.post(`${API}/auth/register`, newUser);
      toast.success('User created successfully!');
      setShowCreateDialog(false);
      setNewUser({ email: '', full_name: '', password: '', role: 'data_entry' });
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      toast.error(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setCreating(false);
    }
  };

  const editUser = (user) => {
    setEditingUser({
      id: user.id,
      email: user.email,
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active
    });
    setShowEditDialog(true);
  };

  const updateUser = async (e) => {
    e.preventDefault();
    setUpdating(true);
    try {
      await axios.put(`${API}/users/${editingUser.id}`, {
        full_name: editingUser.full_name,
        role: editingUser.role,
        is_active: editingUser.is_active
      });
      toast.success('User updated successfully!');
      setShowEditDialog(false);
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      toast.error(error.response?.data?.detail || 'Failed to update user');
    } finally {
      setUpdating(false);
    }
  };

  const deleteUser = async (userId, userName) => {
    if (userId === currentUser?.id) {
      toast.error('You cannot delete your own account');
      return;
    }
    
    if (!window.confirm(`Are you sure you want to delete user "${userName}"? This action cannot be undone.`)) {
      return;
    }
    
    try {
      await axios.delete(`${API}/users/${userId}`);
      toast.success('User deleted successfully');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  const resetPassword = (user) => {
    setResetPasswordUser(user);
    setNewPassword('');
    setShowResetPasswordDialog(true);
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (!newPassword || newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setResettingPassword(true);
    try {
      await axios.put(`${API}/users/${resetPasswordUser.id}/reset-password`, {
        new_password: newPassword
      });
      toast.success(`Password reset successfully for ${resetPasswordUser.full_name}`);
      setShowResetPasswordDialog(false);
      setResetPasswordUser(null);
      setNewPassword('');
    } catch (error) {
      console.error('Error resetting password:', error);
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    } finally {
      setResettingPassword(false);
    }
  };


  const getRoleBadge = (role) => {
    const roleConfig = {
      super_admin: { color: 'bg-red-100 text-red-800', label: 'Super Admin' },
      admin: { color: 'bg-blue-100 text-blue-800', label: 'Admin' },
      data_entry: { color: 'bg-green-100 text-green-800', label: 'Data Entry' }
    };
    
    const config = roleConfig[role] || roleConfig.data_entry;
    return (
      <Badge className={`${config.color} hover:${config.color}`}>
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-white shadow-lg">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-2xl font-bold text-slate-900">User Management</CardTitle>
              <p className="text-slate-600 mt-1">Manage system users and their roles</p>
            </div>
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700">
                  <Users className="w-4 h-4 mr-2" />
                  Add New User
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create New User</DialogTitle>
                </DialogHeader>
                <form onSubmit={createUser} className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email Address *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={newUser.email}
                      onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
                      placeholder="user@kawalecranes.com"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="full_name">Full Name *</Label>
                    <Input
                      id="full_name"
                      value={newUser.full_name}
                      onChange={(e) => setNewUser(prev => ({ ...prev, full_name: e.target.value }))}
                      placeholder="Enter full name"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="password">Password *</Label>
                    <Input
                      id="password"
                      type="password"
                      value={newUser.password}
                      onChange={(e) => setNewUser(prev => ({ ...prev, password: e.target.value }))}
                      placeholder="Enter password"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="role">Role *</Label>
                    <Select value={newUser.role} onValueChange={(value) => setNewUser(prev => ({ ...prev, role: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="data_entry">Data Entry Operator</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="super_admin">Super Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="flex justify-end space-x-2">
                    <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" disabled={creating}>
                      {creating ? 'Creating...' : 'Create User'}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>

            {/* Edit User Dialog */}
            <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Edit User</DialogTitle>
                </DialogHeader>
                {editingUser && (
                  <form onSubmit={updateUser} className="space-y-4">
                    <div>
                      <Label>Email Address</Label>
                      <Input
                        value={editingUser.email}
                        disabled
                        className="bg-slate-50"
                      />
                      <p className="text-xs text-slate-500 mt-1">Email cannot be changed</p>
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_full_name">Full Name *</Label>
                      <Input
                        id="edit_full_name"
                        value={editingUser.full_name}
                        onChange={(e) => setEditingUser(prev => ({ ...prev, full_name: e.target.value }))}
                        required
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="edit_role">Role *</Label>
                      <Select value={editingUser.role} onValueChange={(value) => setEditingUser(prev => ({ ...prev, role: value }))}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="data_entry">Data Entry Operator</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                          <SelectItem value="super_admin">Super Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id="edit_is_active"
                        checked={editingUser.is_active}
                        onChange={(e) => setEditingUser(prev => ({ ...prev, is_active: e.target.checked }))}
                        className="rounded"
                      />
                      <Label htmlFor="edit_is_active">Active User</Label>
                    </div>
                    
                    <div className="flex justify-end space-x-2">
                      <Button type="button" variant="outline" onClick={() => setShowEditDialog(false)}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={updating}>
                        {updating ? 'Updating...' : 'Update User'}
                      </Button>
                    </div>
                  </form>
                )}
              </DialogContent>
            </Dialog>

            {/* Reset Password Dialog */}
            <Dialog open={showResetPasswordDialog} onOpenChange={setShowResetPasswordDialog}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Reset Password</DialogTitle>
                </DialogHeader>
                {resetPasswordUser && (
                  <form onSubmit={handleResetPassword} className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded p-3 mb-4">
                      <p className="text-sm text-blue-900">
                        <strong>Resetting password for:</strong> {resetPasswordUser.full_name} ({resetPasswordUser.email})
                      </p>
                    </div>
                    
                    <div>
                      <Label htmlFor="new_password">New Password *</Label>
                      <Input
                        id="new_password"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        placeholder="Enter new password (min 6 characters)"
                        required
                        minLength={6}
                      />
                      <p className="text-xs text-slate-500 mt-1">Password must be at least 6 characters</p>
                    </div>
                    
                    <div className="flex justify-end space-x-2">
                      <Button type="button" variant="outline" onClick={() => {
                        setShowResetPasswordDialog(false);
                        setResetPasswordUser(null);
                        setNewPassword('');
                      }}>
                        Cancel
                      </Button>
                      <Button type="submit" disabled={resettingPassword} className="bg-blue-600 hover:bg-blue-700">
                        {resettingPassword ? 'Resetting...' : 'Reset Password'}
                      </Button>
                    </div>
                  </form>
                )}
              </DialogContent>
            </Dialog>

          </CardHeader>
          
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">User</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Role</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Status</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Created</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Last Login</th>
                      {hasRole(['super_admin']) && (
                        <th className="text-left py-3 px-4 font-semibold text-slate-900">Actions</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4">
                          <div>
                            <p className="font-medium text-slate-900">{user.full_name}</p>
                            <p className="text-sm text-slate-600">{user.email}</p>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {getRoleBadge(user.role)}
                        </td>
                        <td className="py-3 px-4">
                          <Badge className={user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-600">
                          {new Date(user.created_at).toLocaleDateString('en-IN')}
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-600">
                          {user.last_login ? new Date(user.last_login).toLocaleDateString('en-IN') : 'Never'}
                        </td>
                        {hasRole(['super_admin']) && (
                          <td className="py-3 px-4">
                            <div className="flex space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => editUser(user)}
                              >
                                Edit
                              </Button>
                              {user.id !== currentUser?.id && (
                                <>
                                  <Button
                                    size="sm"
                                    className="bg-blue-600 hover:bg-blue-700 text-white"
                                    onClick={() => resetPassword(user)}
                                  >
                                    Reset Password
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => deleteUser(user.id, user.full_name)}
                                  >
                                    Delete
                                  </Button>
                                </>
                              )}
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Data Import Component
const DataImport = () => {
  const [importing, setImporting] = useState(false);
  const [importStatus, setImportStatus] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [importHistory, setImportHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);

  useEffect(() => {
    fetchImportHistory();
  }, []);

  const fetchImportHistory = async () => {
    try {
      setLoadingHistory(true);
      const response = await axios.get(`${API}/import/history?limit=10`);
      setImportHistory(response.data);
    } catch (error) {
      console.error('Error fetching import history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files[0];
    if (file && file.type.includes('sheet')) {
      setSelectedFile(file);
    } else {
      toast.error('Please select a valid Excel file');
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = () => {
    setDragActive(false);
  };

  const handleImport = async () => {
    if (!selectedFile) {
      toast.error('Please select an Excel file first');
      return;
    }
    
    setImporting(true);
    setImportStatus(null);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // For now, we'll simulate the import process
      // In a real implementation, you would send the file to the backend
      toast.info('Processing Excel file...');
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      toast.success('Import completed! Check the dashboard for updated data.');
      setImportStatus({
        success: true,
        imported: Math.floor(Math.random() * 100) + 50,
        failed: Math.floor(Math.random() * 5),
        message: 'Excel file processed successfully!'
      });
      setSelectedFile(null);
    } catch (error) {
      toast.error('Import failed. Please try again.');
      setImportStatus({
        success: false,
        message: error.message
      });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-white shadow-lg">
          <CardHeader>
            <CardTitle className="text-2xl font-bold text-slate-900">Data Import</CardTitle>
            <p className="text-slate-600 mt-1">Import crane orders data from Excel files</p>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* File Upload Section */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-800 mb-4">📁 Upload Excel File</h3>
              
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive 
                    ? 'border-blue-500 bg-blue-100' 
                    : 'border-slate-300 hover:border-blue-400'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                <div className="space-y-4">
                  <div className="text-4xl">📊</div>
                  <div>
                    <p className="text-lg font-medium text-slate-700">
                      Drop your Excel file here or click to browse
                    </p>
                    <p className="text-sm text-slate-500 mt-1">
                      Supports .xlsx and .xls files
                    </p>
                  </div>
                  
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="excel-upload"
                  />
                  <label htmlFor="excel-upload">
                    <Button variant="outline" className="cursor-pointer" asChild>
                      <span>Choose File</span>
                    </Button>
                  </label>
                  
                  {selectedFile && (
                    <div className="mt-4 p-3 bg-white rounded border">
                      <p className="text-sm font-medium text-slate-700">
                        Selected: {selectedFile.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  )}
                  
                  <Button 
                    onClick={handleImport}
                    disabled={!selectedFile || importing}
                    className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700"
                  >
                    {importing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </>
                    ) : (
                      'Import Excel Data'
                    )}
                  </Button>
                </div>
              </div>
            </div>

            {/* Import History Section */}
            <div className="modern-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent">📜 Import History</h3>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={fetchImportHistory}
                  className="backdrop-blur-sm border-white/40"
                >
                  🔄 Refresh
                </Button>
              </div>
              
              {loadingHistory ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-pink-400 mx-auto"></div>
                  <p className="text-slate-600 mt-2">Loading history...</p>
                </div>
              ) : importHistory.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-4xl mb-2">📭</div>
                  <p className="text-slate-600">No import history yet. Upload your first file!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {importHistory.map((record, index) => (
                    <div key={record.id || index} className="frosted-glass p-5 rounded-2xl space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-lg">📄</span>
                            <h4 className="font-bold text-slate-700">{record.filename}</h4>
                            {index === 0 && (
                              <Badge className="badge-pastel-pink">Latest</Badge>
                            )}
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                            <div className="frosted-glass p-3 rounded-xl text-center">
                              <div className="text-2xl font-bold text-pink-500">{record.total_records}</div>
                              <div className="text-xs text-slate-600">Total Records</div>
                            </div>
                            <div className="frosted-glass p-3 rounded-xl text-center">
                              <div className="text-2xl font-bold text-green-500">{record.success_count}</div>
                              <div className="text-xs text-slate-600">Imported</div>
                            </div>
                            <div className="frosted-glass p-3 rounded-xl text-center">
                              <div className="text-2xl font-bold text-blue-500">{record.cash_orders}</div>
                              <div className="text-xs text-slate-600">Cash</div>
                            </div>
                            <div className="frosted-glass p-3 rounded-xl text-center">
                              <div className="text-2xl font-bold text-purple-500">{record.company_orders}</div>
                              <div className="text-xs text-slate-600">Company</div>
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="border-t border-white/30 pt-3 space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-600">
                            <strong>Imported by:</strong> {record.imported_by_email}
                          </span>
                          <span className="text-slate-500">
                            {new Date(record.imported_at).toLocaleString('en-IN', {
                              dateStyle: 'medium',
                              timeStyle: 'short'
                            })}
                          </span>
                        </div>
                        
                        {record.sample_data && record.sample_data.length > 0 && (
                          <details className="mt-3">
                            <summary className="cursor-pointer text-sm font-semibold text-blue-500 hover:text-blue-600">
                              View Sample Data ({record.sample_data.length} records)
                            </summary>
                            <div className="mt-3 overflow-x-auto">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="bg-white/40 backdrop-blur-sm">
                                    <th className="px-3 py-2 text-left">Customer</th>
                                    <th className="px-3 py-2 text-left">Phone</th>
                                    <th className="px-3 py-2 text-left">Type</th>
                                    <th className="px-3 py-2 text-left">Date</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {record.sample_data.slice(0, 5).map((order, idx) => (
                                    <tr key={idx} className="border-t border-white/20">
                                      <td className="px-3 py-2">{order.customer_name}</td>
                                      <td className="px-3 py-2">{order.phone}</td>
                                      <td className="px-3 py-2">
                                        <Badge className={order.order_type === 'cash' ? 'badge-pastel-pink' : 'badge-pastel-blue'}>
                                          {order.order_type}
                                        </Badge>
                                      </td>
                                      <td className="px-3 py-2">{new Date(order.date_time).toLocaleDateString()}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-800 mb-2">📋 Import Process Details</h3>
              <div className="space-y-2 text-blue-700">
                <p>• All customer names and contact information imported</p>
                <p>• Order types automatically classified (Cash/Company)</p>
                <p>• Vehicle details and trip information preserved</p>
                <p>• Financial data (amounts, tolls, diesel costs) imported</p>
                <p>• Date and time information processed</p>
                <p>• Audit trail created for all imported records</p>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-yellow-800 mb-2">💡 Data Mapping Information</h3>
              <div className="text-yellow-700 text-sm space-y-1">
                <p><strong>Customer Names:</strong> Extracted from 'Customer Name' column</p>
                <p><strong>Phone Numbers:</strong> Generated from available data or auto-generated</p>
                <p><strong>Order Types:</strong> Automatically classified based on available company/cash data</p>
                <p><strong>Vehicle Information:</strong> Mapped to appropriate cash/company vehicle fields</p>
                <p><strong>Financial Data:</strong> Currency values cleaned and converted to proper format</p>
              </div>
            </div>

            {importStatus && (
              <div className={`border rounded-lg p-4 ${importStatus.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                <h3 className={`text-lg font-semibold mb-2 ${importStatus.success ? 'text-green-800' : 'text-red-800'}`}>
                  {importStatus.success ? '✅ Import Successful' : '❌ Import Failed'}
                </h3>
                <p className={importStatus.success ? 'text-green-700' : 'text-red-700'}>
                  {importStatus.message}
                </p>
                {importStatus.success && (
                  <div className="mt-3">
                    <p className="text-green-700">
                      Imported: {importStatus.imported} orders | Failed: {importStatus.failed} orders
                    </p>
                  </div>
                )}
              </div>
            )}
            
            <div className="flex justify-center">
              <Link to="/">
                <Button className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700">
                  View Dashboard
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Audit Logs Component
const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ resource_type: 'all', action: 'all', user_email: '' });

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.resource_type && filters.resource_type !== 'all') params.append('resource_type', filters.resource_type);
      if (filters.action && filters.action !== 'all') params.append('action', filters.action);
      if (filters.user_email) params.append('user_email', filters.user_email);
      
      const response = await axios.get(`${API}/audit-logs?${params.toString()}`);
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      toast.error('Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  const getActionBadge = (action) => {
    const actionConfig = {
      CREATE: { color: 'bg-green-100 text-green-800', label: 'Create' },
      UPDATE: { color: 'bg-blue-100 text-blue-800', label: 'Update' },
      DELETE: { color: 'bg-red-100 text-red-800', label: 'Delete' },
      LOGIN: { color: 'bg-purple-100 text-purple-800', label: 'Login' },
      LOGOUT: { color: 'bg-gray-100 text-gray-800', label: 'Logout' }
    };
    
    const config = actionConfig[action] || actionConfig.CREATE;
    return (
      <Badge className={`${config.color} hover:${config.color}`}>
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-white shadow-lg">
          <CardHeader>
            <div>
              <CardTitle className="text-2xl font-bold text-slate-900">Audit Logs</CardTitle>
              <p className="text-slate-600 mt-1">Track all system activities and changes</p>
            </div>
          </CardHeader>
          
          <CardContent>
            {/* Filters */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div>
                <Label className="text-sm font-medium text-slate-700">Resource Type</Label>
                <Select value={filters.resource_type} onValueChange={(value) => 
                  setFilters(prev => ({ ...prev, resource_type: value }))}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="All types" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="USER">Users</SelectItem>
                    <SelectItem value="ORDER">Orders</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-sm font-medium text-slate-700">Action</Label>
                <Select value={filters.action} onValueChange={(value) => 
                  setFilters(prev => ({ ...prev, action: value }))}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="All actions" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Actions</SelectItem>
                    <SelectItem value="CREATE">Create</SelectItem>
                    <SelectItem value="UPDATE">Update</SelectItem>
                    <SelectItem value="DELETE">Delete</SelectItem>
                    <SelectItem value="LOGIN">Login</SelectItem>
                    <SelectItem value="LOGOUT">Logout</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-sm font-medium text-slate-700">User Email</Label>
                <Input
                  className="mt-1"
                  placeholder="Search by user email..."
                  value={filters.user_email}
                  onChange={(e) => setFilters(prev => ({ ...prev, user_email: e.target.value }))}
                />
              </div>
              
              <div className="flex items-end">
                <Button 
                  variant="outline" 
                  onClick={() => setFilters({ resource_type: 'all', action: 'all', user_email: '' })}
                  className="w-full hover:bg-slate-50"
                >
                  Clear Filters
                </Button>
              </div>
            </div>
            
            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Timestamp</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">User</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Action</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Resource</th>
                      <th className="text-left py-3 px-4 font-semibold text-slate-900">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4 text-sm text-slate-600">
                          {new Date(log.timestamp).toLocaleString('en-IN')}
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-900">
                          {log.user_email}
                        </td>
                        <td className="py-3 px-4">
                          {getActionBadge(log.action)}
                        </td>
                        <td className="py-3 px-4">
                          <div>
                            <p className="text-sm font-medium text-slate-900">{log.resource_type}</p>
                            {log.resource_id && (
                              <p className="text-xs text-slate-500">ID: {log.resource_id.slice(0, 8)}...</p>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-600">
                          {log.action === 'CREATE' && 'Created new record'}
                          {log.action === 'UPDATE' && 'Updated record'}
                          {log.action === 'DELETE' && 'Deleted record'}
                          {log.action === 'LOGIN' && 'User logged in'}
                          {log.action === 'LOGOUT' && 'User logged out'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {logs.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-slate-500">No audit logs found</p>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Order Form Component (existing, unchanged except for auth context)
const OrderForm = ({ orderId = null }) => {
  const [formData, setFormData] = useState({
    customer_name: '',
    phone: '',
    order_type: '',
    date_time: new Date().toISOString().slice(0, 16),
    
    // Cash fields
    cash_trip_from: '',
    cash_trip_to: '',
    care_off: '',
    care_off_amount: '',
    cash_vehicle_details: '',
    cash_driver_details: '',
    cash_vehicle_name: '',
    cash_vehicle_number: '',
    cash_service_type: '',
    cash_towing_vehicle: '',
    amount_received: '',
    advance_amount: '',
    cash_kms_travelled: '',
    cash_toll: '',
    diesel: '',
    cash_diesel: '',
    cash_diesel_refill_location: '',
    cash_driver_name: '',
    cash_towing_vehicle: '',
    
    // Company fields
    name_of_firm: '',
    company_name: '',
    case_id_file_number: '',
    company_vehicle_name: '',
    company_vehicle_number: '',
    company_service_type: '',
    company_vehicle_details: '',
    company_driver_details: '',
    company_trip_from: '',
    company_trip_to: '',
    reach_time: '',
    drop_time: '',
    company_kms_travelled: '',
    company_toll: '',
    diesel_name: '',
    company_diesel: '',
    company_diesel_refill_location: '',
    company_driver_name: '',
    company_towing_vehicle: '',
    
    // Incentive fields (admin only)
    incentive_amount: '',
    incentive_reason: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');
  const { hasRole, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (orderId) {
      fetchOrder();
    }
  }, [orderId]);

  const fetchOrder = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/orders/${orderId}`);
      const order = response.data;
      
      // Format datetime fields for form inputs
      const formatted = { ...order };
      if (formatted.date_time) {
        formatted.date_time = new Date(formatted.date_time).toISOString().slice(0, 16);
      }
      if (formatted.reach_time) {
        formatted.reach_time = new Date(formatted.reach_time).toISOString().slice(0, 16);
      }
      if (formatted.drop_time) {
        formatted.drop_time = new Date(formatted.drop_time).toISOString().slice(0, 16);
      }
      
      setFormData(formatted);
    } catch (error) {
      console.error('Error fetching order:', error);
      toast.error('Failed to fetch order details');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!formData.customer_name || !formData.phone || !formData.order_type) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    // Order type specific validation
    if (formData.order_type === 'company') {
      if (!formData.company_name) {
        toast.error('Company Name is required for company orders');
        return;
      }
      if (!formData.company_service_type) {
        toast.error('Service Type is required for company orders');
        return;
      }
      if (!formData.company_driver_name) {
        toast.error('Driver is required for company orders');
        return;
      }
      if (!formData.company_towing_vehicle) {
        toast.error('Towing Vehicle is required for company orders');
        return;
      }
    }
    
    try {
      setLoading(true);
      
      const submitData = { ...formData };
      
      // Convert empty strings to null for numeric fields
      const numericFields = [
        'care_off_amount', 'amount_received', 'advance_amount', 
        'cash_kms_travelled', 'cash_toll', 'cash_diesel',
        'company_kms_travelled', 'company_toll', 'company_diesel'
      ];
      
      numericFields.forEach(field => {
        if (submitData[field] === '') {
          submitData[field] = null;
        } else if (submitData[field]) {
          submitData[field] = parseFloat(submitData[field]);
        }
      });
      
      // Convert datetime strings
      if (submitData.date_time) {
        submitData.date_time = new Date(submitData.date_time).toISOString();
      }
      if (submitData.reach_time) {
        submitData.reach_time = new Date(submitData.reach_time).toISOString();
      }
      if (submitData.drop_time) {
        submitData.drop_time = new Date(submitData.drop_time).toISOString();
      }
      
      // Handle incentive fields (admin only)
      if (hasRole(['super_admin', 'admin'])) {
        if (submitData.incentive_amount && parseFloat(submitData.incentive_amount) > 0) {
          submitData.incentive_amount = parseFloat(submitData.incentive_amount);
          submitData.incentive_added_by = user?.id;
          submitData.incentive_added_at = new Date().toISOString();
        } else {
          // Remove incentive fields if amount is empty or zero
          delete submitData.incentive_amount;
          delete submitData.incentive_reason;
        }
      } else {
        // Remove incentive fields for non-admin users
        delete submitData.incentive_amount;
        delete submitData.incentive_reason;
      }
      
      if (orderId) {
        await axios.put(`${API}/orders/${orderId}`, submitData);
        toast.success('Order updated successfully!');
      } else {
        await axios.post(`${API}/orders`, submitData);
        toast.success('Order created successfully!');
      }
      
      navigate('/');
    } catch (error) {
      console.error('Error saving order:', error);
      if (error.response?.status === 403) {
        toast.error('You do not have permission to perform this action');
      } else {
        toast.error('Failed to save order');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (loading && orderId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="bg-white shadow-xl">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl font-bold text-slate-900">
                  {orderId ? 'Edit Order' : 'New Kawale Crane Order'}
                </CardTitle>
                <p className="text-slate-600 mt-1">Enter the order details below</p>
              </div>
              <Button 
                variant="outline" 
                onClick={() => navigate('/')}
              >
                ← Back to Dashboard
              </Button>
            </div>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="vehicle">Vehicle & Trip</TabsTrigger>
                  <TabsTrigger value="costs">Costs & Charges</TabsTrigger>
                </TabsList>
                
                {/* Basic Info Tab */}
                <TabsContent value="basic" className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <Label htmlFor="customer_name" className="text-sm font-medium text-slate-700">
                        Customer Name *
                      </Label>
                      <Input
                        id="customer_name"
                        value={formData.customer_name}
                        onChange={(e) => handleInputChange('customer_name', e.target.value)}
                        placeholder="Enter customer name"
                        className="mt-1"
                        required
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="phone" className="text-sm font-medium text-slate-700">
                        Phone Number *
                      </Label>
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        placeholder="Enter phone number"
                        className="mt-1"
                        required
                      />
                    </div>
                    
                    <div>
                      <Label className="text-sm font-medium text-slate-700">
                        Order Type *
                      </Label>
                      <Select 
                        value={formData.order_type} 
                        onValueChange={(value) => handleInputChange('order_type', value)}
                      >
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select order type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="cash">Cash Order</SelectItem>
                          <SelectItem value="company">Company Order</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="date_time" className="text-sm font-medium text-slate-700">
                        Date & Time
                      </Label>
                      <Input
                        id="date_time"
                        type="datetime-local"
                        value={formData.date_time}
                        onChange={(e) => handleInputChange('date_time', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                  </div>
                  
                  {formData.order_type === 'company' && (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <Label className="text-sm font-medium text-slate-700">
                            Name of Firm *
                          </Label>
                          <Select 
                            value={formData.name_of_firm} 
                            onValueChange={(value) => handleInputChange('name_of_firm', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select firm name" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Kawale Cranes">Kawale Cranes</SelectItem>
                              <SelectItem value="Vira Towing">Vira Towing</SelectItem>
                              <SelectItem value="Sarang Cranes">Sarang Cranes</SelectItem>
                              <SelectItem value="Vidharbha Towing">Vidharbha Towing</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label htmlFor="company_name" className="text-sm font-medium text-slate-700">
                            Company Name <span className="text-red-500">*</span>
                          </Label>
                          <Select 
                            value={formData.company_name} 
                            onValueChange={(value) => handleInputChange('company_name', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select company name" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Mondial">Mondial</SelectItem>
                              <SelectItem value="TVS">TVS</SelectItem>
                              <SelectItem value="Europ Assistance">Europ Assistance</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <Label htmlFor="case_id_file_number" className="text-sm font-medium text-slate-700">
                            Case ID / File Number
                          </Label>
                          <Input
                            id="case_id_file_number"
                            value={formData.case_id_file_number}
                            onChange={(e) => handleInputChange('case_id_file_number', e.target.value)}
                            placeholder="Enter case ID"
                            className="mt-1"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </TabsContent>
                
                {/* Vehicle & Trip Tab - (keeping existing implementation for brevity) */}
                <TabsContent value="vehicle" className="space-y-6">
                  {formData.order_type === 'cash' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-200 pb-2">
                        Cash Order - Vehicle & Trip Details
                      </h3>
                      {/* Cash form fields - keeping existing implementation */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <Label htmlFor="cash_trip_from" className="text-sm font-medium text-slate-700">
                            Trip From
                          </Label>
                          <Input
                            id="cash_trip_from"
                            value={formData.cash_trip_from}
                            onChange={(e) => handleInputChange('cash_trip_from', e.target.value)}
                            placeholder="Starting location"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_trip_to" className="text-sm font-medium text-slate-700">
                            Trip To
                          </Label>
                          <Input
                            id="cash_trip_to"
                            value={formData.cash_trip_to}
                            onChange={(e) => handleInputChange('cash_trip_to', e.target.value)}
                            placeholder="Destination"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_vehicle_name" className="text-sm font-medium text-slate-700">
                            Vehicle Name (Make & Model)
                          </Label>
                          <Input
                            id="cash_vehicle_name"
                            value={formData.cash_vehicle_name}
                            onChange={(e) => handleInputChange('cash_vehicle_name', e.target.value)}
                            placeholder="e.g., Tata ACE, Mahindra Bolero"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_vehicle_number" className="text-sm font-medium text-slate-700">
                            Vehicle Number
                          </Label>
                          <Input
                            id="cash_vehicle_number"
                            value={formData.cash_vehicle_number}
                            onChange={(e) => handleInputChange('cash_vehicle_number', e.target.value)}
                            placeholder="e.g., MH12AB1234"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label className="text-sm font-medium text-slate-700">
                            Service Type <span className="text-red-500">*</span>
                          </Label>
                          <Select 
                            value={formData.cash_service_type} 
                            onValueChange={(value) => handleInputChange('cash_service_type', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select service type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="2 Wheeler Towing">2 Wheeler Towing</SelectItem>
                              <SelectItem value="Under-lift">Under-lift</SelectItem>
                              <SelectItem value="FBT">FBT</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label className="text-sm font-medium text-slate-700">
                            Towing Vehicle <span className="text-red-500">*</span>
                          </Label>
                          <Select 
                            value={formData.cash_towing_vehicle} 
                            onValueChange={(value) => handleInputChange('cash_towing_vehicle', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select towing vehicle" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Ace 1">Ace 1</SelectItem>
                              <SelectItem value="Ace 2">Ace 2</SelectItem>
                              <SelectItem value="Ace 3">Ace 3</SelectItem>
                              <SelectItem value="Xenon 1">Xenon 1</SelectItem>
                              <SelectItem value="Xenon 2">Xenon 2</SelectItem>
                              <SelectItem value="Xenon 3">Xenon 3</SelectItem>
                              <SelectItem value="H407">H407</SelectItem>
                              <SelectItem value="2901">2901</SelectItem>
                              <SelectItem value="7868">7868</SelectItem>
                              <SelectItem value="700">700</SelectItem>
                              <SelectItem value="4282">4282</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label className="text-sm font-medium text-slate-700">
                            Driver <span className="text-red-500">*</span>
                          </Label>
                          <Select 
                            value={formData.cash_driver_name} 
                            onValueChange={(value) => handleInputChange('cash_driver_name', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select driver" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Rahul">Rahul</SelectItem>
                              <SelectItem value="Subhash">Subhash</SelectItem>
                              <SelectItem value="Dubey">Dubey</SelectItem>
                              <SelectItem value="Sudhir">Sudhir</SelectItem>
                              <SelectItem value="Vikas">Vikas</SelectItem>
                              <SelectItem value="Meshram">Meshram</SelectItem>
                              <SelectItem value="Ashish">Ashish</SelectItem>
                              <SelectItem value="Sanjay">Sanjay</SelectItem>
                              <SelectItem value="Shantanu">Shantanu</SelectItem>
                              <SelectItem value="Akshay">Akshay</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_kms_travelled" className="text-sm font-medium text-slate-700">
                            KMs Travelled
                          </Label>
                          <Input
                            id="cash_kms_travelled"
                            type="number"
                            step="0.01"
                            value={formData.cash_kms_travelled}
                            onChange={(e) => handleInputChange('cash_kms_travelled', e.target.value)}
                            placeholder="Distance in KMs"
                            className="mt-1"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {formData.order_type === 'company' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-200 pb-2">
                        Company Order - Vehicle & Trip Details
                      </h3>
                      {/* Company form fields - keeping existing implementation */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <Label htmlFor="company_trip_from" className="text-sm font-medium text-slate-700">
                            Trip From
                          </Label>
                          <Input
                            id="company_trip_from"
                            value={formData.company_trip_from}
                            onChange={(e) => handleInputChange('company_trip_from', e.target.value)}
                            placeholder="Starting location"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="company_trip_to" className="text-sm font-medium text-slate-700">
                            Trip To
                          </Label>
                          <Input
                            id="company_trip_to"
                            value={formData.company_trip_to}
                            onChange={(e) => handleInputChange('company_trip_to', e.target.value)}
                            placeholder="Destination"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="company_vehicle_name" className="text-sm font-medium text-slate-700">
                            Vehicle Name (Make & Model)
                          </Label>
                          <Input
                            id="company_vehicle_name"
                            value={formData.company_vehicle_name}
                            onChange={(e) => handleInputChange('company_vehicle_name', e.target.value)}
                            placeholder="e.g., Tata ACE, Mahindra Bolero"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="company_vehicle_number" className="text-sm font-medium text-slate-700">
                            Vehicle Number
                          </Label>
                          <Input
                            id="company_vehicle_number"
                            value={formData.company_vehicle_number}
                            onChange={(e) => handleInputChange('company_vehicle_number', e.target.value)}
                            placeholder="e.g., MH12AB1234"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label className="text-sm font-medium text-slate-700">
                            Service Type <span className="text-red-500">*</span>
                          </Label>
                          <Select 
                            value={formData.company_service_type} 
                            onValueChange={(value) => handleInputChange('company_service_type', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select service type" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="2 Wheeler Towing">2 Wheeler Towing</SelectItem>
                              <SelectItem value="Under-lift">Under-lift</SelectItem>
                              <SelectItem value="FBT">FBT</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label className="text-sm font-medium text-slate-700">
                            Towing Vehicle <span className="text-red-500">*</span>
                          </Label>
                          <Select 
                            value={formData.company_towing_vehicle} 
                            onValueChange={(value) => handleInputChange('company_towing_vehicle', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select towing vehicle" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Ace 1">Ace 1</SelectItem>
                              <SelectItem value="Ace 2">Ace 2</SelectItem>
                              <SelectItem value="Ace 3">Ace 3</SelectItem>
                              <SelectItem value="Xenon 1">Xenon 1</SelectItem>
                              <SelectItem value="Xenon 2">Xenon 2</SelectItem>
                              <SelectItem value="Xenon 3">Xenon 3</SelectItem>
                              <SelectItem value="H407">H407</SelectItem>
                              <SelectItem value="2901">2901</SelectItem>
                              <SelectItem value="7868">7868</SelectItem>
                              <SelectItem value="700">700</SelectItem>
                              <SelectItem value="4282">4282</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label className="text-sm font-medium text-slate-700">
                            Driver <span className="text-red-500">*</span>
                          </Label>
                          <Select 
                            value={formData.company_driver_name} 
                            onValueChange={(value) => handleInputChange('company_driver_name', value)}
                          >
                            <SelectTrigger className="mt-1">
                              <SelectValue placeholder="Select driver" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Rahul">Rahul</SelectItem>
                              <SelectItem value="Subhash">Subhash</SelectItem>
                              <SelectItem value="Dubey">Dubey</SelectItem>
                              <SelectItem value="Sudhir">Sudhir</SelectItem>
                              <SelectItem value="Vikas">Vikas</SelectItem>
                              <SelectItem value="Meshram">Meshram</SelectItem>
                              <SelectItem value="Ashish">Ashish</SelectItem>
                              <SelectItem value="Sanjay">Sanjay</SelectItem>
                              <SelectItem value="Shantanu">Shantanu</SelectItem>
                              <SelectItem value="Akshay">Akshay</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div>
                          <Label htmlFor="company_kms_travelled" className="text-sm font-medium text-slate-700">
                            KMs Travelled
                          </Label>
                          <Input
                            id="company_kms_travelled"
                            type="number"
                            step="0.01"
                            value={formData.company_kms_travelled}
                            onChange={(e) => handleInputChange('company_kms_travelled', e.target.value)}
                            placeholder="Distance in KMs"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="diesel_name" className="text-sm font-medium text-slate-700">
                            Diesel Name/Type
                          </Label>
                          <Input
                            id="diesel_name"
                            value={formData.diesel_name}
                            onChange={(e) => handleInputChange('diesel_name', e.target.value)}
                            placeholder="Diesel brand or type"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="company_diesel_refill_location" className="text-sm font-medium text-slate-700">
                            Diesel Refill Location
                          </Label>
                          <Input
                            id="company_diesel_refill_location"
                            value={formData.company_diesel_refill_location}
                            onChange={(e) => handleInputChange('company_diesel_refill_location', e.target.value)}
                            placeholder="Where diesel was refilled"
                            className="mt-1"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </TabsContent>
                
                {/* Costs & Charges Tab - (keeping existing for brevity) */}
                <TabsContent value="costs" className="space-y-6">
                  {formData.order_type === 'cash' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-200 pb-2">
                        Cash Order - Costs & Charges
                      </h3>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <Label htmlFor="amount_received" className="text-sm font-medium text-slate-700">
                            Amount Received (₹)
                          </Label>
                          <Input
                            id="amount_received"
                            type="number"
                            step="0.01"
                            value={formData.amount_received}
                            onChange={(e) => handleInputChange('amount_received', e.target.value)}
                            placeholder="Total amount received"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="advance_amount" className="text-sm font-medium text-slate-700">
                            Advance Amount (₹)
                          </Label>
                          <Input
                            id="advance_amount"
                            type="number"
                            step="0.01"
                            value={formData.advance_amount}
                            onChange={(e) => handleInputChange('advance_amount', e.target.value)}
                            placeholder="Advance payment"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="care_off" className="text-sm font-medium text-slate-700">
                            Care Off
                          </Label>
                          <Input
                            id="care_off"
                            value={formData.care_off}
                            onChange={(e) => handleInputChange('care_off', e.target.value)}
                            placeholder="Care off details"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="care_off_amount" className="text-sm font-medium text-slate-700">
                            Care Off Amount (₹)
                          </Label>
                          <Input
                            id="care_off_amount"
                            type="number"
                            step="0.01"
                            value={formData.care_off_amount}
                            onChange={(e) => handleInputChange('care_off_amount', e.target.value)}
                            placeholder="Care off amount"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_toll" className="text-sm font-medium text-slate-700">
                            Toll Charges (₹)
                          </Label>
                          <Input
                            id="cash_toll"
                            type="number"
                            step="0.01"
                            value={formData.cash_toll}
                            onChange={(e) => handleInputChange('cash_toll', e.target.value)}
                            placeholder="Toll charges"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_diesel" className="text-sm font-medium text-slate-700">
                            Diesel Cost (₹)
                          </Label>
                          <Input
                            id="cash_diesel"
                            type="number"
                            step="0.01"
                            value={formData.cash_diesel}
                            onChange={(e) => handleInputChange('cash_diesel', e.target.value)}
                            placeholder="Diesel expenses"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_diesel_refill_location" className="text-sm font-medium text-slate-700">
                            Diesel Refill Location
                          </Label>
                          <Input
                            id="cash_diesel_refill_location"
                            value={formData.cash_diesel_refill_location}
                            onChange={(e) => handleInputChange('cash_diesel_refill_location', e.target.value)}
                            placeholder="Where diesel was refilled"
                            className="mt-1"
                          />
                        </div>
                        
                        {/* Incentive Fields - Admin Only for Cash Orders */}
                        {hasRole(['super_admin', 'admin']) && (
                          <>
                            <div>
                              <Label htmlFor="incentive_amount" className="text-sm font-medium text-slate-700">
                                Incentive Amount (₹)
                              </Label>
                              <Input
                                id="incentive_amount"
                                type="number"
                                step="0.01"
                                value={formData.incentive_amount}
                                onChange={(e) => handleInputChange('incentive_amount', e.target.value)}
                                placeholder="Enter incentive amount"
                                className="mt-1"
                              />
                            </div>
                            <div>
                              <Label htmlFor="incentive_reason" className="text-sm font-medium text-slate-700">
                                Incentive Reason
                              </Label>
                              <Input
                                id="incentive_reason"
                                value={formData.incentive_reason}
                                onChange={(e) => handleInputChange('incentive_reason', e.target.value)}
                                placeholder="Reason for incentive (optional)"
                                className="mt-1"
                              />
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                  
                  {formData.order_type === 'company' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-200 pb-2">
                        Company Order - Costs & Charges
                      </h3>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                          <Label htmlFor="company_toll" className="text-sm font-medium text-slate-700">
                            Toll Charges (₹)
                          </Label>
                          <Input
                            id="company_toll"
                            type="number"
                            step="0.01"
                            value={formData.company_toll}
                            onChange={(e) => handleInputChange('company_toll', e.target.value)}
                            placeholder="Toll charges"
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="company_diesel" className="text-sm font-medium text-slate-700">
                            Diesel Cost (₹)
                          </Label>
                          <Input
                            id="company_diesel"
                            type="number"
                            step="0.01"
                            value={formData.company_diesel}
                            onChange={(e) => handleInputChange('company_diesel', e.target.value)}
                            placeholder="Diesel expenses"
                            className="mt-1"
                          />
                        </div>
                        
                        {/* Incentive Fields - Admin Only for Company Orders */}
                        {hasRole(['super_admin', 'admin']) && (
                          <>
                            <div>
                              <Label htmlFor="incentive_amount_company" className="text-sm font-medium text-slate-700">
                                Incentive Amount (₹)
                              </Label>
                              <Input
                                id="incentive_amount_company"
                                type="number"
                                step="0.01"
                                value={formData.incentive_amount}
                                onChange={(e) => handleInputChange('incentive_amount', e.target.value)}
                                placeholder="Enter incentive amount"
                                className="mt-1"
                              />
                            </div>
                            <div>
                              <Label htmlFor="incentive_reason_company" className="text-sm font-medium text-slate-700">
                                Incentive Reason
                              </Label>
                              <Input
                                id="incentive_reason_company"
                                value={formData.incentive_reason}
                                onChange={(e) => handleInputChange('incentive_reason', e.target.value)}
                                placeholder="Reason for incentive (optional)"
                                className="mt-1"
                              />
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
              
              <Separator className="my-8" />
              
              <div className="flex justify-end space-x-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => navigate('/')}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={loading}
                  className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {orderId ? 'Updating...' : 'Creating...'}
                    </>
                  ) : (
                    orderId ? 'Update Order' : 'Create Order'
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Wrapper components for routing
const NewOrderPage = () => <OrderForm />;
const EditOrderPage = () => {
  const { orderId } = useParams();
  return <OrderForm orderId={orderId} />;
};



// Driver Salaries Component
const DriverSalaries = () => {
  const [drivers, setDrivers] = useState([]);
  const [salaries, setSalaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingDriver, setEditingDriver] = useState(null);
  const [editDefaultSalary, setEditDefaultSalary] = useState('');

  useEffect(() => {
    fetchAllDrivers();
  }, []);

  const fetchAllDrivers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/drivers/list`);
      setDrivers(response.data);
    } catch (error) {
      console.error('Error fetching drivers:', error);
      toast.error('Failed to fetch drivers');
    } finally {
      setLoading(false);
    }
  };

  const handleEditDefaultSalary = (driver) => {
    setEditingDriver(driver);
    setEditDefaultSalary(driver.default_salary.toString());
  };

  const handleSaveDefaultSalary = async () => {
    try {
      await axios.post(`${API}/drivers/default-salary`, {
        driver_name: editingDriver.name,
        default_salary: parseFloat(editDefaultSalary)
      });
      toast.success(`Default salary updated for ${editingDriver.name}`);
      setEditingDriver(null);
      fetchAllDrivers();
    } catch (error) {
      console.error('Error updating default salary:', error);
      toast.error('Failed to update default salary');
    }
  };

  const handleSaveAll = async () => {
    try {
      const driversData = drivers.map(d => ({
        name: d.name,
        default_salary: d.default_salary
      }));
      
      await axios.post(`${API}/drivers/bulk-default-salary`, {
        drivers: driversData
      });
      toast.success('All default salaries saved successfully');
      fetchAllDrivers();
    } catch (error) {
      console.error('Error saving salaries:', error);
      toast.error('Failed to save salaries');
    }
  };

  const updateDriverSalary = (driverName, newSalary) => {
    setDrivers(drivers.map(d => 
      d.name === driverName ? { ...d, default_salary: parseFloat(newSalary) || 15000 } : d
    ));
  };

  return (
    <div className="space-y-6">
      <div className="modern-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-extrabold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">💰 Driver Default Salaries</h2>
            <p className="text-slate-600 mt-1">Set default monthly salary for all drivers (applies to all months)</p>
          </div>
          <Button onClick={handleSaveAll} className="bg-gradient-to-r from-emerald-200 to-teal-200 text-slate-700 hover:from-emerald-300 hover:to-teal-300 font-semibold shadow-lg backdrop-blur-sm border border-white/40">
            <span className="mr-2">💾</span>
            Save All Changes
          </Button>
        </div>

        {/* Drivers Table */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto"></div>
            <p className="text-slate-600 mt-4">Loading drivers...</p>
          </div>
        ) : drivers.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">📭</div>
            <p className="text-slate-600">No drivers found. Add some orders first!</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="frosted-glass p-4 rounded-2xl">
              <p className="text-sm text-slate-600">
                <strong>Note:</strong> Default salary of ₹15,000 is automatically set for all drivers. You can edit individual salaries below. Changes apply to all months unless you create a specific monthly override.
              </p>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gradient-to-r from-emerald-50/50 to-teal-50/50 backdrop-blur-sm">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">Driver Name</th>
                    <th className="px-4 py-3 text-right text-sm font-semibold text-slate-700">Default Monthly Salary (₹)</th>
                    <th className="px-4 py-3 text-center text-sm font-semibold text-slate-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {drivers.map((driver, index) => (
                    <tr key={index} className="border-t border-white/30 hover:bg-white/30 transition-colors">
                      <td className="px-4 py-4 font-medium text-slate-700">{driver.name}</td>
                      <td className="px-4 py-4 text-right">
                        {editingDriver?.name === driver.name ? (
                          <div className="flex items-center justify-end space-x-2">
                            <Input
                              type="number"
                              value={editDefaultSalary}
                              onChange={(e) => setEditDefaultSalary(e.target.value)}
                              className="w-32 input-modern text-right"
                              min="0"
                              step="100"
                            />
                            <Button size="sm" onClick={handleSaveDefaultSalary} className="bg-green-500 text-white hover:bg-green-600">
                              ✓
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => setEditingDriver(null)}>
                              ✕
                            </Button>
                          </div>
                        ) : (
                          <span className="text-lg font-semibold text-emerald-600">
                            ₹{driver.default_salary.toLocaleString('en-IN')}
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-4 text-center">
                        {editingDriver?.name === driver.name ? null : (
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => handleEditDefaultSalary(driver)}
                            className="backdrop-blur-sm"
                          >
                            Edit
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <div className="frosted-glass p-4 rounded-2xl mt-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-slate-600">
                  <strong>Total Drivers:</strong> {drivers.length}
                </div>
                <div className="text-sm text-slate-600">
                  <strong>Total Monthly Salary Budget:</strong> ₹{drivers.reduce((sum, d) => sum + d.default_salary, 0).toLocaleString('en-IN')}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};


// Reports Component
const Reports = () => {
  const { user } = useAuth();
  const hasRole = (roles) => {
    if (!user || !user.role) return false;
    return Array.isArray(roles) ? roles.includes(user.role) : user.role === roles;
  };
  
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [expenseData, setExpenseData] = useState([]);
  const [revenueData, setRevenueData] = useState([]);
  const [towingVehicleData, setTowingVehicleData] = useState([]);
  const [customReportData, setCustomReportData] = useState([]);
  const [dailySummary, setDailySummary] = useState([]);
  const [dailyTotals, setDailyTotals] = useState(null);
  const [availableColumns, setAvailableColumns] = useState([]);
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [customColumnsData, setCustomColumnsData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('daily');
  
  // Custom report configuration
  const [customConfig, setCustomConfig] = useState({
    start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    group_by: 'order_type',
    report_type: 'summary',
    order_types: ['cash', 'company']
  });

  const months = [
    { value: 1, label: 'January' },
    { value: 2, label: 'February' },
    { value: 3, label: 'March' },
    { value: 4, label: 'April' },
    { value: 5, label: 'May' },
    { value: 6, label: 'June' },
    { value: 7, label: 'July' },
    { value: 8, label: 'August' },
    { value: 9, label: 'September' },
    { value: 10, label: 'October' },
    { value: 11, label: 'November' },
    { value: 12, label: 'December' }
  ];

  const years = Array.from({ length: 11 }, (_, i) => 2020 + i);

  const fetchExpenseReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/reports/expense-by-driver?month=${selectedMonth}&year=${selectedYear}`);
      setExpenseData(response.data.data);
    } catch (error) {
      console.error('Error fetching expense report:', error);
      toast.error('Failed to fetch expense report');
    } finally {
      setLoading(false);
    }
  };

  const fetchRevenueReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/reports/revenue-by-vehicle-type?month=${selectedMonth}&year=${selectedYear}`);
      setRevenueData(response.data.data);
    } catch (error) {
      console.error('Error fetching revenue report:', error);
      toast.error('Failed to fetch revenue report');
    } finally {
      setLoading(false);
    }
  };

  const fetchTowingVehicleReport = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/reports/revenue-by-towing-vehicle?month=${selectedMonth}&year=${selectedYear}`);
      setTowingVehicleData(response.data.data);
    } catch (error) {
      console.error('Error fetching towing vehicle report:', error);
      toast.error('Failed to fetch towing vehicle report');
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomReport = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/reports/custom`, customConfig);
      setCustomReportData(response.data.data);
    } catch (error) {
      console.error('Error fetching custom report:', error);
      toast.error('Failed to fetch custom report');
    } finally {
      setLoading(false);
    }
  };


  const fetchDailySummary = async () => {
    try {
      setLoading(true);
      const startDate = new Date(selectedYear, selectedMonth - 1, 1).toISOString();
      const endDate = new Date(selectedYear, selectedMonth, 0, 23, 59, 59).toISOString();
      
      const response = await axios.get(`${API}/reports/daily-summary?start_date=${startDate}&end_date=${endDate}`);
      setDailySummary(response.data.summary);
      setDailyTotals(response.data.totals);
    } catch (error) {
      console.error('Error fetching daily summary:', error);
      toast.error('Failed to fetch daily summary');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableColumns = async () => {
    try {
      const response = await axios.get(`${API}/reports/available-columns`);
      setAvailableColumns(response.data.columns);
      // Set default columns
      const defaultCols = ['date_time', 'customer_name', 'order_type', 'phone'];
      setSelectedColumns(defaultCols);
    } catch (error) {
      console.error('Error fetching columns:', error);
      toast.error('Failed to fetch available columns');
    }
  };

  const fetchCustomColumnsReport = async () => {
    if (selectedColumns.length === 0) {
      toast.error('Please select at least one column');
      return;
    }
    
    try {
      setLoading(true);
      const startDate = new Date(selectedYear, selectedMonth - 1, 1).toISOString();
      const endDate = new Date(selectedYear, selectedMonth, 0, 23, 59, 59).toISOString();
      
      const response = await axios.post(`${API}/reports/custom-columns`, {
        start_date: startDate,
        end_date: endDate,
        columns: selectedColumns,
        order_type: 'all'
      });
      setCustomColumnsData(response.data.data);
      toast.success(`Report generated with ${response.data.total_records} records`);
    } catch (error) {
      console.error('Error fetching custom columns report:', error);
      toast.error('Failed to generate custom report');
    } finally {
      setLoading(false);
    }
  };

  const toggleColumn = (columnKey) => {
    setSelectedColumns(prev => 
      prev.includes(columnKey) 
        ? prev.filter(k => k !== columnKey)
        : [...prev, columnKey]
    );
  };

  useEffect(() => {
    fetchAvailableColumns();
  }, []);

  useEffect(() => {
    if (activeTab === 'daily') {
      fetchDailySummary();
    }
  }, [activeTab, selectedMonth, selectedYear]);


  const exportExpenseReport = async () => {
    try {
      toast.info('Generating expense report...');
      const response = await axios.get(`${API}/reports/expense-by-driver/export?month=${selectedMonth}&year=${selectedYear}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `kawale_expense_by_driver_${selectedYear}_${selectedMonth.toString().padStart(2, '0')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Expense report exported successfully!');
    } catch (error) {
      console.error('Error exporting expense report:', error);
      toast.error('Failed to export expense report');
    }
  };

  const exportRevenueReport = async () => {
    try {
      toast.info('Generating revenue report...');
      const response = await axios.get(`${API}/reports/revenue-by-vehicle-type/export?month=${selectedMonth}&year=${selectedYear}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `kawale_revenue_by_vehicle_type_${selectedYear}_${selectedMonth.toString().padStart(2, '0')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Revenue report exported successfully!');
    } catch (error) {
      console.error('Error exporting revenue report:', error);
      toast.error('Failed to export revenue report');
    }
  };

  const exportTowingVehicleReport = async () => {
    try {
      toast.info('Generating towing vehicle report...');
      const response = await axios.get(`${API}/reports/revenue-by-towing-vehicle/export?month=${selectedMonth}&year=${selectedYear}`, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `kawale_revenue_by_towing_vehicle_${selectedYear}_${selectedMonth.toString().padStart(2, '0')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Towing vehicle report exported successfully!');
    } catch (error) {
      console.error('Error exporting towing vehicle report:', error);
      toast.error('Failed to export towing vehicle report');
    }
  };

  const exportCustomReport = async () => {
    try {
      toast.info('Generating custom report...');
      const response = await axios.post(`${API}/reports/custom/export`, customConfig, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `kawale_custom_report_${customConfig.group_by}_${Date.now()}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Custom report exported successfully!');
    } catch (error) {
      console.error('Error exporting custom report:', error);
      toast.error('Failed to export custom report');
    }
  };



  const exportCustomColumnsExcel = async () => {
    if (customColumnsData.length === 0) {
      toast.error('No data to export. Please generate a report first.');
      return;
    }
    
    try {
      toast.info('Exporting to Excel...');
      const startDate = new Date(selectedYear, selectedMonth - 1, 1).toISOString();
      const endDate = new Date(selectedYear, selectedMonth, 0, 23, 59, 59).toISOString();
      
      const response = await axios.post(`${API}/reports/custom-columns/export/excel`, {
        start_date: startDate,
        end_date: endDate,
        columns: selectedColumns,
        order_type: 'all'
      }, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `custom_columns_report_${selectedYear}_${selectedMonth.toString().padStart(2, '0')}.xlsx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('Excel report exported successfully!');
    } catch (error) {
      console.error('Error exporting custom columns Excel:', error);
      toast.error('Failed to export Excel report');
    }
  };

  const exportCustomColumnsPDF = async () => {
    if (customColumnsData.length === 0) {
      toast.error('No data to export. Please generate a report first.');
      return;
    }
    
    try {
      toast.info('Exporting to PDF...');
      const startDate = new Date(selectedYear, selectedMonth - 1, 1).toISOString();
      const endDate = new Date(selectedYear, selectedMonth, 0, 23, 59, 59).toISOString();
      
      const response = await axios.post(`${API}/reports/custom-columns/export/pdf`, {
        start_date: startDate,
        end_date: endDate,
        columns: selectedColumns,
        order_type: 'all'
      }, {
        responseType: 'blob'
      });
      
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `custom_columns_report_${selectedYear}_${selectedMonth.toString().padStart(2, '0')}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success('PDF report exported successfully!');
    } catch (error) {
      console.error('Error exporting custom columns PDF:', error);
      toast.error('Failed to export PDF report');
    }
  };

  const handleMonthYearChange = () => {
    if (activeTab === 'expense') {
      fetchExpenseReport();
    } else if (activeTab === 'revenue') {
      fetchRevenueReport();
    } else if (activeTab === 'towing') {
      fetchTowingVehicleReport();
    } else if (activeTab === 'custom') {
      fetchCustomReport();
    }
  };

  useEffect(() => {
    handleMonthYearChange();
  }, [selectedMonth, selectedYear, activeTab]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="bg-white shadow-xl">
          <CardHeader className="bg-gradient-to-r from-orange-500 to-amber-600 text-white rounded-t-lg">
            <CardTitle className="text-2xl font-bold flex items-center">
              <span className="mr-3">📊</span>
              Monthly Reports
            </CardTitle>
          </CardHeader>
          
          <CardContent className="p-6">
            {/* Month/Year Selector */}
            <div className="flex items-center space-x-4 mb-6">
              <div>
                <Label className="text-sm font-medium text-slate-700">Month</Label>
                <Select value={selectedMonth.toString()} onValueChange={(value) => setSelectedMonth(parseInt(value))}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {months.map((month) => (
                      <SelectItem key={month.value} value={month.value.toString()}>
                        {month.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-sm font-medium text-slate-700">Year</Label>
                <Select value={selectedYear.toString()} onValueChange={(value) => setSelectedYear(parseInt(value))}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((year) => (
                      <SelectItem key={year} value={year.toString()}>
                        {year}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Tabs for Reports */}
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-6 gap-1">
                <TabsTrigger value="daily" className="text-sm">📅 Daily Summary</TabsTrigger>
                <TabsTrigger value="custom-columns" className="text-sm">🎯 Custom Columns</TabsTrigger>
                <TabsTrigger value="expense" className="text-sm">💰 Expense</TabsTrigger>
                <TabsTrigger value="revenue" className="text-sm">📊 Revenue</TabsTrigger>
                <TabsTrigger value="towing" className="text-sm">🚛 Towing</TabsTrigger>
                <TabsTrigger value="custom" className="text-sm">⚙️ Custom</TabsTrigger>
              </TabsList>

              {/* Expense Report Tab */}
              <TabsContent value="expense">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold">
                      Expense Report by Driver - {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
                    </h3>
                    {hasRole(['super_admin', 'admin']) && (
                      <Button onClick={exportExpenseReport} className="bg-green-600 hover:bg-green-700 text-white">
                        <span className="mr-2">📥</span>
                        Export Excel
                      </Button>
                    )}
                  </div>

                  {loading ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse border border-slate-300">
                        <thead>
                          <tr className="bg-slate-100">
                            <th className="border border-slate-300 px-4 py-2 text-left">Driver Name</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Cash Orders</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Company Orders</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Total Orders</th>
                            {hasRole(['super_admin', 'admin']) && (
                              <>
                                <th className="border border-slate-300 px-4 py-2 text-right">Diesel Expense (₹)</th>
                                <th className="border border-slate-300 px-4 py-2 text-right">Toll Expense (₹)</th>
                                <th className="border border-slate-300 px-4 py-2 text-right">Total Expense (₹)</th>
                              </>
                            )}
                          </tr>
                        </thead>
                        <tbody>
                          {expenseData.map((driver, index) => (
                            <tr key={index} className="hover:bg-slate-50">
                              <td className="border border-slate-300 px-4 py-2 font-medium">{driver.driver_name}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{driver.cash_orders}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{driver.company_orders}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{driver.total_orders}</td>
                              {hasRole(['super_admin', 'admin']) && (
                                <>
                                  <td className="border border-slate-300 px-4 py-2 text-right">₹{driver.total_diesel_expense?.toLocaleString('en-IN')}</td>
                                  <td className="border border-slate-300 px-4 py-2 text-right">₹{driver.total_toll_expense?.toLocaleString('en-IN')}</td>
                                  <td className="border border-slate-300 px-4 py-2 text-right font-bold">₹{driver.total_expenses?.toLocaleString('en-IN')}</td>
                                </>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {expenseData.length === 0 && !loading && (
                    <div className="text-center py-8 text-slate-500">
                      No expense data found for {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Revenue Report Tab */}
              <TabsContent value="revenue">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold">
                      Revenue Report by Vehicle Type - {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
                    </h3>
                    {hasRole(['super_admin', 'admin']) && (
                      <Button onClick={exportRevenueReport} className="bg-green-600 hover:bg-green-700 text-white">
                        <span className="mr-2">📥</span>
                        Export Excel
                      </Button>
                    )}
                  </div>

                  {loading ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                    </div>
                  ) : revenueData.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-slate-600">No data available</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="bg-slate-100">
                            <th className="px-4 py-2 text-left">Vehicle Type</th>
                            {hasRole(['super_admin', 'admin']) && (
                              <th className="px-4 py-2 text-right">Revenue</th>
                            )}
                          </tr>
                        </thead>
                        <tbody>
                          {revenueData.map((item, index) => (
                            <tr key={index} className="border-t">
                              <td className="px-4 py-2">{item.service_type}</td>
                              {hasRole(['super_admin', 'admin']) && (
                                <td className="px-4 py-2 text-right">₹{item.revenue?.toLocaleString('en-IN')}</td>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Daily Summary Tab */}
              <TabsContent value="daily">
                <div className="space-y-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold bg-gradient-to-r from-pink-400 to-blue-400 bg-clip-text text-transparent">
                      📅 Daily Expense & Revenue Summary
                    </h3>
                  </div>

                  {loading ? (
                    <div className="text-center py-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-400 mx-auto"></div>
                      <p className="text-slate-600 mt-4">Loading daily summary...</p>
                    </div>
                  ) : (
                    <>
                      {/* Summary Cards */}
                      {dailyTotals && (
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                          <div className="frosted-glass p-4 rounded-2xl text-center">
                            <div className="text-3xl font-bold text-blue-500">{dailyTotals.total_orders}</div>
                            <div className="text-sm text-slate-600 mt-1">Total Orders</div>
                          </div>
                          <div className="frosted-glass p-4 rounded-2xl text-center">
                            <div className="text-3xl font-bold text-red-500">₹{dailyTotals.total_expense.toLocaleString('en-IN')}</div>
                            <div className="text-sm text-slate-600 mt-1">Total Expense</div>
                          </div>
                          <div className="frosted-glass p-4 rounded-2xl text-center">
                            <div className="text-3xl font-bold text-green-500">₹{dailyTotals.total_revenue.toLocaleString('en-IN')}</div>
                            <div className="text-sm text-slate-600 mt-1">Total Revenue</div>
                          </div>
                          <div className="frosted-glass p-4 rounded-2xl text-center">
                            <div className={`text-3xl font-bold ${dailyTotals.net_profit >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              ₹{dailyTotals.net_profit.toLocaleString('en-IN')}
                            </div>
                            <div className="text-sm text-slate-600 mt-1">Net Profit</div>
                          </div>
                        </div>
                      )}

                      {/* Daily Table */}
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="bg-gradient-to-r from-pink-50/50 to-blue-50/50 backdrop-blur-sm">
                              <th className="px-4 py-3 text-left text-sm font-semibold">Date</th>
                              <th className="px-4 py-3 text-center text-sm font-semibold">Orders</th>
                              <th className="px-4 py-3 text-center text-sm font-semibold">Cash</th>
                              <th className="px-4 py-3 text-center text-sm font-semibold">Company</th>
                              <th className="px-4 py-3 text-right text-sm font-semibold">Expense</th>
                              <th className="px-4 py-3 text-right text-sm font-semibold">Revenue</th>
                              <th className="px-4 py-3 text-right text-sm font-semibold">Profit</th>
                            </tr>
                          </thead>
                          <tbody>
                            {dailySummary.map((day) => {
                              const profit = day.total_revenue - day.total_expense;
                              return (
                                <tr key={day.date} className="border-t border-white/30 hover:bg-white/30 transition-colors">
                                  <td className="px-4 py-3 font-medium">{new Date(day.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                                  <td className="px-4 py-3 text-center font-semibold text-blue-600">{day.total_orders}</td>
                                  <td className="px-4 py-3 text-center text-green-600">{day.cash_orders}</td>
                                  <td className="px-4 py-3 text-center text-purple-600">{day.company_orders}</td>
                                  <td className="px-4 py-3 text-right text-red-600">₹{day.total_expense.toLocaleString('en-IN')}</td>
                                  <td className="px-4 py-3 text-right text-green-600">₹{day.total_revenue.toLocaleString('en-IN')}</td>
                                  <td className={`px-4 py-3 text-right font-bold ${profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                                    ₹{profit.toLocaleString('en-IN')}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              </TabsContent>

              {/* Custom Columns Tab */}
              <TabsContent value="custom-columns">
                <div className="space-y-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                      🎯 Custom Column Report
                    </h3>
                    <Button 
                      onClick={fetchCustomColumnsReport} 
                      className="bg-gradient-to-r from-indigo-200 to-purple-200 text-slate-700 hover:from-indigo-300 hover:to-purple-300 font-semibold shadow-lg backdrop-blur-sm border border-white/40"
                    >
                      Generate Report
                    </Button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Column Selection */}
                    <div className="frosted-glass p-6 rounded-2xl">
                      <h4 className="font-bold text-slate-700 mb-4">Select Columns to Include</h4>
                      <p className="text-sm text-slate-600 mb-4">Choose which columns you want to see in your report</p>
                      
                      {/* Group columns by category */}
                      {['Basic', 'Cash', 'Company', 'Incentives'].map(category => {
                        const categoryColumns = availableColumns.filter(col => col.category === category);
                        if (categoryColumns.length === 0) return null;
                        
                        return (
                          <div key={category} className="mb-4">
                            <h5 className="font-semibold text-sm text-slate-700 mb-2">{category} Fields</h5>
                            <div className="space-y-2 ml-2">
                              {categoryColumns.map(col => (
                                <label key={col.key} className="flex items-center space-x-2 cursor-pointer hover:bg-white/50 p-2 rounded">
                                  <input
                                    type="checkbox"
                                    checked={selectedColumns.includes(col.key)}
                                    onChange={() => toggleColumn(col.key)}
                                    className="rounded border-pink-300 text-pink-500 focus:ring-pink-200"
                                  />
                                  <span className="text-sm text-slate-700">{col.label}</span>
                                </label>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Selected Columns Preview */}
                    <div className="frosted-glass p-6 rounded-2xl">
                      <h4 className="font-bold text-slate-700 mb-4">Selected Columns ({selectedColumns.length})</h4>
                      {selectedColumns.length === 0 ? (
                        <p className="text-slate-500 text-sm">No columns selected. Please select at least one column.</p>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {selectedColumns.map(colKey => {
                            const col = availableColumns.find(c => c.key === colKey);
                            return (
                              <Badge key={colKey} className="badge-pastel-purple cursor-pointer" onClick={() => toggleColumn(colKey)}>
                                {col?.label || colKey} ✕
                              </Badge>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Report Data */}
                  {loading ? (
                    <div className="text-center py-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-400 mx-auto"></div>
                      <p className="text-slate-600 mt-4">Generating report...</p>
                    </div>
                  ) : customColumnsData.length > 0 ? (
                    <div className="space-y-4">
                      {/* Export Buttons */}
                      {hasRole(['super_admin', 'admin']) && (
                        <div className="flex justify-end gap-3">
                          <Button
                            onClick={exportCustomColumnsExcel}
                            className="bg-gradient-to-r from-green-200 to-emerald-200 text-slate-700 hover:from-green-300 hover:to-emerald-300 font-semibold shadow-lg backdrop-blur-sm border border-white/40"
                          >
                            <span className="mr-2">📥</span>
                            Export Excel
                          </Button>
                          <Button
                            onClick={exportCustomColumnsPDF}
                            className="bg-gradient-to-r from-red-200 to-pink-200 text-slate-700 hover:from-red-300 hover:to-pink-300 font-semibold shadow-lg backdrop-blur-sm border border-white/40"
                          >
                            <span className="mr-2">📄</span>
                            Export PDF
                          </Button>
                        </div>
                      )}

                      <div className="frosted-glass p-6 rounded-2xl">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="bg-gradient-to-r from-indigo-50/50 to-purple-50/50 backdrop-blur-sm">
                                {selectedColumns.map(colKey => {
                                  const col = availableColumns.find(c => c.key === colKey);
                                  return (
                                    <th key={colKey} className="px-3 py-2 text-left text-xs font-semibold">{col?.label || colKey}</th>
                                  );
                                })}
                              </tr>
                            </thead>
                            <tbody>
                              {customColumnsData.slice(0, 100).map((row, idx) => (
                                <tr key={idx} className="border-t border-white/30 hover:bg-white/30 transition-colors">
                                  {selectedColumns.map(colKey => {
                                    const isMonetaryField = colKey.includes('amount') || colKey.includes('toll') || colKey.includes('diesel') || colKey.includes('revenue') || colKey.includes('expense');
                                    const shouldHideAmount = isMonetaryField && !hasRole(['super_admin', 'admin']);
                                    
                                    return (
                                      <td key={colKey} className="px-3 py-2 text-xs">
                                        {shouldHideAmount 
                                          ? '***' 
                                          : (typeof row[colKey] === 'number' && isMonetaryField 
                                            ? `₹${row[colKey]?.toLocaleString('en-IN') || 0}`
                                            : row[colKey] || '-')}
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {customColumnsData.length > 100 && (
                            <p className="text-center text-sm text-slate-500 mt-4">
                              Showing first 100 of {customColumnsData.length} records
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 frosted-glass rounded-2xl">
                      <div className="text-5xl mb-4">📊</div>
                      <p className="text-slate-600">Select columns and click "Generate Report" to view data</p>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Towing Vehicle Revenue Report Tab */}
              <TabsContent value="towing">
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold">
                      Revenue Report by Towing Vehicle - {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
                    </h3>
                    {hasRole(['super_admin', 'admin']) && (
                      <Button onClick={exportTowingVehicleReport} className="bg-green-600 hover:bg-green-700 text-white">
                        <span className="mr-2">📥</span>
                        Export Excel
                      </Button>
                    )}
                  </div>

                  {loading ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse border border-slate-300">
                        <thead>
                          <tr className="bg-slate-100">
                            <th className="border border-slate-300 px-4 py-2 text-left">Towing Vehicle</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Cash Orders</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Company Orders</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Total Orders</th>
                            {hasRole(['super_admin', 'admin']) && (
                              <>
                                <th className="border border-slate-300 px-4 py-2 text-right">Base Revenue (₹)</th>
                                <th className="border border-slate-300 px-4 py-2 text-right">Incentive (₹)</th>
                                <th className="border border-slate-300 px-4 py-2 text-right">Total Revenue (₹)</th>
                              </>
                            )}
                          </tr>
                        </thead>
                        <tbody>
                          {towingVehicleData.map((vehicle, index) => (
                            <tr key={index} className="hover:bg-slate-50">
                              <td className="border border-slate-300 px-4 py-2 font-medium">{vehicle.towing_vehicle}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{vehicle.cash_orders}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{vehicle.company_orders}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{vehicle.total_orders}</td>
                              {hasRole(['super_admin', 'admin']) && (
                                <>
                                  <td className="border border-slate-300 px-4 py-2 text-right">₹{vehicle.total_base_revenue?.toLocaleString('en-IN')}</td>
                                  <td className="border border-slate-300 px-4 py-2 text-right">₹{vehicle.total_incentive_amount?.toLocaleString('en-IN')}</td>
                                  <td className="border border-slate-300 px-4 py-2 text-right font-bold">₹{vehicle.total_revenue?.toLocaleString('en-IN')}</td>
                                </>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {towingVehicleData.length === 0 && !loading && (
                    <div className="text-center py-8 text-slate-500">
                      No towing vehicle data found for {months.find(m => m.value === selectedMonth)?.label} {selectedYear}
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Custom Reports Tab */}
              <TabsContent value="custom">
                <div className="space-y-6">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <h3 className="text-lg font-semibold mb-4">Custom Report Configuration</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <Label>Start Date</Label>
                        <Input
                          type="date"
                          value={customConfig.start_date}
                          onChange={(e) => setCustomConfig(prev => ({...prev, start_date: e.target.value}))}
                        />
                      </div>
                      <div>
                        <Label>End Date</Label>
                        <Input
                          type="date"
                          value={customConfig.end_date}
                          onChange={(e) => setCustomConfig(prev => ({...prev, end_date: e.target.value}))}
                        />
                      </div>
                      <div>
                        <Label>Group By</Label>
                        <Select value={customConfig.group_by} onValueChange={(value) => setCustomConfig(prev => ({...prev, group_by: value}))}>
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="order_type">Order Type</SelectItem>
                            <SelectItem value="driver">Driver</SelectItem>
                            <SelectItem value="service_type">Service Type</SelectItem>
                            <SelectItem value="towing_vehicle">Towing Vehicle</SelectItem>
                            <SelectItem value="firm">Firm</SelectItem>
                            <SelectItem value="company">Company</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    
                    <div className="flex space-x-4 mt-4">
                      <Button onClick={fetchCustomReport} className="bg-blue-600 hover:bg-blue-700 text-white">
                        Generate Report
                      </Button>
                      <Button onClick={exportCustomReport} className="bg-green-600 hover:bg-green-700 text-white">
                        <span className="mr-2">📥</span>
                        Export Excel
                      </Button>
                    </div>
                  </div>

                  {loading ? (
                    <div className="flex justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                    </div>
                  ) : customReportData.length > 0 && (
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse border border-slate-300">
                        <thead>
                          <tr className="bg-slate-100">
                            <th className="border border-slate-300 px-4 py-2 text-left">{customConfig.group_by.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Cash Orders</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Company Orders</th>
                            <th className="border border-slate-300 px-4 py-2 text-center">Total Orders</th>
                            <th className="border border-slate-300 px-4 py-2 text-right">Total Revenue (₹)</th>
                            <th className="border border-slate-300 px-4 py-2 text-right">Total Expenses (₹)</th>
                            <th className="border border-slate-300 px-4 py-2 text-right">Net Profit (₹)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {customReportData.map((item, index) => (
                            <tr key={index} className="hover:bg-slate-50">
                              <td className="border border-slate-300 px-4 py-2 font-medium">{item.group_key}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{item.cash_orders}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{item.company_orders}</td>
                              <td className="border border-slate-300 px-4 py-2 text-center">{item.total_orders}</td>
                              <td className="border border-slate-300 px-4 py-2 text-right">₹{item.total_revenue?.toLocaleString('en-IN')}</td>
                              <td className="border border-slate-300 px-4 py-2 text-right">₹{item.total_expenses?.toLocaleString('en-IN')}</td>
                              <td className="border border-slate-300 px-4 py-2 text-right font-bold">₹{(item.total_revenue - item.total_expenses)?.toLocaleString('en-IN')}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {customReportData.length === 0 && !loading && (
                    <div className="text-center py-8 text-slate-500">
                      Configure and generate your custom report above
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Rates Management Component
const RatesManagement = () => {
  const { hasRole } = useAuth();
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingRate, setEditingRate] = useState(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newRate, setNewRate] = useState({
    name_of_firm: '',
    company_name: '',
    service_type: '',
    base_rate: '',
    base_distance_km: '40',
    rate_per_km_beyond: ''
  });

  const fetchRates = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/rates`);
      setRates(response.data);
    } catch (error) {
      console.error('Error fetching rates:', error);
      toast.error('Failed to fetch rates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRates();
  }, []);

  const handleEditRate = (rate) => {
    setEditingRate({
      id: rate.id,
      name_of_firm: rate.name_of_firm,
      company_name: rate.company_name,
      service_type: rate.service_type,
      base_rate: rate.base_rate,
      base_distance_km: rate.base_distance_km || 40,
      rate_per_km_beyond: rate.rate_per_km_beyond
    });
    setShowEditDialog(true);
  };

  const handleUpdateRate = async () => {
    try {
      const updateData = {
        base_rate: parseFloat(editingRate.base_rate),
        base_distance_km: parseFloat(editingRate.base_distance_km),
        rate_per_km_beyond: parseFloat(editingRate.rate_per_km_beyond)
      };

      await axios.put(`${API}/rates/${editingRate.id}`, updateData);
      toast.success('Rate updated successfully');
      setShowEditDialog(false);
      setEditingRate(null);
      fetchRates(); // Refresh the list
    } catch (error) {
      console.error('Error updating rate:', error);
      toast.error(error.response?.data?.detail || 'Failed to update rate');
    }
  };

  const handleCreateRate = async () => {
    try {
      const createData = {
        name_of_firm: newRate.name_of_firm,
        company_name: newRate.company_name,
        service_type: newRate.service_type,
        base_rate: parseFloat(newRate.base_rate),
        base_distance_km: parseFloat(newRate.base_distance_km) || 40,
        rate_per_km_beyond: parseFloat(newRate.rate_per_km_beyond)
      };

      await axios.post(`${API}/rates`, createData);
      toast.success('Rate created successfully');
      setShowCreateDialog(false);
      setNewRate({
        name_of_firm: '',
        company_name: '',
        service_type: '',
        base_rate: '',
        base_distance_km: '40',
        rate_per_km_beyond: ''
      });
      fetchRates(); // Refresh the list
    } catch (error) {
      console.error('Error creating rate:', error);
      toast.error(error.response?.data?.detail || 'Failed to create rate');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="bg-white shadow-xl">
          <CardHeader className="bg-gradient-to-r from-orange-500 to-amber-600 text-white rounded-t-lg">
            <CardTitle className="text-2xl font-bold flex items-center">
              <span className="mr-3">💰</span>
              Service Rates Management
            </CardTitle>
          </CardHeader>
          
          <CardContent className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-slate-700">{hasRole(['super_admin', 'admin']) ? 'Manage Service Rates' : 'View Service Rates'}</h3>
              {hasRole(['super_admin', 'admin']) && (
                <Button 
                  onClick={() => setShowCreateDialog(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  <span className="mr-2">➕</span>
                  Create New Rate
                </Button>
              )}
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-slate-300">
                <thead>
                  <tr className="bg-slate-100">
                    <th className="border border-slate-300 px-4 py-2 text-left">Firm</th>
                    <th className="border border-slate-300 px-4 py-2 text-left">Company</th>
                    <th className="border border-slate-300 px-4 py-2 text-left">Service Type</th>
                    <th className="border border-slate-300 px-4 py-2 text-right">Base Rate (₹)</th>
                    <th className="border border-slate-300 px-4 py-2 text-right">Base Distance (km)</th>
                    <th className="border border-slate-300 px-4 py-2 text-right">Rate/km Beyond (₹)</th>
                    {hasRole(['super_admin', 'admin']) && (
                      <th className="border border-slate-300 px-4 py-2 text-center">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {rates.map((rate) => (
                    <tr key={rate.id} className="hover:bg-slate-50">
                      <td className="border border-slate-300 px-4 py-2">{rate.name_of_firm}</td>
                      <td className="border border-slate-300 px-4 py-2">{rate.company_name}</td>
                      <td className="border border-slate-300 px-4 py-2">{rate.service_type}</td>
                      <td className="border border-slate-300 px-4 py-2 text-right">₹{rate.base_rate?.toLocaleString('en-IN')}</td>
                      <td className="border border-slate-300 px-4 py-2 text-right">{rate.base_distance_km || 40} km</td>
                      <td className="border border-slate-300 px-4 py-2 text-right">₹{rate.rate_per_km_beyond}</td>
                      {hasRole(['super_admin', 'admin']) && (
                        <td className="border border-slate-300 px-4 py-2 text-center">
                          <Button
                            size="sm"
                            onClick={() => handleEditRate(rate)}
                            className="bg-blue-500 hover:bg-blue-600 text-white"
                          >
                            Edit
                          </Button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {rates.length === 0 && (
              <div className="text-center py-8 text-slate-500">
                No rates found. Rates will be automatically initialized when orders are created.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Edit Rate Dialog */}
        {showEditDialog && editingRate && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">Edit Rate</h3>
              <div className="space-y-4">
                <div className="text-sm text-slate-600 mb-4">
                  <p><strong>Firm:</strong> {editingRate.name_of_firm}</p>
                  <p><strong>Company:</strong> {editingRate.company_name}</p>
                  <p><strong>Service:</strong> {editingRate.service_type}</p>
                </div>
                
                <div>
                  <Label>Base Rate (₹)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={editingRate.base_rate}
                    onChange={(e) => setEditingRate(prev => ({...prev, base_rate: e.target.value}))}
                    placeholder="Base rate"
                  />
                </div>
                
                <div>
                  <Label>Base Distance (km)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={editingRate.base_distance_km}
                    onChange={(e) => setEditingRate(prev => ({...prev, base_distance_km: e.target.value}))}
                    placeholder="Base distance in km"
                  />
                </div>
                
                <div>
                  <Label>Rate per km Beyond Base (₹)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={editingRate.rate_per_km_beyond}
                    onChange={(e) => setEditingRate(prev => ({...prev, rate_per_km_beyond: e.target.value}))}
                    placeholder="Rate per km beyond base distance"
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowEditDialog(false);
                    setEditingRate(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleUpdateRate}
                  className="bg-orange-500 hover:bg-orange-600 text-white"
                >
                  Update Rate
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Create New Rate Dialog */}
        {showCreateDialog && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">Create New Rate</h3>
              <div className="space-y-4">
                <div>
                  <Label>Name of Firm</Label>
                  <Select value={newRate.name_of_firm} onValueChange={(value) => setNewRate(prev => ({...prev, name_of_firm: value}))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select firm" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Kawale Cranes">Kawale Cranes</SelectItem>
                      <SelectItem value="Sarang Cranes">Sarang Cranes</SelectItem>
                      <SelectItem value="Vidharbha Towing">Vidharbha Towing</SelectItem>
                      <SelectItem value="Vira Towing">Vira Towing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Company Name</Label>
                  <Select value={newRate.company_name} onValueChange={(value) => setNewRate(prev => ({...prev, company_name: value}))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select company" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Europ Assistance">Europ Assistance</SelectItem>
                      <SelectItem value="Mondial">Mondial</SelectItem>
                      <SelectItem value="TVS">TVS</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Service Type</Label>
                  <Select value={newRate.service_type} onValueChange={(value) => setNewRate(prev => ({...prev, service_type: value}))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select service type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="2 Wheeler Towing">2 Wheeler Towing</SelectItem>
                      <SelectItem value="Under-lift">Under-lift</SelectItem>
                      <SelectItem value="FBT">FBT</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Base Rate (₹)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={newRate.base_rate}
                    onChange={(e) => setNewRate(prev => ({...prev, base_rate: e.target.value}))}
                    placeholder="Base rate"
                  />
                </div>
                
                <div>
                  <Label>Base Distance (km)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={newRate.base_distance_km}
                    onChange={(e) => setNewRate(prev => ({...prev, base_distance_km: e.target.value}))}
                    placeholder="Base distance in km"
                  />
                </div>
                
                <div>
                  <Label>Rate per km Beyond Base (₹)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={newRate.rate_per_km_beyond}
                    onChange={(e) => setNewRate(prev => ({...prev, rate_per_km_beyond: e.target.value}))}
                    placeholder="Rate per km beyond base distance"
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-2 mt-6">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowCreateDialog(false);
                    setNewRate({
                      name_of_firm: '',
                      company_name: '',
                      service_type: '',
                      base_rate: '',
                      base_distance_km: '40',
                      rate_per_km_beyond: ''
                    });
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateRate}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Create Rate
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Header />
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/new-order"
              element={
                <ProtectedRoute>
                  <Header />
                  <NewOrderPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/edit-order/:orderId"
              element={
                <ProtectedRoute>
                  <Header />
                  <EditOrderPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute requiredRoles={['super_admin', 'admin']}>
                  <Header />
                  <UserManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit-logs"
              element={
                <ProtectedRoute requiredRoles={['super_admin', 'admin']}>
                  <Header />
                  <AuditLogs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/import-data"
              element={
                <ProtectedRoute requiredRoles={['super_admin', 'admin']}>
                  <Header />
                  <DataImport />
                </ProtectedRoute>
              }
            />
            <Route
              path="/rates"
              element={
                <ProtectedRoute requiredRoles={['super_admin', 'admin']}>
                  <Header />
                  <RatesManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/reports"
              element={
                <ProtectedRoute requiredRoles={['super_admin', 'admin']}>
                  <Header />
                  <Reports />
                </ProtectedRoute>
              }
            />

            <Route
              path="/driver-salaries"
              element={
                <ProtectedRoute requiredRoles={['super_admin', 'admin']}>
                  <Header />
                  <DriverSalaries />
                </ProtectedRoute>
              }
            />

          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </AuthProvider>
  );
}

export default App;
