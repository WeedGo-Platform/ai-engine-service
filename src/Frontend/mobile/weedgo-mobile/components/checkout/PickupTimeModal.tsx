/**
 * Pickup Time Selector Modal
 * Allows users to select a pickup time slot for in-store pickup orders
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';

interface TimeSlot {
  id: string;
  time: string;
  label: string;
  available: boolean;
  estimatedMinutes: number;
}

interface PickupTimeModalProps {
  visible: boolean;
  onClose: () => void;
  onSelectTime: (timeSlot: string) => void;
  selectedTime?: string;
  storeHours?: {
    open: string;
    close: string;
  };
}

export function PickupTimeModal({
  visible,
  onClose,
  onSelectTime,
  selectedTime,
  storeHours,
}: PickupTimeModalProps) {
  const [loading, setLoading] = useState(false);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);

  useEffect(() => {
    if (visible) {
      generateTimeSlots();
    }
  }, [visible, storeHours]);

  const generateTimeSlots = () => {
    setLoading(true);

    const now = new Date();
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();

    // ASAP option (always first)
    const slots: TimeSlot[] = [
      {
        id: 'asap',
        time: 'ASAP',
        label: 'Ready in 15-20 minutes',
        available: true,
        estimatedMinutes: 15,
      },
    ];

    // Generate time slots for next 4 hours
    for (let i = 0; i < 8; i++) {
      const slotTime = new Date(now);
      slotTime.setMinutes(now.getMinutes() + (i + 1) * 30);

      const hour = slotTime.getHours();
      const minute = slotTime.getMinutes();

      // Check if within store hours (default 9 AM - 9 PM if not provided)
      const openHour = storeHours?.open ? parseInt(storeHours.open.split(':')[0]) : 9;
      const closeHour = storeHours?.close ? parseInt(storeHours.close.split(':')[0]) : 21;

      const isAvailable = hour >= openHour && hour < closeHour;

      // Format time
      const period = hour >= 12 ? 'PM' : 'AM';
      const displayHour = hour % 12 || 12;
      const displayMinute = minute.toString().padStart(2, '0');
      const timeString = `${displayHour}:${displayMinute} ${period}`;

      slots.push({
        id: `slot-${i}`,
        time: timeString,
        label: `Ready by ${timeString}`,
        available: isAvailable,
        estimatedMinutes: (i + 1) * 30,
      });
    }

    setTimeSlots(slots);
    setLoading(false);
  };

  const handleSelectTime = (slot: TimeSlot) => {
    if (!slot.available) return;

    onSelectTime(slot.label);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Select Pickup Time</Text>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={theme.text} />
          </TouchableOpacity>
        </View>

        {/* Content */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={theme.primary} />
              <Text style={styles.loadingText}>Loading available times...</Text>
            </View>
          ) : (
            <>
              <View style={styles.infoCard}>
                <Ionicons name="information-circle" size={20} color={theme.primary} />
                <Text style={styles.infoText}>
                  All times are estimated. We'll notify you when your order is ready for pickup.
                </Text>
              </View>

              <View style={styles.timeSlots}>
                {timeSlots.map((slot) => {
                  const isSelected = selectedTime === slot.label;

                  return (
                    <TouchableOpacity
                      key={slot.id}
                      style={[
                        styles.timeSlot,
                        !slot.available && styles.timeSlotDisabled,
                        isSelected && styles.timeSlotSelected,
                      ]}
                      onPress={() => handleSelectTime(slot)}
                      disabled={!slot.available}
                    >
                      <View style={styles.timeSlotContent}>
                        <View style={styles.timeSlotLeft}>
                          {slot.id === 'asap' ? (
                            <Ionicons
                              name="flash"
                              size={24}
                              color={isSelected ? theme.primary : theme.text}
                            />
                          ) : (
                            <Ionicons
                              name="time-outline"
                              size={24}
                              color={
                                !slot.available
                                  ? theme.disabled
                                  : isSelected
                                  ? theme.primary
                                  : theme.text
                              }
                            />
                          )}
                          <View style={styles.timeSlotInfo}>
                            <Text
                              style={[
                                styles.timeSlotTime,
                                !slot.available && styles.timeSlotTextDisabled,
                                isSelected && styles.timeSlotTextSelected,
                              ]}
                            >
                              {slot.time}
                            </Text>
                            <Text
                              style={[
                                styles.timeSlotLabel,
                                !slot.available && styles.timeSlotTextDisabled,
                              ]}
                            >
                              {slot.label}
                            </Text>
                          </View>
                        </View>

                        {isSelected && (
                          <Ionicons name="checkmark-circle" size={24} color={theme.primary} />
                        )}

                        {!slot.available && (
                          <Text style={styles.unavailableText}>Closed</Text>
                        )}
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </>
          )}
        </ScrollView>
      </View>
    </Modal>
  );
}

const theme = Colors.dark;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 60,
    paddingBottom: 15,
    paddingHorizontal: 16,
    backgroundColor: theme.glass,
    borderBottomWidth: 1,
    borderBottomColor: theme.glassBorder,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
  },
  closeButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 14,
    color: theme.textSecondary,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(116, 185, 255, 0.1)',
    padding: 12,
    borderRadius: BorderRadius.lg,
    marginBottom: 20,
    gap: 12,
    borderLeftWidth: 3,
    borderLeftColor: theme.primary,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: theme.textSecondary,
    lineHeight: 18,
  },
  timeSlots: {
    gap: 12,
  },
  timeSlot: {
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    padding: 16,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.small,
  },
  timeSlotDisabled: {
    opacity: 0.5,
  },
  timeSlotSelected: {
    backgroundColor: theme.cardBackground,
    borderColor: theme.primary,
    borderWidth: 2,
    ...Shadows.medium,
  },
  timeSlotContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  timeSlotLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  timeSlotInfo: {
    flex: 1,
  },
  timeSlotTime: {
    fontSize: 18,
    fontWeight: '600',
    color: theme.text,
    marginBottom: 2,
  },
  timeSlotLabel: {
    fontSize: 13,
    color: theme.textSecondary,
  },
  timeSlotTextDisabled: {
    color: theme.disabled,
  },
  timeSlotTextSelected: {
    color: theme.primary,
  },
  unavailableText: {
    fontSize: 12,
    color: theme.error,
    fontWeight: '500',
  },
});
