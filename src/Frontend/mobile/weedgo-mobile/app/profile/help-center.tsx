import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Linking,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';

interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
}

const faqs: FAQ[] = [
  {
    id: '1',
    category: 'Orders',
    question: 'How do I track my order?',
    answer: 'You can track your order by going to the Orders tab and selecting your active order. Real-time tracking information will be displayed including driver location and estimated arrival time.',
  },
  {
    id: '2',
    category: 'Orders',
    question: 'Can I cancel or modify my order?',
    answer: 'Orders can be cancelled within 5 minutes of placing them. After that, please contact support for assistance. Modifications are not available once an order is confirmed.',
  },
  {
    id: '3',
    category: 'Delivery',
    question: 'What are the delivery hours?',
    answer: 'Delivery hours vary by store location. You can check the specific hours for your selected store on the store details page. Most stores offer delivery between 10 AM and 10 PM.',
  },
  {
    id: '4',
    category: 'Delivery',
    question: 'Is there a minimum order for delivery?',
    answer: 'Yes, minimum order amounts vary by delivery zone. The minimum order for your area will be displayed at checkout.',
  },
  {
    id: '5',
    category: 'Payment',
    question: 'What payment methods are accepted?',
    answer: 'We accept cash, debit cards, and credit cards. Payment is collected upon delivery or pickup.',
  },
  {
    id: '6',
    category: 'Payment',
    question: 'Is tipping expected?',
    answer: 'Tipping is optional but appreciated. You can add a tip during checkout or give cash directly to your delivery driver.',
  },
  {
    id: '7',
    category: 'Account',
    question: 'How do I verify my age?',
    answer: 'Age verification is required for all customers. You can verify your age in the Profile settings by providing your date of birth. Additional ID verification may be required at delivery.',
  },
  {
    id: '8',
    category: 'Account',
    question: 'How do I update my delivery address?',
    answer: 'Go to Profile > Edit Profile > Manage Addresses to add, edit, or remove delivery addresses.',
  },
  {
    id: '9',
    category: 'Products',
    question: 'How do I find products in stock?',
    answer: 'All products shown for your selected store are currently in stock. You can use filters to narrow down your search by category, brand, or other preferences.',
  },
  {
    id: '10',
    category: 'Products',
    question: 'Can I return or exchange products?',
    answer: 'Due to regulations, cannabis products cannot be returned or exchanged once they leave the store. Please review your order carefully before confirming.',
  },
];

