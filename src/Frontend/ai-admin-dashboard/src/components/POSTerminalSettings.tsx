import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Monitor,
  Plus,
  Edit2,
  Trash2,
  Wifi,
  WifiOff,
  Receipt,
  Save,
  RefreshCw,
  Bluetooth,
  Globe
} from 'lucide-react';

interface POSTerminal {
  id: string;
  name: string;
  type: string;
  serial_number?: string;
  ip_address?: string;
  port?: number;
  bluetooth_id?: string;
  status: 'active' | 'inactive' | 'offline';
  last_seen?: string;
}

interface ReceiptSettings {
  print_customer_copy: boolean;
  print_merchant_copy: boolean;
  email_receipt: boolean;
  sms_receipt: boolean;
}

interface OfflineMode {
  enabled: boolean;
  max_offline_amount: number;
  sync_interval_minutes: number;
}

interface POSTerminalSettings {
  terminals: POSTerminal[];
  default_terminal?: string;
  payment_methods: string[];
  tip_options: number[];
  tip_enabled: boolean;
  receipt_settings: ReceiptSettings;
  offline_mode: OfflineMode;
}

interface POSTerminalSettingsProps {
  storeId: string;
  settings: POSTerminalSettings;
  onSave: (settings: POSTerminalSettings) => Promise<void>;
  onPingTerminal?: (terminalId: string) => Promise<void>;
}

const TERMINAL_TYPES = [
  { id: 'moneris_move5000', name: 'Moneris Move 5000', icon: '📱' },
  { id: 'moneris_desk5000', name: 'Moneris Desk 5000', icon: '🖥️' },
  { id: 'square_terminal', name: 'Square Terminal', icon: '⬜' },
  { id: 'square_reader', name: 'Square Reader', icon: '📲' },
  { id: 'stripe_terminal', name: 'Stripe Terminal', icon: '💳' },
  { id: 'clover_flex', name: 'Clover Flex', icon: '🍀' }
];

const PAYMENT_METHODS = [
  { id: 'tap', name: 'Tap', icon: '👆' },
  { id: 'chip', name: 'Chip', icon: '💳' },
  { id: 'swipe', name: 'Swipe', icon: '💨' },
  { id: 'cash', name: 'Cash', icon: '💵' },
  { id: 'contactless', name: 'Contactless', icon: '📡' }
];

