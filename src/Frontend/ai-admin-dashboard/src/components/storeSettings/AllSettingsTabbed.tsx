import React, { useState } from 'react';
import {
  Truck, Shield, Clock, DollarSign, AlertTriangle, CreditCard, Smartphone, Plus, Trash2, Monitor, Tablet, Globe
} from 'lucide-react';
import paymentService from '../../services/paymentService';
import OnlinePaymentSettings from './OnlinePaymentSettings';

interface AllSettingsTabbedProps {
  storeId: string;
  initialSettings?: any;
  store?: any; // Add store prop to access hours
  onSave?: (category: string, settings: any) => Promise<void>;
}

interface CloverTerminal {
  id: string;
  terminalId: string;
  merchantId: string;
  name: string;
  status: 'active' | 'inactive';
  lastSeen?: string;
}

interface Device {
  id: string;
  name: string;
  platform: 'web' | 'tablet';
  appType: 'pos' | 'kiosk' | 'menu';
  deviceId: string;
  status: 'active' | 'inactive';
  lastActivity?: string;
}

const AllSettingsTabbed: React.FC<AllSettingsTabbedProps> = ({
  storeId,
  initialSettings = {},
  store,
  onSave
}) => {
  const [activeTab, setActiveTab] = useState<string>('payment');
  const [settings, setSettings] = useState(initialSettings);
  const [saving, setSaving] = useState(false);

  const tabs = [
    { id: 'payment', label: 'Payment', icon: CreditCard, color: 'text-primary-600' },
    { id: 'delivery', label: 'Delivery', icon: Truck, color: 'text-orange-600' },
    { id: 'compliance', label: 'Compliance', icon: Shield, color: 'text-danger-600' },
    { id: 'hours', label: 'Store Hours', icon: Clock, color: 'text-indigo-600' },
    { id: 'devices', label: 'Devices', icon: Smartphone, color: 'text-purple-600' },
  ];

  const handleSave = async (category: string, categorySettings: any) => {
    setSaving(true);
    try {
      if (onSave) {
        await onSave(category, categorySettings);
      }
      setSettings({ ...settings, [category]: categorySettings });
    } finally {
      setSaving(false);
    }
  };

  // Payment Settings Component
  const PaymentSettings = () => {
    const [localSettings, setLocalSettings] = useState({
      provider: 'clover',
      terminals: [] as CloverTerminal[],
      acceptedMethods: ['tap', 'chip', 'swipe', 'cash'],
      tipOptions: [15, 18, 20, 0],
      tipEnabled: true,
      ...settings.payment
    });
    const [showAddTerminal, setShowAddTerminal] = useState(false);
    const [showOnlinePaymentSettings, setShowOnlinePaymentSettings] = useState(false);
    const [newTerminal, setNewTerminal] = useState({
      terminalId: '',
      merchantId: '',
      name: ''
    });

    const addTerminal = () => {
      if (newTerminal.terminalId && newTerminal.merchantId && newTerminal.name) {
        const terminal: CloverTerminal = {
          id: `terminal_${Date.now()}`,
          terminalId: newTerminal.terminalId,
          merchantId: newTerminal.merchantId,
          name: newTerminal.name,
          status: 'active',
          lastSeen: new Date().toISOString()
        };
        setLocalSettings({
          ...localSettings,
          terminals: [...localSettings.terminals, terminal]
        });
        setNewTerminal({ terminalId: '', merchantId: '', name: '' });
        setShowAddTerminal(false);
      }
    };

    const removeTerminal = (id: string) => {
      setLocalSettings({
        ...localSettings,
        terminals: localSettings.terminals.filter((t: any) => t.id !== id)
      });
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold">Clover Payment Terminals</h3>
            </div>
            <button
              onClick={() => setShowAddTerminal(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
            >
              <Plus className="w-4 h-4" />
              Add Terminal
            </button>
          </div>

          {showAddTerminal && (
            <div className="mb-4 p-6 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3">Add Clover Terminal</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Terminal Name</label>
                  <input
                    type="text"
                    placeholder="Front Counter Terminal"
                    value={newTerminal.name}
                    onChange={(e) => setNewTerminal({...newTerminal, name: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Terminal ID</label>
                  <input
                    type="text"
                    placeholder="TERM123456"
                    value={newTerminal.terminalId}
                    onChange={(e) => setNewTerminal({...newTerminal, terminalId: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Merchant ID</label>
                  <input
                    type="text"
                    placeholder="MERCH789012"
                    value={newTerminal.merchantId}
                    onChange={(e) => setNewTerminal({...newTerminal, merchantId: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={addTerminal}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm"
                >
                  Add Terminal
                </button>
                <button
                  onClick={() => {
                    setShowAddTerminal(false);
                    setNewTerminal({ terminalId: '', merchantId: '', name: '' });
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {localSettings.terminals.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No payment terminals configured. Click "Add Terminal" to set up a Clover terminal.
              </div>
            ) : (
              localSettings.terminals.map((terminal) => (
                <div key={terminal.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium">{terminal.name}</div>
                    <div className="text-sm text-gray-600">
                      Terminal ID: {terminal.terminalId} | Merchant ID: {terminal.merchantId}
                    </div>
                    <div className="text-xs text-gray-500">
                      Status: <span className={terminal.status === 'active' ? 'text-primary-600' : 'text-danger-600'}>
                        {terminal.status}
                      </span>
                      {terminal.lastSeen && ` | Last seen: ${new Date(terminal.lastSeen).toLocaleString()}`}
                    </div>
                  </div>
                  <button
                    onClick={() => removeTerminal(terminal.id)}
                    className="p-2 text-danger-600 hover:bg-danger-50 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-5 h-5 text-accent-600" />
            <h3 className="text-lg font-semibold">Payment Methods & Tips</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Accepted Payment Methods</label>
              <div className="space-y-2">
                {['tap', 'chip', 'swipe', 'cash', 'manual_entry'].map(method => (
                  <label key={method} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={localSettings.acceptedMethods.includes(method)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setLocalSettings({
                            ...localSettings,
                            acceptedMethods: [...localSettings.acceptedMethods, method]
                          });
                        } else {
                          setLocalSettings({
                            ...localSettings,
                            acceptedMethods: localSettings.acceptedMethods.filter(m => m !== method)
                          });
                        }
                      }}
                      className="w-4 h-4 text-accent-600 rounded"
                    />
                    <span className="capitalize">{method.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="flex items-center gap-2 mb-3">
                <input
                  type="checkbox"
                  checked={localSettings.tipEnabled}
                  onChange={(e) => setLocalSettings({...localSettings, tipEnabled: e.target.checked})}
                  className="w-4 h-4 text-accent-600 rounded"
                />
                <span className="font-medium">Enable Tips</span>
              </label>

              {localSettings.tipEnabled && (
                <div>
                  <label className="block text-sm font-medium mb-2">Tip Options (%)</label>
                  <div className="flex gap-2">
                    {localSettings.tipOptions.map((tip: any, index: number) => (
                      <input
                        key={index}
                        type="number"
                        value={tip}
                        onChange={(e) => {
                          const newTips = [...localSettings.tipOptions];
                          newTips[index] = parseInt(e.target.value) || 0;
                          setLocalSettings({...localSettings, tipOptions: newTips});
                        }}
                        className="w-20 px-2 py-1 border rounded text-center"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Online Payment Settings Button */}
        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-green-600" />
                <h3 className="text-lg font-semibold">Online Payment Settings</h3>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                Configure payment processing for ecommerce orders
              </p>
            </div>
            <button
              onClick={() => setShowOnlinePaymentSettings(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
            >
              Configure Online Payments
            </button>
          </div>
        </div>

        {/* Online Payment Settings Modal */}
        {showOnlinePaymentSettings && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto m-4">
              <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
                <h2 className="text-xl font-semibold">Online Payment Configuration</h2>
                <button
                  onClick={() => setShowOnlinePaymentSettings(false)}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6">
                <OnlinePaymentSettings
                  storeId={storeId}
                  initialSettings={settings.onlinePayment || {}}
                  onSave={async (onlineSettings) => {
                    await handleSave('onlinePayment', onlineSettings);
                    setShowOnlinePaymentSettings(false);
                  }}
                />
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end">
          <button
            onClick={() => handleSave('payment', localSettings)}
            disabled={saving}
            className="px-6 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Payment Settings'}
          </button>
        </div>
      </div>
    );
  };

  // Devices Settings Component
  const DevicesSettings = () => {
    const [localSettings, setLocalSettings] = useState({
      devices: [] as Device[],
      ...settings.devices
    });
    const [showAddDevice, setShowAddDevice] = useState(false);
    const [newDevice, setNewDevice] = useState({
      name: '',
      platform: 'web' as 'web' | 'tablet',
      appType: 'pos' as 'pos' | 'kiosk' | 'menu',
      deviceId: ''
    });

    const addDevice = () => {
      if (newDevice.name && newDevice.deviceId) {
        const device: Device = {
          id: `device_${Date.now()}`,
          name: newDevice.name,
          platform: newDevice.platform,
          appType: newDevice.appType,
          deviceId: newDevice.deviceId,
          status: 'active',
          lastActivity: new Date().toISOString()
        };
        setLocalSettings({
          ...localSettings,
          devices: [...localSettings.devices, device]
        });
        setNewDevice({ name: '', platform: 'web', appType: 'pos', deviceId: '' });
        setShowAddDevice(false);
      }
    };

    const removeDevice = (id: string) => {
      setLocalSettings({
        ...localSettings,
        devices: localSettings.devices.filter(d => d.id !== id)
      });
    };

    const getDeviceIcon = (platform: string) => {
      return platform === 'tablet'
        ? <Tablet className="w-5 h-5 text-purple-600" />
        : <Monitor className="w-5 h-5 text-accent-600" />;
    };

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Smartphone className="w-5 h-5 text-purple-600" />
              <h3 className="text-lg font-semibold">Registered Devices</h3>
            </div>
            <button
              onClick={() => setShowAddDevice(true)}
              className="flex items-center gap-2 px-3 py-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
            >
              <Plus className="w-4 h-4" />
              Add Device
            </button>
          </div>

          {showAddDevice && (
            <div className="mb-4 p-6 bg-gray-50 rounded-lg">
              <h4 className="font-medium mb-3">Add Device</h4>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Device Name</label>
                  <input
                    type="text"
                    placeholder="Front Counter POS"
                    value={newDevice.name}
                    onChange={(e) => setNewDevice({...newDevice, name: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Platform</label>
                  <select
                    value={newDevice.platform}
                    onChange={(e) => setNewDevice({...newDevice, platform: e.target.value as 'web' | 'tablet'})}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="web">Web Application</option>
                    <option value="tablet">Tablet Application</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Application Type</label>
                  <select
                    value={newDevice.appType}
                    onChange={(e) => setNewDevice({...newDevice, appType: e.target.value as 'pos' | 'kiosk' | 'menu'})}
                    className="w-full px-3 py-2 border rounded-lg"
                  >
                    <option value="pos">POS (Point of Sale)</option>
                    <option value="kiosk">Kiosk (Self-Service)</option>
                    <option value="menu">Menu (Digital Display)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Device ID</label>
                  <input
                    type="text"
                    placeholder="DEV123456"
                    value={newDevice.deviceId}
                    onChange={(e) => setNewDevice({...newDevice, deviceId: e.target.value})}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={addDevice}
                  className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm"
                >
                  Add Device
                </button>
                <button
                  onClick={() => {
                    setShowAddDevice(false);
                    setNewDevice({ name: '', platform: 'web', appType: 'pos', deviceId: '' });
                  }}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {localSettings.devices.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No devices registered. Click "Add Device" to register a POS, kiosk, or tablet device.
              </div>
            ) : (
              localSettings.devices.map((device) => (
                <div key={device.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-4">
                    {getDeviceIcon(device.platform)}
                    <div>
                      <div className="font-medium">{device.name}</div>
                      <div className="text-sm text-gray-600">
                        Platform: {device.platform === 'web' ? 'Web' : 'Tablet'} |
                        App: {device.appType.toUpperCase()} |
                        Device ID: {device.deviceId}
                      </div>
                      <div className="text-xs text-gray-500">
                        Status: <span className={device.status === 'active' ? 'text-primary-600' : 'text-danger-600'}>
                          {device.status}
                        </span>
                        {device.lastActivity && ` | Last activity: ${new Date(device.lastActivity).toLocaleString()}`}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => removeDevice(device.id)}
                    className="p-2 text-danger-600 hover:bg-danger-50 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-warning-600" />
            <h3 className="text-lg font-semibold">Device Information</h3>
          </div>
          <div className="space-y-2 text-sm text-gray-600">
            <p><strong>Web Applications:</strong> Browser-based applications that run on desktop or fixed terminals</p>
            <p><strong>Tablet Applications:</strong> Mobile applications that run on tablets and handheld devices</p>
            <div className="mt-3">
              <p className="font-semibold">Application Types:</p>
              <ul className="ml-4 mt-1 space-y-1">
                <li>• <strong>POS:</strong> Point of Sale application for processing transactions</li>
                <li>• <strong>Kiosk:</strong> Self-service kiosk for customer ordering</li>
                <li>• <strong>Menu:</strong> Digital menu display for showcasing products</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={() => handleSave('devices', localSettings)}
            disabled={saving}
            className="px-6 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Device Settings'}
          </button>
        </div>
      </div>
    );
  };

  // Delivery Settings Component
  const DeliverySettings = () => {
    const [localSettings, setLocalSettings] = useState({
      deliveryFees: { base: 5.00, free_threshold: 100.00 },
      deliveryTimeSlots: ['9:00-12:00', '12:00-15:00', '15:00-18:00', '18:00-21:00'],
      minimumDeliveryOrder: 30.00,
      ...settings.delivery
    });

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <DollarSign className="w-5 h-5 text-primary-600" />
            <h3 className="text-lg font-semibold">Delivery Fees</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Base Delivery Fee</label>
              <input
                type="number"
                step="0.01"
                value={localSettings.deliveryFees.base}
                onChange={(e) => setLocalSettings({
                  ...localSettings,
                  deliveryFees: { ...localSettings.deliveryFees, base: parseFloat(e.target.value) }
                })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Free Delivery Threshold</label>
              <input
                type="number"
                step="0.01"
                value={localSettings.deliveryFees.free_threshold}
                onChange={(e) => setLocalSettings({
                  ...localSettings,
                  deliveryFees: { ...localSettings.deliveryFees, free_threshold: parseFloat(e.target.value) }
                })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Minimum Order for Delivery</label>
              <input
                type="number"
                step="0.01"
                value={localSettings.minimumDeliveryOrder}
                onChange={(e) => setLocalSettings({...localSettings, minimumDeliveryOrder: parseFloat(e.target.value)})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-accent-600" />
            <h3 className="text-lg font-semibold">Time Slots</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Delivery Time Slots</label>
              <div className="space-y-2">
                {['9:00-12:00', '12:00-15:00', '15:00-18:00', '18:00-21:00'].map(slot => (
                  <label key={slot} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={localSettings.deliveryTimeSlots.includes(slot)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setLocalSettings({
                            ...localSettings,
                            deliveryTimeSlots: [...localSettings.deliveryTimeSlots, slot]
                          });
                        } else {
                          setLocalSettings({
                            ...localSettings,
                            deliveryTimeSlots: localSettings.deliveryTimeSlots.filter(s => s !== slot)
                          });
                        }
                      }}
                      className="w-4 h-4 text-accent-600 rounded"
                    />
                    <span>{slot}</span>
                  </label>
                ))}
              </div>
            </div>

          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={() => handleSave('delivery', localSettings)}
            disabled={saving}
            className="px-6 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Delivery Settings'}
          </button>
        </div>
      </div>
    );
  };

  // Compliance Settings Component
  const ComplianceSettings = () => {
    const [localSettings, setLocalSettings] = useState({
      ageVerificationRequired: true,
      minimumAge: 19,
      dailyPurchaseLimit: 30,
      monthlyPurchaseLimit: 150,
      requireIdVerification: true,
      ...settings.compliance
    });

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-danger-600" />
            <h3 className="text-lg font-semibold">Age & ID Verification</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Minimum Age</label>
              <select
                value={localSettings.minimumAge}
                onChange={(e) => setLocalSettings({...localSettings, minimumAge: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="18">18</option>
                <option value="19">19</option>
                <option value="21">21</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={localSettings.ageVerificationRequired}
                  onChange={(e) => setLocalSettings({...localSettings, ageVerificationRequired: e.target.checked})}
                  className="w-4 h-4 text-accent-600 rounded"
                />
                <span>Require Age Verification</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={localSettings.requireIdVerification}
                  onChange={(e) => setLocalSettings({...localSettings, requireIdVerification: e.target.checked})}
                  className="w-4 h-4 text-accent-600 rounded"
                />
                <span>Require ID Verification for All Purchases</span>
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-5 h-5 text-warning-600" />
            <h3 className="text-lg font-semibold">Purchase Limits</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Daily Purchase Limit (grams)</label>
              <input
                type="number"
                value={localSettings.dailyPurchaseLimit}
                onChange={(e) => setLocalSettings({...localSettings, dailyPurchaseLimit: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Monthly Purchase Limit (grams)</label>
              <input
                type="number"
                value={localSettings.monthlyPurchaseLimit}
                onChange={(e) => setLocalSettings({...localSettings, monthlyPurchaseLimit: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={() => handleSave('compliance', localSettings)}
            disabled={saving}
            className="px-6 py-2 bg-accent-600 text-white rounded-lg hover:bg-accent-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Compliance Settings'}
          </button>
        </div>
      </div>
    );
  };

  // Hours Display Component (read-only)
  const HoursSettings = () => {
    const storeHours = store?.business_hours || {};
    const daysOfWeek = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];

    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-indigo-600" />
            <h3 className="text-lg font-semibold">Store Hours</h3>
          </div>

          <div className="space-y-3">
            {daysOfWeek.map(day => {
              const dayHours = storeHours[day];
              return (
                <div key={day} className="flex items-center justify-between py-2 border-b">
                  <span className="font-medium capitalize">{day}</span>
                  <span className={dayHours?.closed ? 'text-danger-600' : 'text-gray-700'}>
                    {!dayHours || dayHours.closed
                      ? 'Closed'
                      : `${dayHours.open} - ${dayHours.close}`}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-6 p-6 bg-blue-50 rounded-lg">
            <p className="text-sm text-accent-700">
              To modify store hours, please use the Store Hours Management page or contact support.
            </p>
          </div>
        </div>
      </div>
    );
  };

  // Render the active tab content
  const renderTabContent = () => {
    switch(activeTab) {
      case 'payment':
        return <PaymentSettings />;
      case 'delivery':
        return <DeliverySettings />;
      case 'compliance':
        return <ComplianceSettings />;
      case 'hours':
        return <HoursSettings />;
      case 'devices':
        return <DevicesSettings />;
      default:
        return <PaymentSettings />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="bg-white rounded-lg  p-1">
        <div className="flex flex-wrap gap-1">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-50 text-accent-600'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <tab.icon className={`w-4 h-4 ${activeTab === tab.id ? tab.color : ''}`} />
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {renderTabContent()}
      </div>
    </div>
  );
};

export default AllSettingsTabbed;