export default function HelpCenterScreen() {
  const router = useRouter();
  const isDark = false;
  const theme = isDark ? Colors.dark : Colors.light;

  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFAQ, setExpandedFAQ] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = Array.from(new Set(faqs.map(f => f.category)));

  const filteredFAQs = faqs.filter(faq => {
    const matchesSearch = searchQuery === '' ||
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !selectedCategory || faq.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const handleContact = (method: 'phone' | 'email' | 'chat') => {
    switch (method) {
      case 'phone':
        Linking.openURL('tel:1-800-WEEDGO');
        break;
      case 'email':
        Linking.openURL('mailto:support@weedgo.com?subject=Help Request');
        break;
      case 'chat':
        router.push('/(tabs)/chat');
        break;
    }
  };

  const toggleFAQ = (id: string) => {
    setExpandedFAQ(expandedFAQ === id ? null : id);
  };

  return (
    <>
      <Stack.Screen
        options={{
          title: 'Help Center',
          headerShown: true,
          headerStyle: {
            backgroundColor: theme.background,
          },
          headerTintColor: theme.primary,
          headerTitleStyle: {
            fontWeight: '600',
          },
          headerLeft: () => (
            <TouchableOpacity onPress={() => router.back()}>
              <Ionicons name="arrow-back" size={24} color={theme.primary} />
            </TouchableOpacity>
          ),
        }}
      />

      <LinearGradient
        colors={[theme.gradientStart, theme.gradientMid, theme.gradientEnd]}
        style={styles.gradientContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 0.5, y: 1 }}
      >
        <SafeAreaView style={styles.container}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Search Bar */}
            <View style={styles.searchContainer}>
              <View style={[styles.searchBar, { backgroundColor: theme.card }]}>
                <Ionicons name="search" size={20} color={theme.textSecondary} />
                <TextInput
                  style={[styles.searchInput, { color: theme.text }]}
                  placeholder="Search for help..."
                  placeholderTextColor={theme.textSecondary}
                  value={searchQuery}
                  onChangeText={setSearchQuery}
                />
                {searchQuery.length > 0 && (
                  <TouchableOpacity onPress={() => setSearchQuery('')}>
                    <Ionicons name="close-circle" size={20} color={theme.textSecondary} />
                  </TouchableOpacity>
                )}
              </View>
            </View>

            {/* Quick Contact */}
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>Need Help?</Text>
              <View style={styles.contactGrid}>
                <TouchableOpacity
                  style={[styles.contactCard, { backgroundColor: theme.card }]}
                  onPress={() => handleContact('chat')}
                >
                  <View style={[styles.contactIcon, { backgroundColor: theme.primary + '20' }]}>
                    <Ionicons name="chatbubbles" size={24} color={theme.primary} />
                  </View>
                  <Text style={[styles.contactTitle, { color: theme.text }]}>Live Chat</Text>
                  <Text style={[styles.contactSubtitle, { color: theme.textSecondary }]}>
                    Chat with AI assistant
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.contactCard, { backgroundColor: theme.card }]}
                  onPress={() => handleContact('phone')}
                >
                  <View style={[styles.contactIcon, { backgroundColor: theme.success + '20' }]}>
                    <Ionicons name="call" size={24} color={theme.success} />
                  </View>
                  <Text style={[styles.contactTitle, { color: theme.text }]}>Call Us</Text>
                  <Text style={[styles.contactSubtitle, { color: theme.textSecondary }]}>
                    1-800-WEEDGO
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.contactCard, { backgroundColor: theme.card }]}
                  onPress={() => handleContact('email')}
                >
                  <View style={[styles.contactIcon, { backgroundColor: theme.warning + '20' }]}>
                    <Ionicons name="mail" size={24} color={theme.warning} />
                  </View>
                  <Text style={[styles.contactTitle, { color: theme.text }]}>Email</Text>
                  <Text style={[styles.contactSubtitle, { color: theme.textSecondary }]}>
                    24-48hr response
                  </Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Category Filter */}
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.categoryContainer}
            >
              <TouchableOpacity
                style={[
                  styles.categoryChip,
                  {
                    backgroundColor: !selectedCategory ? theme.primary : theme.card,
                    borderColor: theme.primary,
                  },
                ]}
                onPress={() => setSelectedCategory(null)}
              >
                <Text
                  style={[
                    styles.categoryChipText,
                    { color: !selectedCategory ? '#fff' : theme.text },
                  ]}
                >
                  All
                </Text>
              </TouchableOpacity>
              {categories.map(category => (
                <TouchableOpacity
                  key={category}
                  style={[
                    styles.categoryChip,
                    {
                      backgroundColor: selectedCategory === category ? theme.primary : theme.card,
                      borderColor: theme.primary,
                    },
                  ]}
                  onPress={() => setSelectedCategory(category)}
                >
                  <Text
                    style={[
                      styles.categoryChipText,
                      { color: selectedCategory === category ? '#fff' : theme.text },
                    ]}
                  >
                    {category}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            {/* FAQs */}
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>
                Frequently Asked Questions
              </Text>

              {filteredFAQs.length === 0 ? (
                <View style={[styles.emptyState, { backgroundColor: theme.card }]}>
                  <Ionicons name="help-circle-outline" size={48} color={theme.textSecondary} />
                  <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                    No FAQs found matching your search
                  </Text>
                </View>
              ) : (
                filteredFAQs.map(faq => (
                  <TouchableOpacity
                    key={faq.id}
                    style={[styles.faqCard, { backgroundColor: theme.card }]}
                    onPress={() => toggleFAQ(faq.id)}
                  >
                    <View style={styles.faqHeader}>
                      <View style={styles.faqQuestionContainer}>
                        <Text style={[styles.faqCategory, { color: theme.primary }]}>
                          {faq.category}
                        </Text>
                        <Text style={[styles.faqQuestion, { color: theme.text }]}>
                          {faq.question}
                        </Text>
                      </View>
                      <Ionicons
                        name={expandedFAQ === faq.id ? 'chevron-up' : 'chevron-down'}
                        size={20}
                        color={theme.textSecondary}
                      />
                    </View>
                    {expandedFAQ === faq.id && (
                      <Text style={[styles.faqAnswer, { color: theme.textSecondary }]}>
                        {faq.answer}
                      </Text>
                    )}
                  </TouchableOpacity>
                ))
              )}
            </View>

            {/* Additional Resources */}
            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>Resources</Text>

              <TouchableOpacity
                style={[styles.resourceCard, { backgroundColor: theme.card }]}
                onPress={() => router.push('/profile/terms-of-service')}
              >
                <Ionicons name="document-text-outline" size={24} color={theme.primary} />
                <Text style={[styles.resourceText, { color: theme.text }]}>
                  Terms of Service
                </Text>
                <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.resourceCard, { backgroundColor: theme.card }]}
                onPress={() => router.push('/profile/privacy-policy')}
              >
                <Ionicons name="shield-checkmark-outline" size={24} color={theme.primary} />
                <Text style={[styles.resourceText, { color: theme.text }]}>
                  Privacy Policy
                </Text>
                <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.resourceCard, { backgroundColor: theme.card }]}
                onPress={() => Linking.openURL('https://weedgo.com/community-guidelines')}
              >
                <Ionicons name="people-outline" size={24} color={theme.primary} />
                <Text style={[styles.resourceText, { color: theme.text }]}>
                  Community Guidelines
                </Text>
                <Ionicons name="chevron-forward" size={20} color={theme.textSecondary} />
              </TouchableOpacity>
            </View>
          </ScrollView>
        </SafeAreaView>
      </LinearGradient>
    </>
  );
}

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  searchContainer: {
    padding: 16,
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: BorderRadius.large,
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 8,
    ...Shadows.small,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  contactGrid: {
    flexDirection: 'row',
    gap: 12,
  },
  contactCard: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    borderRadius: BorderRadius.large,
    ...Shadows.small,
  },
  contactIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  contactTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  contactSubtitle: {
    fontSize: 12,
    textAlign: 'center',
  },
  categoryContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
    marginRight: 8,
  },
  categoryChipText: {
    fontSize: 14,
    fontWeight: '500',
  },
  faqCard: {
    marginBottom: 12,
    borderRadius: BorderRadius.large,
    padding: 16,
    ...Shadows.small,
  },
  faqHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  faqQuestionContainer: {
    flex: 1,
    marginRight: 8,
  },
  faqCategory: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  faqQuestion: {
    fontSize: 16,
    fontWeight: '500',
  },
  faqAnswer: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 12,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    borderRadius: BorderRadius.large,
    ...Shadows.small,
  },
  emptyText: {
    fontSize: 14,
    marginTop: 12,
    textAlign: 'center',
  },
  resourceCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: BorderRadius.large,
    marginBottom: 12,
    ...Shadows.small,
  },
  resourceText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 12,
  },
});