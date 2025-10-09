/**
 * Address Autocomplete Input Component
 * Provides real-time address suggestions using Mapbox API via backend
 * Features: Debounced search, cached results, proximity bias, recent addresses
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  Keyboard,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { mapboxAutocomplete, AddressSuggestion } from '@/services/mapboxAutocomplete';
import { DeliveryAddress } from '@/stores/orderStore';

interface AddressAutocompleteInputProps {
  value: string;
  onAddressSelect: (address: Partial<DeliveryAddress>, suggestion: AddressSuggestion) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

export function AddressAutocompleteInput({
  value,
  onAddressSelect,
  placeholder = 'Enter street address',
  autoFocus = false,
}: AddressAutocompleteInputProps) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [recentAddresses, setRecentAddresses] = useState<AddressSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [focused, setFocused] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Load recent addresses on mount
  useEffect(() => {
    loadRecentAddresses();
  }, []);

  const loadRecentAddresses = async () => {
    try {
      const recent = await mapboxAutocomplete.getRecentAddresses(3);
      setRecentAddresses(recent);
    } catch (error) {
      console.error('Failed to load recent addresses:', error);
    }
  };

  // Handle search with debouncing
  const handleSearch = async (text: string) => {
    setQuery(text);

    // Clear existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Show recent addresses if empty query
    if (!text || text.trim().length < 3) {
      setSuggestions([]);
      setShowSuggestions(true);
      return;
    }

    // Set loading state
    setLoading(true);
    setShowSuggestions(true);

    // Debounce search (300ms)
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const results = await mapboxAutocomplete.searchAddressesDebounced(
          text,
          { useCache: true, limit: 5 },
          'address-input'
        );
        setSuggestions(results);
      } catch (error) {
        console.error('Search failed:', error);
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 300);
  };

  const handleSelectSuggestion = async (suggestion: AddressSuggestion) => {
    // Mark address as selected (for prioritization)
    await mapboxAutocomplete.selectAddress(suggestion);

    // Convert suggestion to DeliveryAddress format
    const address: Partial<DeliveryAddress> = {
      street: suggestion.address.street,
      city: suggestion.address.city,
      province: suggestion.address.province,
      postal_code: suggestion.address.postal_code,
    };

    // Update query and hide suggestions
    setQuery(suggestion.place_name);
    setShowSuggestions(false);
    setSuggestions([]);

    // Dismiss keyboard
    Keyboard.dismiss();

    // Notify parent component
    onAddressSelect(address, suggestion);
  };

  const handleFocus = () => {
    setFocused(true);
    setShowSuggestions(true);
  };

  const handleBlur = () => {
    setFocused(false);
    // Delay hiding suggestions to allow tap to register
    setTimeout(() => {
      setShowSuggestions(false);
    }, 200);
  };

  const renderSuggestion = ({ item }: { item: AddressSuggestion }) => (
    <TouchableOpacity
      style={styles.suggestionItem}
      onPress={() => handleSelectSuggestion(item)}
      activeOpacity={0.7}
    >
      <View style={styles.suggestionIcon}>
        <Ionicons name="location-outline" size={20} color="#27AE60" />
      </View>
      <View style={styles.suggestionContent}>
        <Text style={styles.suggestionText} numberOfLines={1}>
          {item.place_name}
        </Text>
        <Text style={styles.suggestionSubtext} numberOfLines={1}>
          {item.address.city}, {item.address.province} {item.address.postal_code}
        </Text>
      </View>
      <View style={styles.suggestionArrow}>
        <Ionicons name="chevron-forward" size={20} color="#999" />
      </View>
    </TouchableOpacity>
  );

  const renderRecentAddress = ({ item }: { item: AddressSuggestion }) => (
    <TouchableOpacity
      style={styles.suggestionItem}
      onPress={() => handleSelectSuggestion(item)}
      activeOpacity={0.7}
    >
      <View style={styles.suggestionIcon}>
        <Ionicons name="time-outline" size={20} color="#666" />
      </View>
      <View style={styles.suggestionContent}>
        <Text style={styles.suggestionText} numberOfLines={1}>
          {item.place_name}
        </Text>
        <Text style={styles.suggestionSubtext} numberOfLines={1}>
          Recently used
        </Text>
      </View>
      <View style={styles.suggestionArrow}>
        <Ionicons name="chevron-forward" size={20} color="#999" />
      </View>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={[styles.inputContainer, focused && styles.inputContainerFocused]}>
        <Ionicons
          name="search-outline"
          size={20}
          color={focused ? '#27AE60' : '#999'}
          style={styles.searchIcon}
        />
        <TextInput
          style={styles.input}
          value={query}
          onChangeText={handleSearch}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          placeholderTextColor="#999"
          autoCapitalize="words"
          autoCorrect={false}
          autoFocus={autoFocus}
          returnKeyType="search"
        />
        {loading && (
          <ActivityIndicator size="small" color="#27AE60" style={styles.loader} />
        )}
        {query.length > 0 && !loading && (
          <TouchableOpacity
            onPress={() => {
              setQuery('');
              setSuggestions([]);
            }}
            style={styles.clearButton}
          >
            <Ionicons name="close-circle" size={20} color="#999" />
          </TouchableOpacity>
        )}
      </View>

      {/* Suggestions Dropdown */}
      {showSuggestions && (
        <View style={styles.suggestionsContainer}>
          {loading && suggestions.length === 0 ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="small" color="#27AE60" />
              <Text style={styles.loadingText}>Searching addresses...</Text>
            </View>
          ) : suggestions.length > 0 ? (
            <FlatList
              data={suggestions}
              renderItem={renderSuggestion}
              keyExtractor={(item) => item.id}
              style={styles.suggestionsList}
              keyboardShouldPersistTaps="handled"
            />
          ) : query.length === 0 && recentAddresses.length > 0 ? (
            <>
              <Text style={styles.sectionHeader}>Recent Addresses</Text>
              <FlatList
                data={recentAddresses}
                renderItem={renderRecentAddress}
                keyExtractor={(item) => item.id}
                style={styles.suggestionsList}
                keyboardShouldPersistTaps="handled"
              />
            </>
          ) : query.length >= 3 ? (
            <View style={styles.emptyState}>
              <Ionicons name="location-outline" size={32} color="#CCC" />
              <Text style={styles.emptyText}>No addresses found</Text>
              <Text style={styles.emptySubtext}>
                Try a different search term
              </Text>
            </View>
          ) : null}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    zIndex: 1000,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5E5',
    paddingHorizontal: 12,
    height: 48,
  },
  inputContainerFocused: {
    borderColor: '#27AE60',
    backgroundColor: '#FFF',
  },
  searchIcon: {
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: '#333',
    padding: 0,
  },
  loader: {
    marginLeft: 8,
  },
  clearButton: {
    marginLeft: 8,
    padding: 4,
  },
  suggestionsContainer: {
    position: 'absolute',
    top: 52,
    left: 0,
    right: 0,
    backgroundColor: '#FFF',
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 5,
    maxHeight: 300,
    zIndex: 1001,
  },
  suggestionsList: {
    maxHeight: 300,
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
  },
  suggestionIcon: {
    width: 32,
    alignItems: 'center',
    marginRight: 12,
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionText: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
    marginBottom: 2,
  },
  suggestionSubtext: {
    fontSize: 12,
    color: '#666',
  },
  suggestionArrow: {
    marginLeft: 8,
  },
  sectionHeader: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#F8F9FA',
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  loadingText: {
    marginLeft: 12,
    fontSize: 14,
    color: '#666',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  emptyText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#666',
    marginTop: 8,
  },
  emptySubtext: {
    fontSize: 13,
    color: '#999',
    marginTop: 4,
  },
});
