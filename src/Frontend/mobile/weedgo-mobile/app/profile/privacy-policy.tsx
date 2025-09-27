import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors, BorderRadius, Shadows } from '@/constants/Colors';
import { LinearGradient } from 'expo-linear-gradient';

export default function PrivacyPolicyScreen() {
  const router = useRouter();
  const isDark = false;
  const theme = isDark ? Colors.dark : Colors.light;

  const lastUpdated = 'January 1, 2025';

  return (
    <>
      <Stack.Screen
        options={{
          title: 'Privacy Policy',
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
          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
            <View style={[styles.header, { backgroundColor: theme.card }]}>
              <Text style={[styles.title, { color: theme.text }]}>Privacy Policy</Text>
              <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
                Last updated: {lastUpdated}
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>1. Introduction</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                WeedGo ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our mobile application and services.
              </Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Please read this privacy policy carefully. If you do not agree with the terms of this privacy policy, please do not access the application.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>2. Information We Collect</Text>
              <Text style={[styles.subheading, { color: theme.text }]}>Personal Information</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                We collect information you provide directly to us, such as:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Name and contact information (email, phone number, address)
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Date of birth for age verification
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Government-issued ID for verification purposes
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Payment information (processed securely by payment providers)
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Order history and preferences
                </Text>
              </View>

              <Text style={[styles.subheading, { color: theme.text }]}>Automatically Collected Information</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                When you use our app, we automatically collect:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Device information (type, operating system, unique identifiers)
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Location data (with your permission) for delivery services
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Usage data (pages viewed, features used, time spent)
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Log data (IP address, browser type, access times)
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>3. How We Use Your Information</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                We use the information we collect to:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Process and fulfill your orders
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Verify your age and identity as required by law
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Send order confirmations and delivery updates
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Provide customer support
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Personalize your experience
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Send promotional communications (with your consent)
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Improve our services and develop new features
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Comply with legal obligations
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>4. Information Sharing</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                We do not sell, trade, or rent your personal information. We may share your information with:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Licensed cannabis retailers fulfilling your orders
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Delivery partners providing delivery services
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Payment processors for transaction processing
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Service providers helping us operate our business
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Law enforcement when required by law
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>5. Data Security</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                We implement appropriate technical and organizational security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction. These measures include:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Encryption of data in transit and at rest
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Regular security audits and updates
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Limited access to personal information
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Secure data centers with physical security controls
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>6. Your Rights</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                You have the right to:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Access your personal information
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Correct inaccurate information
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Request deletion of your information
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Object to processing of your information
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Request data portability
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Withdraw consent for marketing communications
                </Text>
              </View>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                To exercise these rights, please contact us using the information provided below.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>7. Data Retention</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                We retain your personal information for as long as necessary to fulfill the purposes outlined in this privacy policy, unless a longer retention period is required by law. Order records are retained for a minimum of 7 years to comply with regulatory requirements.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>8. Children's Privacy</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Our services are not intended for individuals under the age of 19. We do not knowingly collect personal information from children. If you believe we have collected information from a minor, please contact us immediately.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>9. Cookies and Tracking</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                We use cookies and similar tracking technologies to improve your experience, analyze usage, and provide personalized content. You can control cookie preferences through your device settings.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>10. Third-Party Links</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Our app may contain links to third-party websites or services. We are not responsible for the privacy practices or content of these third parties. We encourage you to review their privacy policies.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>11. International Data Transfers</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Your information may be transferred to and processed in countries other than Canada. By using our services, you consent to such transfers. We ensure appropriate safeguards are in place to protect your information.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>12. Changes to This Policy</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                We may update this privacy policy from time to time. We will notify you of material changes by posting the new policy on this page and updating the "Last Updated" date. Your continued use constitutes acceptance of the updated policy.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>13. Contact Us</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                If you have questions about this Privacy Policy or our privacy practices, please contact us:
              </Text>
              <Text style={[styles.contactInfo, { color: theme.text }]}>
                Email: privacy@weedgo.com{'\n'}
                Phone: 1-800-WEEDGO{'\n'}
                Address: 123 Cannabis Street, Toronto, ON M5V 3A9{'\n'}
                Privacy Officer: privacy@weedgo.com
              </Text>
            </View>

            <View style={[styles.footer, { backgroundColor: theme.card }]}>
              <Text style={[styles.footerText, { color: theme.textSecondary }]}>
                Your privacy is important to us. We are committed to protecting your personal information and being transparent about how we use it.
              </Text>
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
  content: {
    paddingBottom: 20,
  },
  header: {
    padding: 20,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: BorderRadius.large,
    ...Shadows.small,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
  },
  section: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  subheading: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 8,
    marginBottom: 8,
  },
  paragraph: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 12,
  },
  list: {
    marginLeft: 8,
    marginBottom: 12,
  },
  listItem: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 8,
  },
  contactInfo: {
    fontSize: 14,
    lineHeight: 22,
    fontWeight: '500',
  },
  footer: {
    padding: 20,
    marginHorizontal: 16,
    marginTop: 20,
    borderRadius: BorderRadius.large,
    ...Shadows.small,
  },
  footerText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
    textAlign: 'center',
  },
});