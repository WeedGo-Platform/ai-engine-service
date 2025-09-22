import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/stores/authStore';
import { Colors } from '@/constants/Colors';
import { Ionicons } from '@expo/vector-icons';

export default function HomeScreen() {
  const { user, isAuthenticated } = useAuthStore();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>
              {isAuthenticated && user
                ? `Hello, ${user.first_name}!`
                : 'Welcome to WeedGo'}
            </Text>
            <Text style={styles.subtitle}>
              {isAuthenticated
                ? 'What can we help you find today?'
                : 'Sign in for a personalized experience'}
            </Text>
          </View>
          <TouchableOpacity style={styles.notificationButton}>
            <Ionicons name="notifications-outline" size={24} color={Colors.light.text} />
          </TouchableOpacity>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActions}>
            <TouchableOpacity style={styles.actionCard}>
              <Ionicons name="location-outline" size={28} color={Colors.light.primary} />
              <Text style={styles.actionText}>Find Stores</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionCard}>
              <Ionicons name="time-outline" size={28} color={Colors.light.primary} />
              <Text style={styles.actionText}>Order History</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionCard}>
              <Ionicons name="star-outline" size={28} color={Colors.light.primary} />
              <Text style={styles.actionText}>Deals</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.actionCard}>
              <Ionicons name="heart-outline" size={28} color={Colors.light.primary} />
              <Text style={styles.actionText}>Favorites</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Featured Products */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Featured Products</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {[1, 2, 3, 4].map((item) => (
              <View key={item} style={styles.productCard}>
                <View style={styles.productImage} />
                <Text style={styles.productName}>Product {item}</Text>
                <Text style={styles.productPrice}>$29.99</Text>
              </View>
            ))}
          </ScrollView>
        </View>

        {/* Categories */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Shop by Category</Text>
          <View style={styles.categories}>
            {['Flower', 'Edibles', 'Concentrates', 'Accessories'].map((category) => (
              <TouchableOpacity key={category} style={styles.categoryCard}>
                <View style={styles.categoryIcon} />
                <Text style={styles.categoryText}>{category}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.light.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 10,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.light.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.light.gray,
  },
  notificationButton: {
    padding: 8,
  },
  section: {
    padding: 20,
    paddingTop: 0,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.light.text,
    marginBottom: 16,
  },
  quickActions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  actionCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  actionText: {
    fontSize: 12,
    color: Colors.light.text,
    marginTop: 8,
    fontWeight: '500',
  },
  productCard: {
    width: 120,
    marginRight: 12,
  },
  productImage: {
    width: 120,
    height: 120,
    backgroundColor: Colors.light.backgroundSecondary,
    borderRadius: 8,
    marginBottom: 8,
  },
  productName: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.light.text,
  },
  productPrice: {
    fontSize: 14,
    color: Colors.light.primary,
    fontWeight: '600',
  },
  categories: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  categoryCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.light.border,
  },
  categoryIcon: {
    width: 40,
    height: 40,
    backgroundColor: Colors.light.primaryLight,
    borderRadius: 20,
    marginBottom: 8,
  },
  categoryText: {
    fontSize: 12,
    color: Colors.light.text,
    fontWeight: '500',
  },
});