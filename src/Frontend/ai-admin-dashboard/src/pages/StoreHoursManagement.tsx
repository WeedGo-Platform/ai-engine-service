import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Clock, Calendar, AlertCircle, Save, Plus, Trash2, 
  Settings, ChevronDown, ChevronUp, X, Check, ArrowLeft, Loader2
} from 'lucide-react';
import tenantService from '../services/tenantService';
import storeService from '../services/storeService';
import storeHoursService from '../services/storeHoursService';

// Import types from service
import type {
  TimeSlot,
  ServiceHours,
  RegularHours,
  HolidayHours as HolidayHoursType,
  SpecialHours as SpecialHoursType,
  StoreHoursSettings,
  Holiday
} from '../services/storeHoursService';


const DAYS_OF_WEEK = [
  'Sunday', 'Monday', 'Tuesday', 'Wednesday', 
  'Thursday', 'Friday', 'Saturday'
];

const TIMEZONES = [
  'America/Vancouver',    // PST/PDT
  'America/Edmonton',     // MST/MDT
  'America/Regina',       // CST (no DST)
  'America/Winnipeg',     // CST/CDT
  'America/Toronto',      // EST/EDT
  'America/Halifax',      // AST/ADT
  'America/St_Johns',     // NST/NDT
];

export default function StoreHoursManagement() {
  const { storeCode } = useParams<{ storeCode: string }>();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [store, setStore] = useState<any>(null);
  const [storeId, setStoreId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'regular' | 'holidays' | 'special' | 'settings'>('regular');
  
  // State for different hour types
  const [regularHours, setRegularHours] = useState<RegularHours[]>([]);
  const [holidayHours, setHolidayHours] = useState<HolidayHoursType[]>([]);
  const [specialHours, setSpecialHours] = useState<SpecialHoursType[]>([]);
  const [settings, setSettings] = useState<StoreHoursSettings>({
    observe_federal_holidays: true,
    observe_provincial_holidays: true,
    observe_municipal_holidays: false,
    default_holiday_action: 'closed',
    delivery_holiday_behavior: 'same_as_store',
    pickup_holiday_behavior: 'same_as_store'
  });
  
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  
  // Modal states
  const [showHolidayModal, setShowHolidayModal] = useState(false);
  const [showSpecialModal, setShowSpecialModal] = useState(false);
  const [editingHoliday, setEditingHoliday] = useState<HolidayHoursType | null>(null);
  const [editingSpecial, setEditingSpecial] = useState<SpecialHoursType | null>(null);

  useEffect(() => {
    if (storeCode) {
      loadStoreByCode();
    }
  }, [storeCode]);

  useEffect(() => {
    if (storeId) {
      loadStoreData();
      loadHolidays();
    }
  }, [storeId]);

  const loadStoreByCode = async () => {
    try {
      setLoading(true);
      
      // First try to get by store code
      try {
        const storeData = await storeService.getStoreByCode(storeCode!);
        setStore(storeData);
        setStoreId(storeData.id);
      } catch (err) {
        console.log('Store by code not found, trying alternative approach');
        
        // If that fails, get the first store (temporary workaround)
        const tenantId = 'e6e513b2-c589-4f0b-a6f8-a52dd93feb90'; // This should come from auth context
        const stores = await storeService.getStoresByTenant(tenantId);
        const storeData = stores.find(s => s.store_code === storeCode) || stores[0];
        if (storeData) {
          setStore(storeData);
          setStoreId(storeData.id);
        } else {
          throw new Error('Store not found');
        }
      }
    } catch (error) {
      console.error('Error loading store:', error);
      showNotification('error', 'Failed to load store');
    } finally {
      setLoading(false);
    }
  };

  const loadStoreData = async () => {
    if (!storeId) return;
    
    try {
      
      // Load hours data using service
      const data = await storeHoursService.getStoreHours(storeId);
      setRegularHours(data.regular_hours.length > 0 ? data.regular_hours : initializeRegularHours());
      setHolidayHours(data.holiday_hours || []);
      setSpecialHours(data.special_hours || []);
      setSettings(data.settings || settings);
      // Don't overwrite holidays - they're loaded separately via loadHolidays()
    } catch (err) {
      // Initialize with default hours if none exist
      setRegularHours(initializeRegularHours());
    }
  };

  const loadHolidays = async () => {
    try {
      const data = await storeHoursService.getHolidays();
      console.log('Loaded holidays:', data);
      setHolidays(data);
    } catch (error) {
      console.error('Error loading holidays:', error);
    }
  };

  const initializeRegularHours = (): RegularHours[] => {
    return Array.from({ length: 7 }, (_, i) => ({
      day_of_week: i,
      is_closed: i === 0, // Closed on Sunday by default
      time_slots: [{
        open: i === 0 ? '' : (i === 6 ? '10:00' : '09:00'),
        close: i === 0 ? '' : (i === 6 ? '20:00' : '21:00')
      }],
      delivery_hours: undefined,
      pickup_hours: undefined
    }));
  };

  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  const saveRegularHours = async () => {
    if (!storeId) return;
    
    try {
      setSaving(true);
      await storeHoursService.updateRegularHours(storeId, regularHours);
      showNotification('success', 'Regular hours saved successfully');
    } catch (error) {
      console.error('Error saving regular hours:', error);
      showNotification('error', 'Failed to save regular hours');
    } finally {
      setSaving(false);
    }
  };

  const saveHolidayHours = async (holidayHour: HolidayHoursType) => {
    if (!storeId) return;
    
    try {
      setSaving(true);
      if (editingHoliday?.id) {
        await storeHoursService.updateHolidayHours(storeId, editingHoliday.id, holidayHour);
      } else {
        await storeHoursService.addHolidayHours(storeId, holidayHour);
      }
      showNotification('success', 'Holiday hours saved successfully');
      await loadStoreData();
      setShowHolidayModal(false);
      setEditingHoliday(null);
    } catch (error) {
      console.error('Error saving holiday hours:', error);
      showNotification('error', 'Failed to save holiday hours');
    } finally {
      setSaving(false);
    }
  };

  const saveSpecialHours = async (specialHour: SpecialHoursType) => {
    if (!storeId) return;
    
    try {
      setSaving(true);
      if (editingSpecial?.id) {
        await storeHoursService.updateSpecialHours(storeId, editingSpecial.id, specialHour);
      } else {
        await storeHoursService.addSpecialHours(storeId, specialHour);
      }
      showNotification('success', 'Special hours saved successfully');
      await loadStoreData();
      setShowSpecialModal(false);
      setEditingSpecial(null);
    } catch (error) {
      console.error('Error saving special hours:', error);
      showNotification('error', 'Failed to save special hours');
    } finally {
      setSaving(false);
    }
  };

  const saveSettings = async () => {
    if (!storeId) return;
    
    try {
      setSaving(true);
      await storeHoursService.updateSettings(storeId, settings);
      showNotification('success', 'Settings saved successfully');
    } catch (error) {
      console.error('Error saving settings:', error);
      showNotification('error', 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const updateRegularHours = (dayIndex: number, field: keyof RegularHours, value: any) => {
    setRegularHours(prev => {
      const updated = [...prev];
      updated[dayIndex] = { ...updated[dayIndex], [field]: value };
      return updated;
    });
  };

  const addTimeSlot = (dayIndex: number) => {
    setRegularHours(prev => {
      const updated = [...prev];
      updated[dayIndex].time_slots.push({ open: '09:00', close: '17:00' });
      return updated;
    });
  };

  const removeTimeSlot = (dayIndex: number, slotIndex: number) => {
    setRegularHours(prev => {
      const updated = [...prev];
      updated[dayIndex].time_slots.splice(slotIndex, 1);
      return updated;
    });
  };

  const updateTimeSlot = (dayIndex: number, slotIndex: number, field: 'open' | 'close', value: string) => {
    setRegularHours(prev => {
      const updated = [...prev];
      updated[dayIndex].time_slots[slotIndex][field] = value;
      return updated;
    });
  };

  const toggleDayExpanded = (dayIndex: number) => {
    setExpandedDays(prev => {
      const next = new Set(prev);
      if (next.has(dayIndex)) {
        next.delete(dayIndex);
      } else {
        next.add(dayIndex);
      }
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="text-gray-600 hover:text-gray-900 mb-4"
        >
          ← Back to Store
        </button>
        <h1 className="text-3xl font-bold text-gray-900">Store Hours Management</h1>
        <p className="text-gray-600 mt-2">{store?.name} - {store?.store_code}</p>
      </div>

      {/* Notification */}
      {notification && (
        <div className={`mb-4 p-6 rounded-lg flex items-center ${
          notification.type === 'success' ? 'bg-primary-50 text-primary-800' : 'bg-danger-50 text-danger-800'
        }`}>
          {notification.type === 'success' ? (
            <Check className="h-5 w-5 mr-2" />
          ) : (
            <AlertCircle className="h-5 w-5 mr-2" />
          )}
          {notification.message}
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg  mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('regular')}
              className={`py-2 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'regular'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
              }`}
            >
              <Clock className="inline h-4 w-4 mr-2" />
              Regular Hours
            </button>
            <button
              onClick={() => setActiveTab('holidays')}
              className={`py-2 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'holidays'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
              }`}
            >
              <Calendar className="inline h-4 w-4 mr-2" />
              Holiday Hours
            </button>
            <button
              onClick={() => setActiveTab('special')}
              className={`py-2 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'special'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
              }`}
            >
              <AlertCircle className="inline h-4 w-4 mr-2" />
              Special Hours
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`py-2 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'settings'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
              }`}
            >
              <Settings className="inline h-4 w-4 mr-2" />
              Settings
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* Regular Hours Tab */}
          {activeTab === 'regular' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Regular Weekly Hours</h2>
              <div className="space-y-4">
                {regularHours.map((day, dayIndex) => (
                  <div key={dayIndex} className="border rounded-lg p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <h3 className="font-medium text-lg">{DAYS_OF_WEEK[dayIndex]}</h3>
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={day.is_closed}
                            onChange={(e) => updateRegularHours(dayIndex, 'is_closed', e.target.checked)}
                            className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
                          />
                          <span className="ml-2 text-sm text-gray-600">Closed</span>
                        </label>
                      </div>
                      <button
                        onClick={() => toggleDayExpanded(dayIndex)}
                        className="text-gray-500 hover:text-gray-700"
                      >
                        {expandedDays.has(dayIndex) ? <ChevronUp /> : <ChevronDown />}
                      </button>
                    </div>

                    {!day.is_closed && (
                      <div className="mt-4 space-y-3">
                        {/* Time Slots */}
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Store Hours
                          </label>
                          {day.time_slots.map((slot, slotIndex) => (
                            <div key={slotIndex} className="flex items-center space-x-2 mb-2">
                              <input
                                type="time"
                                value={slot.open}
                                onChange={(e) => updateTimeSlot(dayIndex, slotIndex, 'open', e.target.value)}
                                className="px-3 py-2 border border-gray-200 rounded-lg"
                              />
                              <span className="text-gray-500">to</span>
                              <input
                                type="time"
                                value={slot.close}
                                onChange={(e) => updateTimeSlot(dayIndex, slotIndex, 'close', e.target.value)}
                                className="px-3 py-2 border border-gray-200 rounded-lg"
                              />
                              {day.time_slots.length > 1 && (
                                <button
                                  onClick={() => removeTimeSlot(dayIndex, slotIndex)}
                                  className="text-danger-600 hover:text-danger-800"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          ))}
                          <button
                            onClick={() => addTimeSlot(dayIndex)}
                            className="text-sm text-primary-600 hover:text-primary-700"
                          >
                            <Plus className="inline h-4 w-4" /> Add time slot
                          </button>
                        </div>

                        {/* Service Hours (if expanded) */}
                        {expandedDays.has(dayIndex) && (
                          <div className="pt-4 border-t space-y-3">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Delivery Hours (optional)
                              </label>
                              <div className="space-y-2">
                                <label className="flex items-center">
                                  <input
                                    type="checkbox"
                                    checked={day.delivery_hours?.enabled || false}
                                    onChange={(e) => {
                                      const hours = day.delivery_hours || { enabled: false, time_slots: [] };
                                      updateRegularHours(dayIndex, 'delivery_hours', {
                                        ...hours,
                                        enabled: e.target.checked,
                                        time_slots: hours.time_slots.length > 0 ? hours.time_slots : [{ open: '09:00', close: '21:00' }]
                                      });
                                    }}
                                    className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
                                  />
                                  <span className="ml-2 text-sm">Enable delivery during these hours</span>
                                </label>
                                {day.delivery_hours?.enabled && (
                                  <div className="ml-6">
                                    {(day.delivery_hours.time_slots || []).map((slot, idx) => (
                                      <div key={idx} className="flex items-center space-x-2 mb-2">
                                        <input
                                          type="time"
                                          value={slot.open}
                                          onChange={(e) => {
                                            const updatedSlots = [...(day.delivery_hours?.time_slots || [])];
                                            updatedSlots[idx] = { ...updatedSlots[idx], open: e.target.value };
                                            updateRegularHours(dayIndex, 'delivery_hours', {
                                              ...day.delivery_hours!,
                                              time_slots: updatedSlots
                                            });
                                          }}
                                          className="px-3 py-2 border border-gray-200 rounded-lg"
                                        />
                                        <span className="text-gray-500">to</span>
                                        <input
                                          type="time"
                                          value={slot.close}
                                          onChange={(e) => {
                                            const updatedSlots = [...(day.delivery_hours?.time_slots || [])];
                                            updatedSlots[idx] = { ...updatedSlots[idx], close: e.target.value };
                                            updateRegularHours(dayIndex, 'delivery_hours', {
                                              ...day.delivery_hours!,
                                              time_slots: updatedSlots
                                            });
                                          }}
                                          className="px-3 py-2 border border-gray-200 rounded-lg"
                                        />
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 mb-2">
                                Pickup Hours (optional)
                              </label>
                              <div className="space-y-2">
                                <label className="flex items-center">
                                  <input
                                    type="checkbox"
                                    checked={day.pickup_hours?.enabled || false}
                                    onChange={(e) => {
                                      const hours = day.pickup_hours || { enabled: false, time_slots: [] };
                                      updateRegularHours(dayIndex, 'pickup_hours', {
                                        ...hours,
                                        enabled: e.target.checked,
                                        time_slots: hours.time_slots.length > 0 ? hours.time_slots : [{ open: '09:00', close: '21:00' }]
                                      });
                                    }}
                                    className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
                                  />
                                  <span className="ml-2 text-sm">Enable pickup during these hours</span>
                                </label>
                                {day.pickup_hours?.enabled && (
                                  <div className="ml-6">
                                    {(day.pickup_hours.time_slots || []).map((slot, idx) => (
                                      <div key={idx} className="flex items-center space-x-2 mb-2">
                                        <input
                                          type="time"
                                          value={slot.open}
                                          onChange={(e) => {
                                            const updatedSlots = [...(day.pickup_hours?.time_slots || [])];
                                            updatedSlots[idx] = { ...updatedSlots[idx], open: e.target.value };
                                            updateRegularHours(dayIndex, 'pickup_hours', {
                                              ...day.pickup_hours!,
                                              time_slots: updatedSlots
                                            });
                                          }}
                                          className="px-3 py-2 border border-gray-200 rounded-lg"
                                        />
                                        <span className="text-gray-500">to</span>
                                        <input
                                          type="time"
                                          value={slot.close}
                                          onChange={(e) => {
                                            const updatedSlots = [...(day.pickup_hours?.time_slots || [])];
                                            updatedSlots[idx] = { ...updatedSlots[idx], close: e.target.value };
                                            updateRegularHours(dayIndex, 'pickup_hours', {
                                              ...day.pickup_hours!,
                                              time_slots: updatedSlots
                                            });
                                          }}
                                          className="px-3 py-2 border border-gray-200 rounded-lg"
                                        />
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-6">
                <button
                  onClick={saveRegularHours}
                  disabled={saving}
                  className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  <Save className="inline h-4 w-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Regular Hours'}
                </button>
              </div>
            </div>
          )}

          {/* Holiday Hours Tab */}
          {activeTab === 'holidays' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Holiday Hours</h2>
              
              <button
                onClick={() => {
                  setEditingHoliday(null);
                  setShowHolidayModal(true);
                }}
                className="mb-6 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Holiday Hours
              </button>

              {/* List of Holiday Hours */}
              <div className="space-y-4">
                {holidayHours.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    No holiday hours configured. Add holiday-specific hours above.
                  </p>
                ) : (
                  holidayHours.map((holiday, index) => (
                    <div key={index} className="border rounded-lg p-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium">
                            {holidays.find(h => h.id === holiday.holiday_id)?.name || 'Holiday'}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {holiday.is_closed ? 'Closed' : `Open: ${holiday.time_slots.map(s => `${s.open}-${s.close}`).join(', ')}`}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button 
                            onClick={() => {
                              setEditingHoliday(holiday);
                              setShowHolidayModal(true);
                            }}
                            className="text-accent-600 hover:text-blue-800"
                          >
                            Edit
                          </button>
                          <button 
                            onClick={async () => {
                              if (holiday.id && confirm('Delete this holiday configuration?')) {
                                try {
                                  await storeHoursService.deleteHolidayHours(storeId, holiday.id);
                                  await loadStoreData();
                                  showNotification('success', 'Holiday hours deleted');
                                } catch (error) {
                                  showNotification('error', 'Failed to delete holiday hours');
                                }
                              }
                            }}
                            className="text-danger-600 hover:text-danger-800"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Special Hours Tab */}
          {activeTab === 'special' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Special Hours</h2>
              
              <button
                onClick={() => {
                  setEditingSpecial(null);
                  setShowSpecialModal(true);
                }}
                className="mb-6 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Add Special Hours
              </button>

              {/* List of Special Hours */}
              <div className="space-y-4">
                {specialHours.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">
                    No special hours scheduled. Add temporary schedule changes above.
                  </p>
                ) : (
                  specialHours.map((special, index) => (
                    <div key={index} className="border rounded-lg p-6">
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium">{special.date}</h4>
                          {special.reason && (
                            <p className="text-sm text-gray-500">{special.reason}</p>
                          )}
                          <p className="text-sm text-gray-600">
                            {special.is_closed ? 'Closed' : `Open: ${special.time_slots.map(s => `${s.open}-${s.close}`).join(', ')}`}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button 
                            onClick={() => {
                              setEditingSpecial(special);
                              setShowSpecialModal(true);
                            }}
                            className="text-accent-600 hover:text-blue-800"
                          >
                            Edit
                          </button>
                          <button 
                            onClick={async () => {
                              if (special.id && confirm('Delete this special hours entry?')) {
                                try {
                                  await storeHoursService.deleteSpecialHours(storeId, special.id);
                                  await loadStoreData();
                                  showNotification('success', 'Special hours deleted');
                                } catch (error) {
                                  showNotification('error', 'Failed to delete special hours');
                                }
                              }
                            }}
                            className="text-danger-600 hover:text-danger-800"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Hours Management Settings</h2>
              
              <div className="space-y-6">
                {/* Holiday Observance */}
                <div>
                  <h3 className="font-medium mb-3">Holiday Observance</h3>
                  <div className="space-y-3">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={settings.observe_federal_holidays}
                        onChange={(e) => setSettings({ ...settings, observe_federal_holidays: e.target.checked })}
                        className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="ml-2">Observe federal holidays</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={settings.observe_provincial_holidays}
                        onChange={(e) => setSettings({ ...settings, observe_provincial_holidays: e.target.checked })}
                        className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="ml-2">Observe provincial holidays</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={settings.observe_municipal_holidays}
                        onChange={(e) => setSettings({ ...settings, observe_municipal_holidays: e.target.checked })}
                        className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="ml-2">Observe municipal holidays</span>
                    </label>
                  </div>
                </div>

                {/* Holiday Behavior */}
                <div>
                  <h3 className="font-medium mb-3">Default Holiday Behavior</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        When a holiday is observed
                      </label>
                      <select
                        value={settings.default_holiday_action}
                        onChange={(e) => setSettings({ ...settings, default_holiday_action: e.target.value as 'closed' | 'modified' | 'open' })}
                        className="w-64 px-3 py-2 border border-gray-200 rounded-lg"
                      >
                        <option value="closed">Store is closed</option>
                        <option value="modified">Store has modified hours</option>
                        <option value="open">Store remains open (regular hours)</option>
                      </select>
                    </div>
                    
                    {settings.default_holiday_action === 'modified' && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Default holiday hours
                        </label>
                        <div className="flex items-center space-x-2">
                          <input
                            type="time"
                            value={settings.modified_holiday_hours?.[0]?.open || '10:00'}
                            onChange={(e) => setSettings({ 
                              ...settings, 
                              modified_holiday_hours: [{ open: e.target.value, close: settings.modified_holiday_hours?.[0]?.close || '18:00' }]
                            })}
                            className="px-3 py-2 border border-gray-200 rounded-lg"
                          />
                          <span className="text-gray-500">to</span>
                          <input
                            type="time"
                            value={settings.modified_holiday_hours?.[0]?.close || '18:00'}
                            onChange={(e) => setSettings({ 
                              ...settings, 
                              modified_holiday_hours: [{ open: settings.modified_holiday_hours?.[0]?.open || '10:00', close: e.target.value }]
                            })}
                            className="px-3 py-2 border border-gray-200 rounded-lg"
                          />
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Delivery service on holidays
                      </label>
                      <select
                        value={settings.delivery_holiday_behavior}
                        onChange={(e) => setSettings({ ...settings, delivery_holiday_behavior: e.target.value as 'same_as_store' | 'closed' | 'modified' })}
                        className="w-64 px-3 py-2 border border-gray-200 rounded-lg"
                      >
                        <option value="same_as_store">Same as store hours</option>
                        <option value="closed">No delivery</option>
                        <option value="modified">Modified delivery hours</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Pickup service on holidays
                      </label>
                      <select
                        value={settings.pickup_holiday_behavior}
                        onChange={(e) => setSettings({ ...settings, pickup_holiday_behavior: e.target.value as 'same_as_store' | 'closed' | 'modified' })}
                        className="w-64 px-3 py-2 border border-gray-200 rounded-lg"
                      >
                        <option value="same_as_store">Same as store hours</option>
                        <option value="closed">No pickup</option>
                        <option value="modified">Modified pickup hours</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="pt-4">
                  <button
                    onClick={saveSettings}
                    disabled={saving}
                    className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                  >
                    <Save className="inline h-4 w-4 mr-2" />
                    {saving ? 'Saving...' : 'Save Settings'}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Holiday Hours Modal */}
      {showHolidayModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">
                {editingHoliday ? 'Edit Holiday Hours' : 'Add Holiday Hours'}
              </h3>
              <button
                onClick={() => {
                  setShowHolidayModal(false);
                  setEditingHoliday(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <HolidayHoursForm
              holiday={editingHoliday}
              holidays={holidays}
              onSave={saveHolidayHours}
              onCancel={() => {
                setShowHolidayModal(false);
                setEditingHoliday(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Special Hours Modal */}
      {showSpecialModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">
                {editingSpecial ? 'Edit Special Hours' : 'Add Special Hours'}
              </h3>
              <button
                onClick={() => {
                  setShowSpecialModal(false);
                  setEditingSpecial(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <SpecialHoursForm
              special={editingSpecial}
              onSave={saveSpecialHours}
              onCancel={() => {
                setShowSpecialModal(false);
                setEditingSpecial(null);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Holiday Hours Form Component
function HolidayHoursForm({
  holiday,
  holidays,
  onSave,
  onCancel
}: {
  holiday: HolidayHoursType | null;
  holidays: Holiday[];
  onSave: (holiday: HolidayHoursType) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<HolidayHoursType>(holiday || {
    holiday_id: '',
    is_closed: true,
    time_slots: [{ open: '10:00', close: '18:00' }]
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Holiday
        </label>
        <select
          value={formData.holiday_id}
          onChange={(e) => setFormData({ ...formData, holiday_id: e.target.value })}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg"
          required
        >
          <option value="">Select a holiday...</option>
          {holidays && holidays.map(h => (
            <option key={h.id} value={h.id}>
              {h.name} ({h.holiday_type})
            </option>
          ))}
        </select>
      </div>

      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={formData.is_closed}
            onChange={(e) => setFormData({ ...formData, is_closed: e.target.checked })}
            className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
          />
          <span className="ml-2">Store is closed on this holiday</span>
        </label>
      </div>

      {!formData.is_closed && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Store Hours
          </label>
          {formData.time_slots.map((slot, index) => (
            <div key={index} className="flex items-center space-x-2 mb-2">
              <input
                type="time"
                value={slot.open}
                onChange={(e) => {
                  const updated = [...formData.time_slots];
                  updated[index] = { ...updated[index], open: e.target.value };
                  setFormData({ ...formData, time_slots: updated });
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg"
                required
              />
              <span className="text-gray-500">to</span>
              <input
                type="time"
                value={slot.close}
                onChange={(e) => {
                  const updated = [...formData.time_slots];
                  updated[index] = { ...updated[index], close: e.target.value };
                  setFormData({ ...formData, time_slots: updated });
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg"
                required
              />
              {formData.time_slots.length > 1 && (
                <button
                  type="button"
                  onClick={() => {
                    const updated = formData.time_slots.filter((_, i) => i !== index);
                    setFormData({ ...formData, time_slots: updated });
                  }}
                  className="text-danger-600 hover:text-danger-800"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={() => {
              setFormData({
                ...formData,
                time_slots: [...formData.time_slots, { open: '09:00', close: '17:00' }]
              });
            }}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            <Plus className="inline h-4 w-4" /> Add time slot
          </button>
        </div>
      )}

      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Save
        </button>
      </div>
    </form>
  );
}

// Special Hours Form Component
function SpecialHoursForm({
  special,
  onSave,
  onCancel
}: {
  special: SpecialHoursType | null;
  onSave: (special: SpecialHoursType) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<SpecialHoursType>(special || {
    date: '',
    is_closed: false,
    reason: '',
    time_slots: [{ open: '09:00', close: '21:00' }]
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Date
        </label>
        <input
          type="date"
          value={formData.date}
          onChange={(e) => setFormData({ ...formData, date: e.target.value })}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Reason (optional)
        </label>
        <input
          type="text"
          value={formData.reason || ''}
          onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
          placeholder="e.g., Staff Training, Inventory, Holiday Sale"
          className="w-full px-3 py-2 border border-gray-200 rounded-lg"
        />
      </div>

      <div>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={formData.is_closed}
            onChange={(e) => setFormData({ ...formData, is_closed: e.target.checked })}
            className="rounded border-gray-200 text-primary-600 focus:ring-primary-500"
          />
          <span className="ml-2">Store is closed on this date</span>
        </label>
      </div>

      {!formData.is_closed && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Store Hours
          </label>
          {formData.time_slots.map((slot, index) => (
            <div key={index} className="flex items-center space-x-2 mb-2">
              <input
                type="time"
                value={slot.open}
                onChange={(e) => {
                  const updated = [...formData.time_slots];
                  updated[index] = { ...updated[index], open: e.target.value };
                  setFormData({ ...formData, time_slots: updated });
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg"
                required
              />
              <span className="text-gray-500">to</span>
              <input
                type="time"
                value={slot.close}
                onChange={(e) => {
                  const updated = [...formData.time_slots];
                  updated[index] = { ...updated[index], close: e.target.value };
                  setFormData({ ...formData, time_slots: updated });
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg"
                required
              />
              {formData.time_slots.length > 1 && (
                <button
                  type="button"
                  onClick={() => {
                    const updated = formData.time_slots.filter((_, i) => i !== index);
                    setFormData({ ...formData, time_slots: updated });
                  }}
                  className="text-danger-600 hover:text-danger-800"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={() => {
              setFormData({
                ...formData,
                time_slots: [...formData.time_slots, { open: '09:00', close: '17:00' }]
              });
            }}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            <Plus className="inline h-4 w-4" /> Add time slot
          </button>
        </div>
      )}

      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Save
        </button>
      </div>
    </form>
  );
}