import React from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  StyleSheet,
  Alert,
} from 'react-native';
import { useTheme } from '../components/templates/ThemeProvider';
import {
  ProductCard,
  Button,
  LoadingSpinner,
  Input,
  ErrorBoundary,
} from '../components/common';
import type { Product } from '../components/common/ProductCard';
import type { TemplateType } from '../components/templates/types';

const sampleProduct: Product = {
  id: '1',
  name: 'Purple Haze Premium Flower',
  brand: 'WeedGo Select',
  price: 45.99,
  thc: 22.5,
  cbd: 0.8,
  category: 'flower',
  inStock: true,
  image: 'https://via.placeholder.com/300x200/4CAF50/FFFFFF?text=Purple+Haze',
};

const outOfStockProduct: Product = {
  id: '2',
  name: 'CBD Relief Tincture',
  brand: 'Medical Grade',
  price: 89.99,
  thc: 0.3,
  cbd: 25.0,
  category: 'tincture',
  inStock: false,
  image: 'https://via.placeholder.com/300x200/2196F3/FFFFFF?text=CBD+Tincture',
};

export const TemplateTestScreen: React.FC = () => {
  const { template, setTemplate, colors, spacing, typography } = useTheme();
  const [loading, setLoading] = React.useState(false);
  const [searchText, setSearchText] = React.useState('');

  const handleTemplateChange = async (newTemplate: TemplateType) => {
    setLoading(true);
    await setTemplate(newTemplate);
    setTimeout(() => setLoading(false), 500);
  };

  const templates: TemplateType[] = ['pot-palace', 'modern', 'headless'];

  if (loading) {
    return <LoadingSpinner message="Switching template..." />;
  }

  return (
    <ErrorBoundary>
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={[styles.header, { backgroundColor: colors.primary }]}>
            <Text style={[styles.headerTitle, { color: '#FFFFFF' }]}>
              WeedGo Template System
            </Text>
            <Text style={[styles.headerSubtitle, { color: '#FFFFFF' }]}>
              Current: {template}
            </Text>
          </View>

          {/* Template Switcher */}
          <View style={[styles.section, { padding: spacing.md }]}>
            <Text
              style={[
                styles.sectionTitle,
                { color: colors.text, fontSize: typography.sizes.h2 },
              ]}
            >
              Select Template
            </Text>
            <View style={styles.templateButtons}>
              {templates.map((t) => (
                <Button
                  key={t}
                  title={t.split('-').map(w =>
                    w.charAt(0).toUpperCase() + w.slice(1)
                  ).join(' ')}
                  onPress={() => handleTemplateChange(t)}
                  variant={template === t ? 'primary' : 'secondary'}
                  size="small"
                  style={{ marginHorizontal: 4, marginVertical: 4 }}
                />
              ))}
            </View>
          </View>

          {/* Input Component Test */}
          <View style={[styles.section, { padding: spacing.md }]}>
            <Text
              style={[
                styles.sectionTitle,
                { color: colors.text, fontSize: typography.sizes.h2 },
              ]}
            >
              Input Component
            </Text>
            <Input
              label="Search Products"
              placeholder="Enter product name..."
              value={searchText}
              onChangeText={setSearchText}
            />
            <Input
              label="Email"
              placeholder="user@example.com"
              keyboardType="email-address"
              error="Please enter a valid email"
            />
          </View>

          {/* Button Component Test */}
          <View style={[styles.section, { padding: spacing.md }]}>
            <Text
              style={[
                styles.sectionTitle,
                { color: colors.text, fontSize: typography.sizes.h2 },
              ]}
            >
              Button Components
            </Text>
            <View style={styles.buttonRow}>
              <Button
                title="Primary"
                onPress={() => Alert.alert('Primary Button Pressed')}
                variant="primary"
                style={{ marginRight: 8 }}
              />
              <Button
                title="Secondary"
                onPress={() => Alert.alert('Secondary Button Pressed')}
                variant="secondary"
                style={{ marginRight: 8 }}
              />
              <Button
                title="Danger"
                onPress={() => Alert.alert('Danger Button Pressed')}
                variant="danger"
              />
            </View>
            <Button
              title="Full Width Button"
              onPress={() => Alert.alert('Full Width Button')}
              fullWidth
              style={{ marginTop: 8 }}
            />
            <Button
              title="Loading..."
              onPress={() => {}}
              loading
              fullWidth
              style={{ marginTop: 8 }}
            />
            <Button
              title="Disabled"
              onPress={() => {}}
              disabled
              fullWidth
              style={{ marginTop: 8 }}
            />
          </View>

          {/* Product Card Test */}
          <View style={[styles.section, { padding: spacing.md }]}>
            <Text
              style={[
                styles.sectionTitle,
                { color: colors.text, fontSize: typography.sizes.h2 },
              ]}
            >
              Product Cards
            </Text>
            <View style={styles.productGrid}>
              <View style={styles.productColumn}>
                <ProductCard
                  product={sampleProduct}
                  onPress={() => Alert.alert('Product', sampleProduct.name)}
                  onAddToCart={() =>
                    Alert.alert('Added to Cart', sampleProduct.name)
                  }
                />
              </View>
              <View style={styles.productColumn}>
                <ProductCard
                  product={outOfStockProduct}
                  onPress={() => Alert.alert('Product', outOfStockProduct.name)}
                  onAddToCart={() =>
                    Alert.alert('Out of Stock', outOfStockProduct.name)
                  }
                />
              </View>
            </View>
          </View>

          {/* Loading Spinner Test */}
          <View style={[styles.section, { padding: spacing.md }]}>
            <Text
              style={[
                styles.sectionTitle,
                { color: colors.text, fontSize: typography.sizes.h2 },
              ]}
            >
              Loading States
            </Text>
            <View style={styles.loadingContainer}>
              <View style={styles.loadingItem}>
                <LoadingSpinner size="small" />
                <Text style={[styles.loadingLabel, { color: colors.textSecondary }]}>
                  Small
                </Text>
              </View>
              <View style={styles.loadingItem}>
                <LoadingSpinner size="medium" />
                <Text style={[styles.loadingLabel, { color: colors.textSecondary }]}>
                  Medium
                </Text>
              </View>
              <View style={styles.loadingItem}>
                <LoadingSpinner size="large" />
                <Text style={[styles.loadingLabel, { color: colors.textSecondary }]}>
                  Large
                </Text>
              </View>
            </View>
          </View>

          {/* Theme Info */}
          <View style={[styles.section, { padding: spacing.md }]}>
            <Text
              style={[
                styles.sectionTitle,
                { color: colors.text, fontSize: typography.sizes.h2 },
              ]}
            >
              Current Theme Info
            </Text>
            <View style={styles.themeInfo}>
              <View style={styles.colorRow}>
                <Text style={[styles.colorLabel, { color: colors.text }]}>
                  Primary:
                </Text>
                <View
                  style={[styles.colorSwatch, { backgroundColor: colors.primary }]}
                />
                <Text style={[styles.colorValue, { color: colors.textSecondary }]}>
                  {colors.primary}
                </Text>
              </View>
              <View style={styles.colorRow}>
                <Text style={[styles.colorLabel, { color: colors.text }]}>
                  Secondary:
                </Text>
                <View
                  style={[styles.colorSwatch, { backgroundColor: colors.secondary }]}
                />
                <Text style={[styles.colorValue, { color: colors.textSecondary }]}>
                  {colors.secondary}
                </Text>
              </View>
              <View style={styles.colorRow}>
                <Text style={[styles.colorLabel, { color: colors.text }]}>
                  Accent:
                </Text>
                <View
                  style={[styles.colorSwatch, { backgroundColor: colors.accent }]}
                />
                <Text style={[styles.colorValue, { color: colors.textSecondary }]}>
                  {colors.accent}
                </Text>
              </View>
            </View>
          </View>
        </ScrollView>
      </SafeAreaView>
    </ErrorBoundary>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  header: {
    paddingVertical: 20,
    paddingHorizontal: 16,
    marginBottom: 10,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    fontSize: 16,
    marginTop: 4,
    opacity: 0.9,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontWeight: 'bold',
    marginBottom: 12,
  },
  templateButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  buttonRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  productGrid: {
    flexDirection: 'row',
    marginHorizontal: -8,
  },
  productColumn: {
    flex: 1,
  },
  loadingContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'flex-end',
    minHeight: 100,
  },
  loadingItem: {
    alignItems: 'center',
  },
  loadingLabel: {
    marginTop: 8,
    fontSize: 12,
  },
  themeInfo: {
    marginTop: 8,
  },
  colorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  colorLabel: {
    width: 80,
    fontSize: 14,
  },
  colorSwatch: {
    width: 24,
    height: 24,
    borderRadius: 4,
    marginHorizontal: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  colorValue: {
    fontSize: 12,
    fontFamily: 'monospace',
  },
});