import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { useStoreContext } from '../contexts/StoreContext';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  Truck,
  User,
  MapPin,
  Clock,
  Phone,
  Mail,
  Map,
  Navigation,
  Camera,
  CheckCircle,
  XCircle,
  Users,
  Route,
  AlertCircle,
  Package,
  Eye,
  Plus
} from 'lucide-react';

// Fix leaflet icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

interface Delivery {
  id: string;
  order_id: string;
  status: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  address: {
    street: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
    notes?: string;
    location?: {
      latitude: number;
      longitude: number;
    };
  };
  assigned_to?: string;
  metrics?: {
    estimated_time?: string;
    actual_time?: string;
    distance_km?: number;
    delivery_fee: number;
    tip_amount: number;
  };
  proof?: {
    signature: boolean;
    photo: boolean;
    id_verified: boolean;
    age_verified: boolean;
  };
  created_at: string;
}

interface StaffMember {
  id: string;
  name: string;
  phone: string;
  status: string;
  current_deliveries: number;
  max_deliveries: number;
  is_available: boolean;
  can_accept: boolean;
  location?: {
    latitude: number;
    longitude: number;
  };
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  assigned: 'bg-blue-100 text-blue-800',
  accepted: 'bg-green-100 text-green-800',
  preparing: 'bg-purple-100 text-purple-800',
  ready_for_pickup: 'bg-cyan-100 text-cyan-800',
  picked_up: 'bg-indigo-100 text-indigo-800',
  en_route: 'bg-orange-100 text-orange-800',
  arrived: 'bg-amber-100 text-amber-800',
  delivering: 'bg-gray-100 text-gray-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-600'
};