const POSTerminalSettingsComponent: React.FC<POSTerminalSettingsProps> = ({
  storeId,
  settings: initialonSave,
  onPingTerminal
}) => {
  const { t } = useTranslation(['common']);
  const [settings, setSettings] = useState<POSTerminalSettings>(initialSettings || {
    terminals: [],
    payment_methods: ['tap', 'chip', 'swipe', 'cash'],
    tip_options: [15, 18, 20, 0],
    tip_enabled: true,
    receipt_settings: {
      print_customer_copy: true,
      print_merchant_copy: false,
      email_receipt: true,
      sms_receipt: false
    },
    offline_mode: {
      enabled: false,
      max_offline_amount: 500,
      sync_interval_minutes: 5
    }
  });
  
  const [editingTerminal, setEditingTerminal] = useState<POSTerminal | null>(null);
  const [showAddTerminal, setShowAddTerminal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pingingTerminal, setPingingTerminal] = useState<string | null>(null);

  const handleAddTerminal = () => {
    const newTerminal: POSTerminal = {
      id: `term_${Date.now()}`,
      name: '',
      type: 'moneris_move5000',
      status: 'inactive'
    };
    setEditingTerminal(newTerminal);
    setShowAddTerminal(true);
  };

  const handleSaveTerminal = () => {
    if (!editingTerminal) return;

    if (showAddTerminal) {
      setSettings(prev => ({
        ...prev,
        terminals: [...prev.terminals, editingTerminal]
      }));
    } else {
      setSettings(prev => ({
        ...prev,
        terminals: prev.terminals.map(t => 
          t.id === editingTerminal.id ? editingTerminal : t
        )
      }));
    }

    setEditingTerminal(null);
    setShowAddTerminal(false);
  };

  const handleDeleteTerminal = (terminalId: string) => {
    if (window.confirm(t('common:confirmations.deleteTerminal'))) {
      setSettings(prev => ({
        ...prev,
        terminals: prev.terminals.filter(t => t.id !== terminalId)
      }));
    }
  };

  const handlePingTerminal = async (terminalId: string) => {
    if (!onPingTerminal) return;
    
    setPingingTerminal(terminalId);
    try {
      await onPingTerminal(terminalId);
      // Update terminal status based on ping result
      setSettings(prev => ({
        ...prev,
        terminals: prev.terminals.map(t => 
          t.id === terminalId 
            ? { ...t, status: 'active', last_seen: new Date().toISOString() }
            : t
        )
      }));
    } catch (error) {
      // Update terminal status to offline if ping fails
      setSettings(prev => ({
        ...prev,
        terminals: prev.terminals.map(t => 
          t.id === terminalId ? { ...t, status: 'offline' } : t
        )
      }));
    } finally {
      setPingingTerminal(null);
    }
  };

  const handlePaymentMethodToggle = (method: string) => {
    setSettings(prev => ({
      ...prev,
      payment_methods: prev.payment_methods.includes(method)
        ? prev.payment_methods.filter(m => m !== method)
        : [...prev.payment_methods, method]
    }));
  };

  const handleTipOptionChange = (index: number, value: number) => {
    setSettings(prev => ({
      ...prev,
      tip_options: prev.tip_options.map((opt, i) => i === index ? value : opt)
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(settings);
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-primary-600 bg-primary-100';
      case 'inactive': return 'text-gray-600 bg-gray-50';
      case 'offline': return 'text-danger-600 bg-danger-100';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-2">
          <Monitor className="w-6 h-6" />
          POS Terminal Settings
        </h2>
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-accent-500 text-white px-4 py-2 rounded-lg hover:bg-accent-600 flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Terminals List */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Terminals</h3>
          <button
            onClick={handleAddTerminal}
            className="bg-primary-500 text-white px-3 py-1 rounded-lg hover:bg-primary-600 flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Terminal
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {settings.terminals.map(terminal => (
            <div key={terminal.id} className="border rounded-lg p-6">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h4 className="font-semibold">{terminal.name || 'Unnamed Terminal'}</h4>
                  <p className="text-sm text-gray-600">
                    {TERMINAL_TYPES.find(t => t.id === terminal.type)?.name}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(terminal.status)}`}>
                  {terminal.status}
                </span>
              </div>

              {terminal.serial_number && (
                <p className="text-xs text-gray-500 mb-1">SN: {terminal.serial_number}</p>
              )}

              {terminal.ip_address && (
                <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                  <Globe className="w-3 h-3" />
                  {terminal.ip_address}:{terminal.port || 3000}
                </p>
              )}

              {terminal.bluetooth_id && (
                <p className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                  <Bluetooth className="w-3 h-3" />
                  {terminal.bluetooth_id}
                </p>
              )}

              {terminal.last_seen && (
                <p className="text-xs text-gray-500 mb-3">
                  Last seen: {new Date(terminal.last_seen).toLocaleString()}
                </p>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => handlePingTerminal(terminal.id)}
                  disabled={pingingTerminal === terminal.id}
                  className="flex-1 bg-accent-500 text-white px-2 py-1 rounded text-sm hover:bg-accent-600 flex items-center justify-center gap-1"
                >
                  {pingingTerminal === terminal.id ? (
                    <RefreshCw className="w-3 h-3 animate-spin" />
                  ) : terminal.status === 'active' ? (
                    <Wifi className="w-3 h-3" />
                  ) : (
                    <WifiOff className="w-3 h-3" />
                  )}
                  Ping
                </button>
                <button
                  onClick={() => {
                    setEditingTerminal(terminal);
                    setShowAddTerminal(false);
                  }}
                  className="flex-1 bg-gray-500 text-white px-2 py-1 rounded text-sm hover:bg-gray-600 flex items-center justify-center gap-1"
                >
                  <Edit2 className="w-3 h-3" />
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteTerminal(terminal.id)}
                  className="bg-danger-500 text-white px-2 py-1 rounded text-sm hover:bg-danger-600 flex items-center justify-center"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>

              {settings.default_terminal === terminal.id && (
                <div className="mt-2 text-xs bg-blue-100 text-accent-700 px-2 py-1 rounded text-center">
                  Default Terminal
                </div>
              )}
            </div>
          ))}
        </div>

        {settings.terminals.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No terminals configured. Add a terminal to get started.
          </div>
        )}
      </div>

      {/* Payment Methods */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Accepted Payment Methods</h3>
        <div className="flex flex-wrap gap-2">
          {PAYMENT_METHODS.map(method => (
            <button
              key={method.id}
              onClick={() => handlePaymentMethodToggle(method.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                settings.payment_methods.includes(method.id)
                  ? 'bg-blue-100 text-accent-700'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="mr-2">{method.icon}</span>
              {method.name}
            </button>
          ))}
        </div>
      </div>

      {/* Tip Settings */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <input
            type="checkbox"
            id="tip-enabled"
            checked={settings.tip_enabled}
            onChange={(e) => setSettings(prev => ({ ...prev, tip_enabled: e.target.checked }))}
            className="w-4 h-4 text-accent-600 rounded focus:ring-blue-500"
          />
          <label htmlFor="tip-enabled" className="text-lg font-semibold">
            Enable Tipping
          </label>
        </div>
        
        {settings.tip_enabled && (
          <div className="flex gap-4">
            <label className="text-sm font-medium text-gray-700">Tip Options (%):</label>
            {settings.tip_options.map((option, index) => (
              <input
                key={index}
                type="number"
                value={option}
                onChange={(e) => handleTipOptionChange(index, parseInt(e.target.value) || 0)}
                className="w-16 px-2 py-1 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="0"
                max="100"
              />
            ))}
          </div>
        )}
      </div>

      {/* Receipt Settings */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Receipt className="w-5 h-5" />
          Receipt Settings
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.receipt_settings.print_customer_copy}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                receipt_settings: { ...prev.receipt_settings, print_customer_copy: e.target.checked }
              }))}
              className="w-4 h-4 text-accent-600 rounded focus:ring-blue-500"
            />
            <span className="text-sm">Print Customer Copy</span>
          </label>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.receipt_settings.print_merchant_copy}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                receipt_settings: { ...prev.receipt_settings, print_merchant_copy: e.target.checked }
              }))}
              className="w-4 h-4 text-accent-600 rounded focus:ring-blue-500"
            />
            <span className="text-sm">Print Merchant Copy</span>
          </label>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.receipt_settings.email_receipt}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                receipt_settings: { ...prev.receipt_settings, email_receipt: e.target.checked }
              }))}
              className="w-4 h-4 text-accent-600 rounded focus:ring-blue-500"
            />
            <span className="text-sm">Email Receipt</span>
          </label>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.receipt_settings.sms_receipt}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                receipt_settings: { ...prev.receipt_settings, sms_receipt: e.target.checked }
              }))}
              className="w-4 h-4 text-accent-600 rounded focus:ring-blue-500"
            />
            <span className="text-sm">SMS Receipt</span>
          </label>
        </div>
      </div>

      {/* Offline Mode Settings */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Offline Mode</h3>
        <div className="space-y-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.offline_mode.enabled}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                offline_mode: { ...prev.offline_mode, enabled: e.target.checked }
              }))}
              className="w-4 h-4 text-accent-600 rounded focus:ring-blue-500"
            />
            <span className="text-sm font-medium">Enable Offline Processing</span>
          </label>
          
          {settings.offline_mode.enabled && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 ml-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Offline Amount ($)
                </label>
                <input
                  type="number"
                  value={settings.offline_mode.max_offline_amount}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    offline_mode: { ...prev.offline_mode, max_offline_amount: parseFloat(e.target.value) || 0 }
                  }))}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="0"
                  step="50"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sync Interval (minutes)
                </label>
                <input
                  type="number"
                  value={settings.offline_mode.sync_interval_minutes}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    offline_mode: { ...prev.offline_mode, sync_interval_minutes: parseInt(e.target.value) || 5 }
                  }))}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="60"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Terminal Edit Modal */}
      {editingTerminal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">
              {showAddTerminal ? 'Add Terminal' : 'Edit Terminal'}
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Terminal Name
                </label>
                <input
                  type="text"
                  value={editingTerminal.name}
                  onChange={(e) => setEditingTerminal({ ...editingTerminal, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Front Counter"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Terminal Type
                </label>
                <select
                  value={editingTerminal.type}
                  onChange={(e) => setEditingTerminal({ ...editingTerminal, type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {TERMINAL_TYPES.map(type => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Serial Number
                </label>
                <input
                  type="text"
                  value={editingTerminal.serial_number || ''}
                  onChange={(e) => setEditingTerminal({ ...editingTerminal, serial_number: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., SN123456"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  IP Address (for network terminals)
                </label>
                <input
                  type="text"
                  value={editingTerminal.ip_address || ''}
                  onChange={(e) => setEditingTerminal({ ...editingTerminal, ip_address: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., 192.168.1.100"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Bluetooth ID (for Bluetooth terminals)
                </label>
                <input
                  type="text"
                  value={editingTerminal.bluetooth_id || ''}
                  onChange={(e) => setEditingTerminal({ ...editingTerminal, bluetooth_id: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., XX:XX:XX:XX:XX:XX"
                />
              </div>
              
              <div className="flex items-center gap-4">
                <input
                  type="checkbox"
                  id="set-default"
                  checked={settings.default_terminal === editingTerminal.id}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    default_terminal: e.target.checked ? editingTerminal.id : undefined
                  }))}
                  className="w-4 h-4 text-accent-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="set-default" className="text-sm font-medium text-gray-700">
                  Set as default terminal
                </label>
              </div>
            </div>
            
            <div className="flex gap-4 mt-6">
              <button
                onClick={handleSaveTerminal}
                className="flex-1 bg-accent-500 text-white px-4 py-2 rounded-lg hover:bg-accent-600"
              >
                Save
              </button>
              <button
                onClick={() => {
                  setEditingTerminal(null);
                  setShowAddTerminal(false);
                }}
                className="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default POSTerminalSettingsComponent;