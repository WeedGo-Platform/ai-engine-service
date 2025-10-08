/**
 * Address Autocomplete Component
 * Search-as-you-type address input with dropdown suggestions
 * Uses Mapbox API with local caching for performance
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Keyboard,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { mapboxAutocomplete, AddressSuggestion } from '../services/mapboxAutocomplete';

interface AddressAutocompleteProps {
  onAddressSelect: (address: AddressSuggestion) => void;
  placeholder?: string;
  initialValue?: string;
  showRecentAddresses?: boolean;
  useProximity?: boolean;
  limit?: number;
}

export const AddressAutocomplete: React.FC<AddressAutocompleteProps> = ({
  onAddressSelect,
  placeholder = 'Enter your delivery address',
  initialValue = '',
  showRecentAddresses = true,
  useProximity = true,
  limit = 5,
}) => {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [recentAddresses, setRecentAddresses] = useState<AddressSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<TextInput>(null);

  // Load recent addresses when component mounts
  useEffect(() => {
    if (showRecentAddresses) {
      loadRecentAddresses();
    }
  }, [showRecentAddresses]);

  // Search addresses as user types (debounced)
  useEffect(() => {
    if (query.length >= 3 && isFocused) {
      searchAddresses(query);
    } else if (query.length < 3) {
      setSuggestions([]);
    }
  }, [query, isFocused]);

  const loadRecentAddresses = async () => {
    try {
      const recent = await mapboxAutocomplete.getRecentAddresses(3);
      setRecentAddresses(recent);
    } catch (error) {
      console.error('Failed to load recent addresses:', error);
    }
  };

  const searchAddresses = async (searchQuery: string) => {
    try {
      setIsLoading(true);

      const options = {
        limit,
        useCache: true,
        ...(useProximity && {
          proximity: await mapboxAutocomplete.getCurrentLocation() || undefined,
        }),
      };

      const results = await mapboxAutocomplete.searchAddressesDebounced(
        searchQuery,
        options,
        'address-input'
      );

      setSuggestions(results);
      setShowDropdown(true);
    } catch (error) {
      console.error('Address search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectAddress = async (address: AddressSuggestion) => {
    // Update input with selected address
    setQuery(address.place_name);

    // Mark as selected (increments use count)
    await mapboxAutocomplete.selectAddress(address);

    // Hide dropdown and keyboard
    setShowDropdown(false);
    Keyboard.dismiss();

    // Notify parent component
    onAddressSelect(address);

    // Reload recent addresses to show the newly selected one
    if (showRecentAddresses) {
      loadRecentAddresses();
    }
  };

  const handleClearInput = () => {
    setQuery('');
    setSuggestions([]);
    setShowDropdown(false);
    inputRef.current?.focus();
  };

  const handleFocus = () => {
    setIsFocused(true);
    if (query.length >= 3) {
      setShowDropdown(true);
    } else if (showRecentAddresses && recentAddresses.length > 0) {
      setShowDropdown(true);
    }
  };

  const handleBlur = () => {
    setIsFocused(false);
    // Delay hiding dropdown to allow tap on suggestion
    setTimeout(() => setShowDropdown(false), 200);
  };

  const showingSuggestions = suggestions.length > 0;
  const showingRecent = !showingSuggestions && recentAddresses.length > 0 && query.length < 3;

  return (
    <View style={styles.container}>
      {/* Search Input */}
      <View style={[styles.inputContainer, isFocused && styles.inputContainerFocused]}>
        <Ionicons name="search" size={20} color="#999" style={styles.searchIcon} />
        <TextInput
          ref={inputRef}
          style={styles.input}
          placeholder={placeholder}
          placeholderTextColor="#999"
          value={query}
          onChangeText={setQuery}
          onFocus={handleFocus}
          onBlur={handleBlur}
          autoCapitalize="words"
          autoCorrect={false}
          returnKeyType="search"
        />
        {query.length > 0 && (
          <TouchableOpacity onPress={handleClearInput} style={styles.clearButton}>
            <Ionicons name="close-circle" size={20} color="#999" />
          </TouchableOpacity>
        )}
        {isLoading && (
          <ActivityIndicator size="small" color="#4CAF50" style={styles.loader} />
        )}
      </View>

      {/* Dropdown with Suggestions */}
      {showDropdown && (showingSuggestions || showingRecent) && (
        <View style={styles.dropdown}>
          {showingSuggestions && (
            <>
              <View style={styles.dropdownHeader}>
                <Text style={styles.dropdownHeaderText}>Address Suggestions</Text>
              </View>
              <ScrollView style={styles.suggestionsList} keyboardShouldPersistTaps="handled">
                {suggestions.map((item) => (
                  <TouchableOpacity
                    key={item.id}
                    style={styles.suggestionItem}
                    onPress={() => handleSelectAddress(item)}
                  >
                    <Ionicons name="location-outline" size={20} color="#666" style={styles.suggestionIcon} />
                    <View style={styles.suggestionContent}>
                      <Text style={styles.suggestionText} numberOfLines={1}>
                        {item.address.street}
                      </Text>
                      <Text style={styles.suggestionSubtext} numberOfLines={1}>
                        {item.address.city}, {item.address.province} {item.address.postal_code}
                      </Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </>
          )}

          {showingRecent && (
            <>
              <View style={styles.dropdownHeader}>
                <Text style={styles.dropdownHeaderText}>Recent Addresses</Text>
              </View>
              <ScrollView style={styles.suggestionsList} keyboardShouldPersistTaps="handled">
                {recentAddresses.map((item) => (
                  <TouchableOpacity
                    key={item.id}
                    style={styles.suggestionItem}
                    onPress={() => handleSelectAddress(item)}
                  >
                    <Ionicons name="time-outline" size={20} color="#666" style={styles.suggestionIcon} />
                    <View style={styles.suggestionContent}>
                      <Text style={styles.suggestionText} numberOfLines={1}>
                        {item.address.street}
                      </Text>
                      <Text style={styles.suggestionSubtext} numberOfLines={1}>
                        {item.address.city}, {item.address.province}
                      </Text>
                    </View>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    zIndex: 1000,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  inputContainerFocused: {
    borderColor: '#4CAF50',
    backgroundColor: '#fff',
  },
  searchIcon: {
    marginRight: 8,
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#000',
    paddingVertical: 8,
  },
  clearButton: {
    marginLeft: 8,
    padding: 4,
  },
  loader: {
    marginLeft: 8,
  },
  dropdown: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderRadius: 12,
    marginTop: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
    maxHeight: 300,
    zIndex: 1001,
  },
  dropdownHeader: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  dropdownHeaderText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    textTransform: 'uppercase',
  },
  suggestionsList: {
    maxHeight: 250,
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f5f5f5',
  },
  suggestionIcon: {
    marginRight: 12,
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionText: {
    fontSize: 15,
    color: '#000',
    fontWeight: '500',
    marginBottom: 2,
  },
  suggestionSubtext: {
    fontSize: 13,
    color: '#666',
  },
});