export default function DeliveryManagement() {
  const queryClient = useQueryClient();
  const { currentStore } = useStoreContext();
  const [activeTab, setActiveTab] = useState('active');
  const [selectedDelivery, setSelectedDelivery] = useState<Delivery | null>(null);
  const [selectedStaff, setSelectedStaff] = useState<StaffMember | null>(null);
  const [showAssignmentModal, setShowAssignmentModal] = useState(false);
  const [showProofModal, setShowProofModal] = useState(false);
  const [batchMode, setBatchMode] = useState(false);
  const [selectedDeliveries, setSelectedDeliveries] = useState<string[]>([]);
  const [trackingData, setTrackingData] = useState<any>(null);
  const [proofData, setProofData] = useState({
    signature: '',
    photo_urls: [] as string[],
    id_verified: false,
    id_type: '',
    age_verified: false,
    notes: ''
  });

  // Fetch deliveries
  const { data: deliveries = [], isLoading: loadingDeliveries } = useQuery({
    queryKey: ['deliveries', 'active', currentStore?.id],
    queryFn: async () => {
      if (!currentStore?.id) return [];
      const response = await api.get('/api/v1/delivery/active');
      return response.data.deliveries;
    },
    enabled: !!currentStore
  });

  // Fetch staff
  const { data: staff = [], isLoading: loadingStaff } = useQuery({
    queryKey: ['staff', 'available', currentStore?.id],
    queryFn: async () => {
      if (!currentStore?.id) return [];
      const response = await api.get('/api/v1/delivery/staff/available');
      return response.data.staff;
    },
    enabled: !!currentStore
  });

  // Fetch tracking data
  const { data: tracking } = useQuery({
    queryKey: ['tracking', selectedDelivery?.id],
    queryFn: async () => {
      if (!selectedDelivery) return null;
      const response = await api.get(`/api/v1/delivery/${selectedDelivery.id}/tracking`);
      return response.data.tracking;
    },
    enabled: !!selectedDelivery && activeTab === 'tracking',
    refetchInterval: activeTab === 'tracking' ? 5000 : false
  });

  // Assign delivery mutation
  const assignMutation = useMutation({
    mutationFn: async (data: { deliveryId: string; staffId: string }) => {
      const response = await api.post(`/api/v1/delivery/${data.deliveryId}/assign`, {
        staff_id: data.staffId
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries'] });
      queryClient.invalidateQueries({ queryKey: ['staff'] });
      setShowAssignmentModal(false);
      setSelectedDelivery(null);
      setSelectedStaff(null);
    }
  });

  // Batch assign mutation
  const batchAssignMutation = useMutation({
    mutationFn: async (data: { deliveryIds: string[]; staffId: string }) => {
      const response = await api.post('/api/v1/delivery/batch-assign', {
        delivery_ids: data.deliveryIds,
        staff_id: data.staffId
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries'] });
      queryClient.invalidateQueries({ queryKey: ['staff'] });
      setShowAssignmentModal(false);
      setSelectedDeliveries([]);
      setSelectedStaff(null);
      setBatchMode(false);
    }
  });

  // Update status mutation
  const updateStatusMutation = useMutation({
    mutationFn: async (data: { deliveryId: string; status: string }) => {
      const response = await api.put(`/api/v1/delivery/${data.deliveryId}/status`, {
        status: data.status
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries'] });
    }
  });

  // Add proof mutation
  const addProofMutation = useMutation({
    mutationFn: async (data: { deliveryId: string; proof: any }) => {
      const response = await api.post(`/api/v1/delivery/${data.deliveryId}/proof`, data.proof);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries'] });
      setShowProofModal(false);
      setProofData({
        signature: '',
        photo_urls: [],
        id_verified: false,
        id_type: '',
        age_verified: false,
        notes: ''
      });
    }
  });

  const handleAssign = () => {
    if (!selectedStaff) return;

    if (batchMode && selectedDeliveries.length > 0) {
      batchAssignMutation.mutate({
        deliveryIds: selectedDeliveries,
        staffId: selectedStaff.id
      });
    } else if (selectedDelivery) {
      assignMutation.mutate({
        deliveryId: selectedDelivery.id,
        staffId: selectedStaff.id
      });
    }
  };

  const handleAddProof = () => {
    if (!selectedDelivery) return;
    addProofMutation.mutate({
      deliveryId: selectedDelivery.id,
      proof: proofData
    });
  };

  const toggleDeliverySelection = (deliveryId: string) => {
    setSelectedDeliveries(prev =>
      prev.includes(deliveryId)
        ? prev.filter(id => id !== deliveryId)
        : [...prev, deliveryId]
    );
  };

  // Early return if no store is selected
  if (!currentStore) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full">
              <Truck className="w-8 h-8 text-primary-600" />
            </div>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Store Selected</h3>
          <p className="text-gray-500">Please select a store to manage deliveries</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Delivery Management</h1>
        <p className="text-sm text-gray-500 mt-1">Managing deliveries for {currentStore.name}</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['active', 'tracking', 'staff', 'batch'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center space-x-2">
                {tab === 'active' && <Truck className="h-4 w-4" />}
                {tab === 'tracking' && <Map className="h-4 w-4" />}
                {tab === 'staff' && <Users className="h-4 w-4" />}
                {tab === 'batch' && <Route className="h-4 w-4" />}
                <span className="capitalize">{tab === 'active' ? 'Active Deliveries' : tab}</span>
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* Active Deliveries Tab */}
      {activeTab === 'active' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-medium">Active Deliveries ({deliveries.length})</h2>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={batchMode}
                  onChange={(e) => setBatchMode(e.target.checked)}
                  className="rounded text-primary-600 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700">Batch Mode</span>
              </label>
            </div>

            {loadingDeliveries ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {deliveries.map((delivery: Delivery) => (
                  <div key={delivery.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3">
                        {batchMode && (
                          <input
                            type="checkbox"
                            checked={selectedDeliveries.includes(delivery.id)}
                            onChange={() => toggleDeliverySelection(delivery.id)}
                            className="mt-1 rounded text-primary-600 focus:ring-primary-500"
                          />
                        )}
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h3 className="font-medium text-gray-900">{delivery.customer_name}</h3>
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColors[delivery.status]}`}>
                              {delivery.status.replace(/_/g, ' ')}
                            </span>
                          </div>

                          <div className="space-y-1 text-sm text-gray-600">
                            <div className="flex items-center space-x-2">
                              <MapPin className="h-4 w-4" />
                              <span>{delivery.address.street}, {delivery.address.city}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Phone className="h-4 w-4" />
                              <span>{delivery.customer_phone}</span>
                            </div>
                            {delivery.metrics?.estimated_time && (
                              <div className="flex items-center space-x-2">
                                <Clock className="h-4 w-4" />
                                <span>ETA: {new Date(delivery.metrics.estimated_time).toLocaleTimeString()}</span>
                              </div>
                            )}
                            {delivery.assigned_to && (
                              <div className="flex items-center space-x-2">
                                <User className="h-4 w-4" />
                                <span>Assigned to: {staff.find((s: StaffMember) => s.id === delivery.assigned_to)?.name || 'Unknown'}</span>
                              </div>
                            )}
                          </div>

                          <div className="flex space-x-2 mt-3">
                            {!delivery.assigned_to && (
                              <button
                                onClick={() => {
                                  setSelectedDelivery(delivery);
                                  setShowAssignmentModal(true);
                                }}
                                className="px-3 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700"
                              >
                                Assign
                              </button>
                            )}
                            <button
                              onClick={() => {
                                setSelectedDelivery(delivery);
                                setActiveTab('tracking');
                              }}
                              className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
                            >
                              Track
                            </button>
                            {delivery.status === 'arrived' && (
                              <button
                                onClick={() => {
                                  setSelectedDelivery(delivery);
                                  setShowProofModal(true);
                                }}
                                className="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"
                              >
                                Add Proof
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {batchMode && selectedDeliveries.length > 0 && (
              <button
                onClick={() => setShowAssignmentModal(true)}
                className="w-full py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
              >
                Assign {selectedDeliveries.length} Deliveries
              </button>
            )}
          </div>

          {/* Delivery Details Sidebar */}
          <div className="lg:col-span-1">
            {selectedDelivery && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-4">Delivery Details</h3>

                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500">Order ID</p>
                    <p className="text-sm font-medium">{selectedDelivery.order_id}</p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">Customer</p>
                    <p className="text-sm font-medium">{selectedDelivery.customer_name}</p>
                    <p className="text-sm text-gray-600">{selectedDelivery.customer_phone}</p>
                    {selectedDelivery.customer_email && (
                      <p className="text-sm text-gray-600">{selectedDelivery.customer_email}</p>
                    )}
                  </div>

                  <div>
                    <p className="text-xs text-gray-500">Delivery Address</p>
                    <p className="text-sm">{selectedDelivery.address.street}</p>
                    <p className="text-sm">
                      {selectedDelivery.address.city}, {selectedDelivery.address.state} {selectedDelivery.address.postal_code}
                    </p>
                    {selectedDelivery.address.notes && (
                      <p className="text-sm italic text-gray-600 mt-1">
                        Notes: {selectedDelivery.address.notes}
                      </p>
                    )}
                  </div>

                  {selectedDelivery.metrics && (
                    <div>
                      <p className="text-xs text-gray-500">Metrics</p>
                      <p className="text-sm">Delivery Fee: ${selectedDelivery.metrics.delivery_fee}</p>
                      <p className="text-sm">Tip: ${selectedDelivery.metrics.tip_amount}</p>
                      {selectedDelivery.metrics.distance_km && (
                        <p className="text-sm">Distance: {selectedDelivery.metrics.distance_km} km</p>
                      )}
                    </div>
                  )}

                  <div>
                    <p className="text-xs text-gray-500 mb-1">Update Status</p>
                    <select
                      value={selectedDelivery.status}
                      onChange={(e) => {
                        updateStatusMutation.mutate({
                          deliveryId: selectedDelivery.id,
                          status: e.target.value
                        });
                      }}
                      className="w-full text-sm border-gray-300 rounded-lg"
                    >
                      <option value="pending">Pending</option>
                      <option value="assigned">Assigned</option>
                      <option value="accepted">Accepted</option>
                      <option value="preparing">Preparing</option>
                      <option value="ready_for_pickup">Ready for Pickup</option>
                      <option value="picked_up">Picked Up</option>
                      <option value="en_route">En Route</option>
                      <option value="arrived">Arrived</option>
                      <option value="delivering">Delivering</option>
                      <option value="completed">Completed</option>
                      <option value="failed">Failed</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tracking Tab */}
      {activeTab === 'tracking' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden" style={{ height: '600px' }}>
              {selectedDelivery?.address.location ? (
                <MapContainer
                  center={[
                    selectedDelivery.address.location.latitude,
                    selectedDelivery.address.location.longitude
                  ]}
                  zoom={13}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  />
                  <Marker
                    position={[
                      selectedDelivery.address.location.latitude,
                      selectedDelivery.address.location.longitude
                    ]}
                  >
                    <Popup>
                      <div className="text-sm">
                        <p className="font-medium">{selectedDelivery.customer_name}</p>
                        <p>{selectedDelivery.address.street}</p>
                      </div>
                    </Popup>
                  </Marker>

                  {tracking?.current_location && (
                    <Marker
                      position={[
                        tracking.current_location.latitude,
                        tracking.current_location.longitude
                      ]}
                    >
                      <Popup>Driver Location</Popup>
                    </Marker>
                  )}

                  {tracking?.location_history && tracking.location_history.length > 1 && (
                    <Polyline
                      positions={tracking.location_history.map((loc: any) => [
                        loc.latitude,
                        loc.longitude
                      ])}
                      color="blue"
                    />
                  )}
                </MapContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  Select a delivery with location data to view map
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-1">
            {tracking && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-4">Tracking Information</h3>

                <div className="space-y-3">
                  {tracking.current_location && (
                    <div>
                      <p className="text-xs text-gray-500">Current Location</p>
                      <p className="text-sm">Lat: {tracking.current_location.latitude.toFixed(6)}</p>
                      <p className="text-sm">Lng: {tracking.current_location.longitude.toFixed(6)}</p>
                      {tracking.current_location.timestamp && (
                        <p className="text-sm text-gray-600">
                          Updated: {new Date(tracking.current_location.timestamp).toLocaleTimeString()}
                        </p>
                      )}
                    </div>
                  )}

                  {tracking.stats && (
                    <div>
                      <p className="text-xs text-gray-500">Statistics</p>
                      <p className="text-sm">Total Points: {tracking.stats.total_points}</p>
                      <p className="text-sm">Distance: {tracking.stats.total_distance_km} km</p>
                      <p className="text-sm">Avg Speed: {tracking.stats.avg_speed_kmh} km/h</p>
                      <p className="text-sm">Max Speed: {tracking.stats.max_speed_kmh} km/h</p>
                    </div>
                  )}

                  {tracking.estimated_arrival && (
                    <div>
                      <p className="text-xs text-gray-500">Estimated Arrival</p>
                      <p className="text-sm font-medium">
                        {new Date(tracking.estimated_arrival).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Staff Tab */}
      {activeTab === 'staff' && (
        <div>
          <h2 className="text-lg font-medium mb-4">Available Staff ({staff.length})</h2>

          {loadingStaff ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {staff.map((member: StaffMember) => (
                <div key={member.id} className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-gray-900">{member.name}</h3>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      member.is_available
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {member.status}
                    </span>
                  </div>

                  <div className="space-y-1 text-sm text-gray-600">
                    <div className="flex items-center space-x-2">
                      <Phone className="h-4 w-4" />
                      <span>{member.phone}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Truck className="h-4 w-4" />
                      <span>Active: {member.current_deliveries}/{member.max_deliveries}</span>
                    </div>
                    {member.location && (
                      <div className="flex items-center space-x-2">
                        <MapPin className="h-4 w-4" />
                        <span className="text-green-600">Location available</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Batch Operations Tab */}
      {activeTab === 'batch' && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-medium mb-4">Batch Operations</h2>
          <p className="text-gray-600 mb-4">
            Select multiple deliveries from the Active Deliveries tab to perform batch operations.
          </p>

          <div className="space-y-4">
            <div>
              <h3 className="font-medium text-gray-900">Available Operations:</h3>
              <ul className="mt-2 space-y-2">
                <li className="flex items-start">
                  <span className="block w-2 h-2 bg-primary-600 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                  <div>
                    <span className="font-medium">Batch Assignment:</span>
                    <span className="text-gray-600 ml-1">Assign multiple deliveries to a single driver</span>
                  </div>
                </li>
                <li className="flex items-start">
                  <span className="block w-2 h-2 bg-primary-600 rounded-full mt-1.5 mr-2 flex-shrink-0"></span>
                  <div>
                    <span className="font-medium">Route Optimization:</span>
                    <span className="text-gray-600 ml-1">Optimize delivery order for efficiency</span>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Assignment Modal */}
      {showAssignmentModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowAssignmentModal(false)} />

            <div className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
              <div>
                <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
                  {batchMode ? `Assign ${selectedDeliveries.length} Deliveries` : 'Assign Delivery'}
                </h3>

                <div className="mt-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Select Staff Member
                  </label>
                  <select
                    className="w-full border-gray-300 rounded-lg"
                    value={selectedStaff?.id || ''}
                    onChange={(e) => {
                      const staffMember = staff.find((s: StaffMember) => s.id === e.target.value);
                      setSelectedStaff(staffMember || null);
                    }}
                  >
                    <option value="">Choose a staff member</option>
                    {staff
                      .filter((s: StaffMember) => s.is_available && s.can_accept)
                      .map((s: StaffMember) => (
                        <option key={s.id} value={s.id}>
                          {s.name} ({s.current_deliveries}/{s.max_deliveries} deliveries)
                        </option>
                      ))}
                  </select>
                </div>
              </div>

              <div className="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
                <button
                  type="button"
                  className="inline-flex w-full justify-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:col-start-2"
                  onClick={handleAssign}
                  disabled={!selectedStaff || assignMutation.isPending || batchAssignMutation.isPending}
                >
                  {assignMutation.isPending || batchAssignMutation.isPending ? 'Assigning...' : 'Assign'}
                </button>
                <button
                  type="button"
                  className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:col-start-1 sm:mt-0"
                  onClick={() => setShowAssignmentModal(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Proof of Delivery Modal */}
      {showProofModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowProofModal(false)} />

            <div className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
              <div>
                <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">
                  Add Proof of Delivery
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Signature Data (Base64)
                    </label>
                    <textarea
                      className="w-full border-gray-300 rounded-lg"
                      rows={3}
                      value={proofData.signature}
                      onChange={(e) => setProofData({ ...proofData, signature: e.target.value })}
                    />
                  </div>

                  <div className="flex items-center space-x-4">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={proofData.id_verified}
                        onChange={(e) => setProofData({ ...proofData, id_verified: e.target.checked })}
                        className="rounded text-primary-600 focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">ID Verified</span>
                    </label>

                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={proofData.age_verified}
                        onChange={(e) => setProofData({ ...proofData, age_verified: e.target.checked })}
                        className="rounded text-primary-600 focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Age Verified (21+)</span>
                    </label>
                  </div>

                  {proofData.id_verified && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        ID Type
                      </label>
                      <input
                        type="text"
                        className="w-full border-gray-300 rounded-lg"
                        value={proofData.id_type}
                        onChange={(e) => setProofData({ ...proofData, id_type: e.target.value })}
                      />
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Notes
                    </label>
                    <textarea
                      className="w-full border-gray-300 rounded-lg"
                      rows={2}
                      value={proofData.notes}
                      onChange={(e) => setProofData({ ...proofData, notes: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
                <button
                  type="button"
                  className="inline-flex w-full justify-center rounded-md bg-primary-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:col-start-2"
                  onClick={handleAddProof}
                  disabled={addProofMutation.isPending}
                >
                  {addProofMutation.isPending ? 'Submitting...' : 'Submit'}
                </button>
                <button
                  type="button"
                  className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:col-start-1 sm:mt-0"
                  onClick={() => setShowProofModal(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}