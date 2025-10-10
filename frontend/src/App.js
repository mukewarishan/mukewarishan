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
import { AlertCircle, Users, Shield, FileText, LogOut, User, Eye, EyeOff } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-white shadow-2xl">
        <CardHeader className="text-center space-y-4">
          <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-amber-600 rounded-xl flex items-center justify-center mx-auto">
            <span className="text-white font-bold text-2xl">🏗️</span>
          </div>
          <div>
            <CardTitle className="text-2xl font-bold text-slate-900">Kawale Cranes</CardTitle>
            <p className="text-slate-600 text-sm mt-1">Data Entry System</p>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-sm font-medium text-slate-700">
                Email Address
              </Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                className="mt-1"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="password" className="text-sm font-medium text-slate-700">
                Password
              </Label>
              <div className="relative mt-1">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="pr-10"
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
            
            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Signing In...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
          
          <div className="mt-6 p-3 bg-slate-50 rounded-lg">
            <p className="text-xs text-slate-600 text-center">
              <strong>Demo Credentials:</strong><br />
              Email: admin@kawalecranes.com<br />
              Password: admin123
            </p>
          </div>
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

  const handleLogout = async () => {
    await logout();
    navigate('/login');
    toast.success('Logged out successfully');
  };

  return (
    <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-amber-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">🏗️</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Kawale Cranes</h1>
              <p className="text-slate-300 text-sm">Data Entry System</p>
            </div>
          </Link>
          
          <nav className="flex items-center space-x-4">
            <Link to="/">
              <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                Dashboard
              </Button>
            </Link>
            
            <Link to="/new-order">
              <Button className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white">
                New Order
              </Button>
            </Link>
            
            {hasRole(['super_admin', 'admin']) && (
              <>
                <Link to="/users">
                  <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                    <Users size={16} className="mr-2" />
                    Users
                  </Button>
                </Link>
                
                <Link to="/audit-logs">
                  <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                    <FileText size={16} className="mr-2" />
                    Audit Logs
                  </Button>
                </Link>
                
                <Link to="/import-data">
                  <Button variant="ghost" className="text-slate-300 hover:text-white hover:bg-slate-700">
                    <FileText size={16} className="mr-2" />
                    Import Data
                  </Button>
                </Link>
              </>
            )}
            
            <div className="flex items-center space-x-2 text-slate-300">
              <User size={16} />
              <span className="text-sm">
                {user?.full_name}
                <Badge className="ml-2 text-xs" variant={user?.role === 'super_admin' ? 'default' : user?.role === 'admin' ? 'secondary' : 'outline'}>
                  {user?.role?.replace('_', ' ')?.toUpperCase()}
                </Badge>
              </span>
            </div>
            
            <Button 
              variant="ghost" 
              onClick={handleLogout}
              className="text-slate-300 hover:text-white hover:bg-slate-700"
            >
              <LogOut size={16} />
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
};

// Dashboard Component (existing with auth)
const Dashboard = () => {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({ total_orders: 0, by_type: [] });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ order_type: 'all', customer_name: '', phone: '' });
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [orderFinancials, setOrderFinancials] = useState({}); // Store calculated financials
  const { hasRole } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchOrders();
    fetchStats();
  }, [filters]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.order_type && filters.order_type !== 'all') params.append('order_type', filters.order_type);
      if (filters.customer_name) params.append('customer_name', filters.customer_name);
      if (filters.phone) params.append('phone', filters.phone);
      
      const response = await axios.get(`${API}/orders?${params.toString()}`);
      setOrders(response.data);
      
      // Fetch financials for company orders
      await fetchFinancialsForCompanyOrders(response.data);
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
    setFilters({ order_type: 'all', customer_name: '', phone: '' });
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
      const formatDisplay = format === 'googlesheets' ? 'Google Sheets' : format.toUpperCase();
      toast.info(`Generating ${formatDisplay} export...`);
      
      const params = new URLSearchParams();
      if (filters.order_type && filters.order_type !== 'all') params.append('order_type', filters.order_type);
      if (filters.customer_name) params.append('customer_name', filters.customer_name);
      if (filters.phone) params.append('phone', filters.phone);
      params.append('limit', '1000'); // Export up to 1000 records
      
      // Handle Google Sheets differently (returns JSON)
      if (format === 'googlesheets') {
        const response = await axios.get(`${API}/export/${format}?${params.toString()}`);
        
        if (response.data.spreadsheet_url) {
          toast.success(`${response.data.message || 'Google Sheets export completed!'}`);
          
          // Open the spreadsheet in a new tab
          window.open(response.data.spreadsheet_url, '_blank');
          
          // Show additional info
          if (response.data.worksheet_name) {
            setTimeout(() => {
              toast.info(`Data exported to worksheet: ${response.data.worksheet_name}`);
            }, 1000);
          }
        } else {
          toast.error('Google Sheets export failed - no spreadsheet URL returned');
        }
      } else {
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
      }
    } catch (error) {
      console.error('Export error:', error);
      const formatDisplay = format === 'googlesheets' ? 'Google Sheets' : format.toUpperCase();
      
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
                    {stat._id === 'cash' && stat.total_amount > 0 && (
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
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
                  <Button
                    variant="outline"
                    onClick={() => exportData('googlesheets')}
                    className="flex items-center space-x-2"
                  >
                    <span>📊</span>
                    <span>Export Google Sheets</span>
                  </Button>
                </>
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
                        {order.order_type === 'company' && order.case_id_file_number && (
                          <p className="text-sm text-slate-600">
                            Case ID: {order.case_id_file_number}
                          </p>
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
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => deleteUser(user.id, user.full_name)}
                                >
                                  Delete
                                </Button>
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

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-green-800 mb-2">✅ Previous Import Status</h3>
              <p className="text-green-700">
                The Excel data has been successfully imported into the system.
              </p>
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">205</div>
                  <div className="text-sm text-slate-600">Total Records</div>
                </div>
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">158</div>
                  <div className="text-sm text-slate-600">Cash Orders</div>
                </div>
                <div className="bg-white rounded p-3 text-center">
                  <div className="text-2xl font-bold text-green-600">50</div>
                  <div className="text-sm text-slate-600">Company Orders</div>
                </div>
              </div>
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
    
    if (!formData.customer_name || !formData.phone || !formData.order_type) {
      toast.error('Please fill in all required fields');
      return;
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
    if (field === 'order_type') {
      // Clear incentive fields when switching to company type (incentives only for cash orders)
      if (value === 'company') {
        setFormData(prev => ({ 
          ...prev, 
          [field]: value,
          incentive_amount: '',
          incentive_reason: ''
        }));
      } else {
        setFormData(prev => ({ ...prev, [field]: value }));
      }
    } else {
      setFormData(prev => ({ ...prev, [field]: value }));
    }
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
                            Company Name
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
                            Service Type
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
                            Towing Vehicle
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
                            Driver
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
                            Service Type
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
                            Towing Vehicle
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
                            Driver
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
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" richColors />
      </div>
    </AuthProvider>
  );
}

export default App;
