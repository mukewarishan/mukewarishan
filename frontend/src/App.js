import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, useParams } from 'react-router-dom';
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

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Header Component
const Header = () => {
  return (
    <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-amber-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">🏗️</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Crane Orders</h1>
              <p className="text-slate-300 text-sm">Data Entry System</p>
            </div>
          </Link>
          <nav className="flex space-x-4">
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
          </nav>
        </div>
      </div>
    </header>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({ total_orders: 0, by_type: [] });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ order_type: '', customer_name: '', phone: '' });
  const navigate = useNavigate();

  useEffect(() => {
    fetchOrders();
    fetchStats();
  }, [filters]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.order_type) params.append('order_type', filters.order_type);
      if (filters.customer_name) params.append('customer_name', filters.customer_name);
      if (filters.phone) params.append('phone', filters.phone);
      
      const response = await axios.get(`${API}/orders?${params.toString()}`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('Failed to fetch orders');
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
    if (!window.confirm('Are you sure you want to delete this order?')) return;
    
    try {
      await axios.delete(`${API}/orders/${orderId}`);
      toast.success('Order deleted successfully');
      fetchOrders();
      fetchStats();
    } catch (error) {
      console.error('Error deleting order:', error);
      toast.error('Failed to delete order');
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
    setFilters({ order_type: '', customer_name: '', phone: '' });
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
            <CardTitle className="text-xl font-bold text-slate-900">Recent Orders</CardTitle>
            <Button 
              onClick={() => navigate('/new-order')}
              className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700"
            >
              + Add New Order
            </Button>
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
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => deleteOrder(order.id)}
                        >
                          Delete
                        </Button>
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

// Order Form Component
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
    amount_received: '',
    advance_amount: '',
    cash_kms_travelled: '',
    cash_toll: '',
    diesel: '',
    cash_diesel: '',
    cash_diesel_refill_location: '',
    
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
    company_diesel_refill_location: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');
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
      toast.error('Failed to save order');
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
                  {orderId ? 'Edit Order' : 'New Crane Order'}
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
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="vehicle">Vehicle & Trip</TabsTrigger>
                  <TabsTrigger value="costs">Costs & Charges</TabsTrigger>
                  <TabsTrigger value="additional">Additional Info</TabsTrigger>
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
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <Label htmlFor="name_of_firm" className="text-sm font-medium text-slate-700">
                          Name of Firm *
                        </Label>
                        <Input
                          id="name_of_firm"
                          value={formData.name_of_firm}
                          onChange={(e) => handleInputChange('name_of_firm', e.target.value)}
                          placeholder="Enter firm name"
                          className="mt-1"
                        />
                      </div>
                      
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
                  )}
                </TabsContent>
                
                {/* Vehicle & Trip Tab */}
                <TabsContent value="vehicle" className="space-y-6">
                  {formData.order_type === 'cash' && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-200 pb-2">
                        Cash Order - Vehicle & Trip Details
                      </h3>
                      
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
                          <Label htmlFor="cash_service_type" className="text-sm font-medium text-slate-700">
                            Service Type
                          </Label>
                          <Input
                            id="cash_service_type"
                            value={formData.cash_service_type}
                            onChange={(e) => handleInputChange('cash_service_type', e.target.value)}
                            placeholder="e.g., 2-Wheeler Crane, 4-Wheeler Crane"
                            className="mt-1"
                          />
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
                      
                      <div className="grid grid-cols-1 gap-4">
                        <div>
                          <Label htmlFor="cash_vehicle_details" className="text-sm font-medium text-slate-700">
                            Vehicle Details
                          </Label>
                          <Textarea
                            id="cash_vehicle_details"
                            value={formData.cash_vehicle_details}
                            onChange={(e) => handleInputChange('cash_vehicle_details', e.target.value)}
                            placeholder="Additional vehicle information"
                            className="mt-1"
                            rows={3}
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="cash_driver_details" className="text-sm font-medium text-slate-700">
                            Driver Details
                          </Label>
                          <Textarea
                            id="cash_driver_details"
                            value={formData.cash_driver_details}
                            onChange={(e) => handleInputChange('cash_driver_details', e.target.value)}
                            placeholder="Driver name, license, contact details"
                            className="mt-1"
                            rows={3}
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
                          <Label htmlFor="reach_time" className="text-sm font-medium text-slate-700">
                            Reach Time
                          </Label>
                          <Input
                            id="reach_time"
                            type="datetime-local"
                            value={formData.reach_time}
                            onChange={(e) => handleInputChange('reach_time', e.target.value)}
                            className="mt-1"
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="drop_time" className="text-sm font-medium text-slate-700">
                            Drop Time
                          </Label>
                          <Input
                            id="drop_time"
                            type="datetime-local"
                            value={formData.drop_time}
                            onChange={(e) => handleInputChange('drop_time', e.target.value)}
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
                          <Label htmlFor="company_service_type" className="text-sm font-medium text-slate-700">
                            Service Type
                          </Label>
                          <Input
                            id="company_service_type"
                            value={formData.company_service_type}
                            onChange={(e) => handleInputChange('company_service_type', e.target.value)}
                            placeholder="e.g., 2-Wheeler Crane, 4-Wheeler Crane"
                            className="mt-1"
                          />
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
                      </div>
                      
                      <div className="grid grid-cols-1 gap-4">
                        <div>
                          <Label htmlFor="company_vehicle_details" className="text-sm font-medium text-slate-700">
                            Vehicle Details
                          </Label>
                          <Textarea
                            id="company_vehicle_details"
                            value={formData.company_vehicle_details}
                            onChange={(e) => handleInputChange('company_vehicle_details', e.target.value)}
                            placeholder="Additional vehicle information"
                            className="mt-1"
                            rows={3}
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="company_driver_details" className="text-sm font-medium text-slate-700">
                            Driver Details
                          </Label>
                          <Textarea
                            id="company_driver_details"
                            value={formData.company_driver_details}
                            onChange={(e) => handleInputChange('company_driver_details', e.target.value)}
                            placeholder="Driver name, license, contact details"
                            className="mt-1"
                            rows={3}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </TabsContent>
                
                {/* Costs & Charges Tab */}
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
                
                {/* Additional Info Tab */}
                <TabsContent value="additional" className="space-y-6">
                  <div className="space-y-6">
                    <h3 className="text-lg font-semibold text-slate-900 border-b border-slate-200 pb-2">
                      Additional Information
                    </h3>
                    
                    {formData.order_type === 'cash' && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                          <Label htmlFor="diesel" className="text-sm font-medium text-slate-700">
                            Diesel Name/Type
                          </Label>
                          <Input
                            id="diesel"
                            value={formData.diesel}
                            onChange={(e) => handleInputChange('diesel', e.target.value)}
                            placeholder="Diesel brand or type"
                            className="mt-1"
                          />
                        </div>
                      </div>
                    )}
                    
                    {formData.order_type === 'company' && (
                      <div>
                        <Label htmlFor="company_name" className="text-sm font-medium text-slate-700">
                          Company Name (Secondary)
                        </Label>
                        <Input
                          id="company_name"
                          value={formData.company_name}
                          onChange={(e) => handleInputChange('company_name', e.target.value)}
                          placeholder="Additional company information"
                          className="mt-1"
                        />
                      </div>
                    )}
                  </div>
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
    <div className="App">
      <BrowserRouter>
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new-order" element={<NewOrderPage />} />
          <Route path="/edit-order/:orderId" element={<EditOrderPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;
