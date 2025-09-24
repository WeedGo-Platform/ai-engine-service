import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';
import { promoService } from '@/services/api/promo';

interface Promotion {
  id: string;
  title: string;
  description: string;
  discountType: 'percentage' | 'fixed' | 'bogo' | 'freebie';
  discountValue?: number;
  code?: string;
  image?: string;
  validFrom: string;
  validTo: string;
  minimumPurchase?: number;
  category?: string;
  isActive: boolean;
  usageLimit?: number;
  usageCount?: number;
}

export default function PromotionsScreen() {
  const router = useRouter();
  const [promotions, setPromotions] = useState<Promotion[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const isDark = false;
  const theme = isDark ? Colors.dark : Colors.light;

  useEffect(() => {
    loadPromotions();
  }, []);

  const loadPromotions = async () => {
    try {
      const data = await promoService.getPromotions();
      // Add some mock promotions for demonstration
      const mockPromos: Promotion[] = [
        {
          id: '1',
          title: 'First Time Customer',
          description: 'Get 20% off your first order',
          discountType: 'percentage',
          discountValue: 20,
          code: 'FIRST20',
          validFrom: new Date().toISOString(),
          validTo: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          isActive: true,
          category: 'new',
        },
        {
          id: '2',
          title: 'Weekend Special',
          description: 'Buy 2 get 1 free on all edibles',
          discountType: 'bogo',
          code: 'WEEKEND',
          validFrom: new Date().toISOString(),
          validTo: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
          isActive: true,
          category: 'limited',
        },
        {
          id: '3',
          title: 'Happy Hour',
          description: '15% off between 4-6 PM',
          discountType: 'percentage',
          discountValue: 15,
          validFrom: new Date().toISOString(),
          validTo: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString(),
          isActive: true,
          category: 'daily',
        },
        {
          id: '4',
          title: 'Loyalty Reward',
          description: '$10 off orders over $50',
          discountType: 'fixed',
          discountValue: 10,
          code: 'LOYAL10',
          minimumPurchase: 50,
          validFrom: new Date().toISOString(),
          validTo: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
          isActive: true,
          category: 'loyalty',
        },
      ];
      setPromotions(data.data || mockPromos);
    } catch (error) {
      console.error('Failed to load promotions:', error);
      // Use mock data on error
      const mockPromos: Promotion[] = [
        {
          id: '1',
          title: 'First Time Customer',
          description: 'Get 20% off your first order',
          discountType: 'percentage',
          discountValue: 20,
          code: 'FIRST20',
          validFrom: new Date().toISOString(),
          validTo: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
          isActive: true,
          category: 'new',
        },
      ];
      setPromotions(mockPromos);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadPromotions();
    setRefreshing(false);
  };

  const copyPromoCode = (code: string) => {
    // In a real app, you would copy to clipboard
    alert(`Promo code "${code}" copied to clipboard!`);
  };

  const getPromoGradient = (category?: string) => {
    switch (category) {
      case 'new':
        return Gradients.primary;
      case 'limited':
        return Gradients.sunset;
      case 'daily':
        return Gradients.ocean;
      case 'loyalty':
        return Gradients.purple;
      default:
        return Gradients.warm;
    }
  };

  const getDiscountText = (promo: Promotion) => {
    switch (promo.discountType) {
      case 'percentage':
        return `${promo.discountValue}% OFF`;
      case 'fixed':
        return `$${promo.discountValue} OFF`;
      case 'bogo':
        return 'BOGO';
      case 'freebie':
        return 'FREE';
      default:
        return 'DEAL';
    }
  };

  const getDaysLeft = (validTo: string) => {
    const days = Math.ceil((new Date(validTo).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
    if (days < 0) return 'Expired';
    if (days === 0) return 'Ends today';
    if (days === 1) return '1 day left';
    return `${days} days left`;
  };

  const categories = [
    { id: 'all', label: 'All Deals', icon: 'pricetag' },
    { id: 'new', label: 'New', icon: 'sparkles' },
    { id: 'limited', label: 'Limited', icon: 'time' },
    { id: 'daily', label: 'Daily', icon: 'today' },
    { id: 'loyalty', label: 'Loyalty', icon: 'heart' },
  ];

  const filteredPromotions = selectedCategory === 'all'
    ? promotions
    : promotions.filter(p => p.category === selectedCategory);

  if (loading) {
    return (
      <LinearGradient
        colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <SafeAreaView style={styles.container}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.primary} />
            <Text style={styles.loadingText}>Loading deals...</Text>
          </View>
        </SafeAreaView>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient
      colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
      style={styles.gradientContainer}
      start={{ x: 0, y: 0 }}
      end={{ x: 0.5, y: 1 }}
    >
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={theme.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Promotions & Deals</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={theme.primary}
            />
          }
          showsVerticalScrollIndicator={false}
        >
          {/* Categories */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.categoriesContainer}
          >
            {categories.map((category) => (
              <TouchableOpacity
                key={category.id}
                style={[
                  styles.categoryChip,
                  selectedCategory === category.id && styles.categoryChipActive,
                ]}
                onPress={() => setSelectedCategory(category.id)}
                activeOpacity={0.8}
              >
                {selectedCategory === category.id ? (
                  <LinearGradient
                    colors={Gradients.primary}
                    style={styles.categoryGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 1 }}
                  >
                    <Ionicons name={category.icon as any} size={16} color="white" />
                    <Text style={styles.categoryTextActive}>{category.label}</Text>
                  </LinearGradient>
                ) : (
                  <>
                    <Ionicons name={category.icon as any} size={16} color={theme.textSecondary} />
                    <Text style={styles.categoryText}>{category.label}</Text>
                  </>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Featured Deal */}
          {filteredPromotions.length > 0 && (
            <TouchableOpacity
              style={styles.featuredCard}
              activeOpacity={0.9}
              onPress={() => copyPromoCode(filteredPromotions[0].code || '')}
            >
              <LinearGradient
                colors={getPromoGradient(filteredPromotions[0].category)}
                style={styles.featuredGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <View style={styles.featuredBadge}>
                  <Text style={styles.featuredBadgeText}>FEATURED</Text>
                </View>
                <View style={styles.featuredContent}>
                  <View style={styles.featuredLeft}>
                    <Text style={styles.featuredDiscount}>
                      {getDiscountText(filteredPromotions[0])}
                    </Text>
                    <Text style={styles.featuredTitle}>{filteredPromotions[0].title}</Text>
                    <Text style={styles.featuredDescription}>
                      {filteredPromotions[0].description}
                    </Text>
                    {filteredPromotions[0].minimumPurchase && (
                      <Text style={styles.featuredMinimum}>
                        Min. purchase: ${filteredPromotions[0].minimumPurchase}
                      </Text>
                    )}
                  </View>
                  <View style={styles.featuredRight}>
                    <View style={styles.codeContainer}>
                      <Text style={styles.codeLabel}>CODE</Text>
                      <Text style={styles.codeText}>{filteredPromotions[0].code}</Text>
                    </View>
                    <Text style={styles.expiryText}>
                      {getDaysLeft(filteredPromotions[0].validTo)}
                    </Text>
                  </View>
                </View>
              </LinearGradient>
            </TouchableOpacity>
          )}

          {/* Promotions List */}
          <View style={styles.promotionsList}>
            {filteredPromotions.slice(1).map((promo) => (
              <TouchableOpacity
                key={promo.id}
                style={styles.promoCard}
                onPress={() => copyPromoCode(promo.code || '')}
                activeOpacity={0.9}
              >
                <LinearGradient
                  colors={['rgba(255, 255, 255, 0.95)', 'rgba(250, 250, 255, 0.9)']}
                  style={styles.promoGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                >
                  <View style={styles.promoHeader}>
                    <LinearGradient
                      colors={getPromoGradient(promo.category)}
                      style={styles.promoDiscountBadge}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 1 }}
                    >
                      <Text style={styles.promoDiscount}>{getDiscountText(promo)}</Text>
                    </LinearGradient>
                    <Text style={styles.promoExpiry}>{getDaysLeft(promo.validTo)}</Text>
                  </View>

                  <Text style={styles.promoTitle}>{promo.title}</Text>
                  <Text style={styles.promoDescription}>{promo.description}</Text>

                  {promo.minimumPurchase && (
                    <Text style={styles.promoMinimum}>
                      Minimum purchase: ${promo.minimumPurchase}
                    </Text>
                  )}

                  {promo.code && (
                    <View style={styles.promoCodeContainer}>
                      <View style={styles.promoCode}>
                        <Text style={styles.promoCodeText}>{promo.code}</Text>
                      </View>
                      <TouchableOpacity
                        style={styles.copyButton}
                        onPress={(e) => {
                          e.stopPropagation();
                          copyPromoCode(promo.code!);
                        }}
                      >
                        <Ionicons name="copy-outline" size={18} color={theme.primary} />
                        <Text style={styles.copyText}>Copy</Text>
                      </TouchableOpacity>
                    </View>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </View>

          {filteredPromotions.length === 0 && (
            <View style={styles.emptyContainer}>
              <Ionicons name="pricetag-outline" size={64} color={theme.textSecondary} />
              <Text style={styles.emptyTitle}>No deals available</Text>
              <Text style={styles.emptyText}>
                Check back later for exciting promotions and discounts
              </Text>
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

const isDark = false;
const theme = isDark ? Colors.dark : Colors.light;

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.text,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  categoriesContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    maxHeight: 50,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BorderRadius.full,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    marginRight: 8,
    borderWidth: 1,
    borderColor: theme.border,
  },
  categoryChipActive: {
    borderColor: 'transparent',
    overflow: 'hidden',
  },
  categoryGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginHorizontal: -16,
    marginVertical: -8,
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.textSecondary,
  },
  categoryTextActive: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
  },
  featuredCard: {
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 20,
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    ...Shadows.colorful,
  },
  featuredGradient: {
    padding: 20,
  },
  featuredBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BorderRadius.md,
  },
  featuredBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: 'white',
    letterSpacing: 0.5,
  },
  featuredContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  featuredLeft: {
    flex: 1,
  },
  featuredDiscount: {
    fontSize: 32,
    fontWeight: '800',
    color: 'white',
    marginBottom: 8,
  },
  featuredTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: 'white',
    marginBottom: 4,
  },
  featuredDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 8,
  },
  featuredMinimum: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  featuredRight: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  codeContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
    marginBottom: 8,
  },
  codeLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: theme.textSecondary,
    marginBottom: 4,
  },
  codeText: {
    fontSize: 18,
    fontWeight: '800',
    color: theme.text,
  },
  expiryText: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.9)',
    fontWeight: '600',
  },
  promotionsList: {
    paddingHorizontal: 16,
  },
  promoCard: {
    marginBottom: 16,
    borderRadius: BorderRadius.xl,
    overflow: 'hidden',
    ...Shadows.medium,
  },
  promoGradient: {
    padding: 16,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.5)',
    borderRadius: BorderRadius.xl,
  },
  promoHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  promoDiscountBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: BorderRadius.full,
  },
  promoDiscount: {
    fontSize: 14,
    fontWeight: '700',
    color: 'white',
  },
  promoExpiry: {
    fontSize: 12,
    color: theme.textSecondary,
    fontWeight: '600',
  },
  promoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.text,
    marginBottom: 4,
  },
  promoDescription: {
    fontSize: 14,
    color: theme.textSecondary,
    marginBottom: 8,
  },
  promoMinimum: {
    fontSize: 12,
    color: theme.textTertiary,
    marginBottom: 12,
  },
  promoCodeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 8,
  },
  promoCode: {
    flex: 1,
    backgroundColor: theme.inputBackground,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: theme.border,
    borderStyle: 'dashed',
  },
  promoCodeText: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.text,
    textAlign: 'center',
  },
  copyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  copyText: {
    fontSize: 14,
    fontWeight: '600',
    color: theme.primary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: theme.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingTop: 100,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
    marginTop: 16,
  },
  emptyText: {
    fontSize: 14,
    color: theme.textSecondary,
    textAlign: 'center',
    marginTop: 8,
  },
});