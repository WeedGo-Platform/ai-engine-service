import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';

const { width } = Dimensions.get('window');
const isDark = true;
const theme = isDark ? Colors.dark : Colors.light;

export function EmptyCart() {
  const router = useRouter();

  const handleStartShopping = () => {
    router.push('/(tabs)/');
  };

  const handleBrowseDeals = () => {
    router.push('/(tabs)/search');
  };

  return (
    <View style={styles.container}>
      {/* Animated gradient background circles */}
      <View style={styles.backgroundDecoration}>
        <LinearGradient
          colors={['rgba(116, 185, 255, 0.1)', 'rgba(139, 233, 253, 0.1)']}
          style={styles.circleOne}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
        <LinearGradient
          colors={['rgba(255, 107, 157, 0.1)', 'rgba(255, 121, 198, 0.1)']}
          style={styles.circleTwo}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
      </View>

      {/* Main content */}
      <View style={styles.content}>
        {/* Icon with gradient background */}
        <View style={styles.iconContainer}>
          <LinearGradient
            colors={['rgba(116, 185, 255, 0.15)', 'rgba(139, 233, 253, 0.15)']}
            style={styles.iconBackground}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
          >
            <Ionicons name="cart-outline" size={80} color={theme.textSecondary} />
          </LinearGradient>
        </View>

        {/* Title and subtitle */}
        <Text style={styles.title}>Your cart awaits</Text>
        <Text style={styles.subtitle}>
          Discover amazing products and exclusive deals
        </Text>

        {/* Action buttons */}
        <View style={styles.buttonContainer}>
          <TouchableOpacity
            onPress={handleStartShopping}
            activeOpacity={0.9}
            style={styles.primaryButtonWrapper}
          >
            <LinearGradient
              colors={['#74B9FF', '#8BE9FD']}
              style={styles.primaryButton}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Ionicons name="sparkles" size={20} color="white" />
              <Text style={styles.primaryButtonText}>Start Shopping</Text>
            </LinearGradient>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleBrowseDeals}
            activeOpacity={0.8}
            style={styles.secondaryButton}
          >
            <Ionicons name="search" size={20} color={theme.primary} />
            <Text style={styles.secondaryButtonText}>Browse Deals</Text>
          </TouchableOpacity>
        </View>

        {/* Suggestion cards */}
        <View style={styles.suggestionsContainer}>
          <Text style={styles.suggestionsTitle}>Popular Categories</Text>
          <View style={styles.categoriesRow}>
            {[
              { icon: 'leaf', label: 'Flower', color: Gradients.sativa },
              { icon: 'nutrition', label: 'Edibles', color: Gradients.indica },
              { icon: 'water', label: 'Concentrates', color: Gradients.hybrid },
            ].map((category, index) => (
              <TouchableOpacity
                key={index}
                onPress={() => router.push('/(tabs)/search')}
                activeOpacity={0.7}
              >
                <LinearGradient
                  colors={category.color}
                  style={styles.categoryCard}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <Ionicons name={category.icon as any} size={28} color="white" />
                  <Text style={styles.categoryLabel}>{category.label}</Text>
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Bottom hint */}
        <View style={styles.hintContainer}>
          <LinearGradient
            colors={['rgba(255, 193, 7, 0.1)', 'rgba(255, 152, 0, 0.1)']}
            style={styles.hintBackground}
          >
            <Ionicons name="information-circle" size={20} color="#FFA000" />
            <Text style={styles.hintText}>
              Free delivery on orders over $50
            </Text>
          </LinearGradient>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  backgroundDecoration: {
    position: 'absolute',
    width: '100%',
    height: '100%',
  },
  circleOne: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    top: -100,
    right: -100,
  },
  circleTwo: {
    position: 'absolute',
    width: 250,
    height: 250,
    borderRadius: 125,
    bottom: -50,
    left: -50,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    width: '100%',
  },
  iconContainer: {
    marginBottom: 32,
  },
  iconBackground: {
    width: 140,
    height: 140,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    color: theme.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: theme.textSecondary,
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 20,
  },
  buttonContainer: {
    width: '100%',
    gap: 16,
    marginBottom: 48,
  },
  primaryButtonWrapper: {
    width: '100%',
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    borderRadius: BorderRadius.xxl,
    gap: 10,
    ...Shadows.colorful,
  },
  primaryButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: BorderRadius.xxl,
    backgroundColor: theme.glass,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    gap: 8,
    ...Shadows.small,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.primary,
  },
  suggestionsContainer: {
    width: '100%',
    marginBottom: 32,
  },
  suggestionsTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
    marginBottom: 16,
  },
  categoriesRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  categoryCard: {
    width: (width - 72) / 3,
    aspectRatio: 1,
    borderRadius: BorderRadius.xl,
    justifyContent: 'center',
    alignItems: 'center',
    ...Shadows.medium,
  },
  categoryLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: 'white',
    marginTop: 8,
  },
  hintContainer: {
    position: 'absolute',
    bottom: 40,
    width: '100%',
    paddingHorizontal: 24,
  },
  hintBackground: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: BorderRadius.xl,
    gap: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 193, 7, 0.3)',
  },
  hintText: {
    flex: 1,
    fontSize: 14,
    color: theme.text,
    fontWeight: '500',
  },
});