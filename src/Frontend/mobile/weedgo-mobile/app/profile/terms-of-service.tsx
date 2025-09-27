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

export default function TermsOfServiceScreen() {
  const router = useRouter();
  const isDark = false;
  const theme = isDark ? Colors.dark : Colors.light;

  const lastUpdated = 'January 1, 2025';

  return (
    <>
      <Stack.Screen
        options={{
          title: 'Terms of Service',
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
              <Text style={[styles.title, { color: theme.text }]}>Terms of Service</Text>
              <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
                Last updated: {lastUpdated}
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>1. Acceptance of Terms</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                By accessing and using the WeedGo mobile application ("Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this Service.
              </Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                This Service is available only to individuals who are at least 19 years of age (or the legal age in your province/territory). By using this Service, you represent and warrant that you meet this age requirement.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>2. Use License</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Permission is granted to temporarily download one copy of the WeedGo app for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Modify or copy the materials
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Use the materials for any commercial purpose or for any public display
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Attempt to reverse engineer any software contained in the WeedGo app
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • Remove any copyright or other proprietary notations from the materials
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>3. Account Responsibilities</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                You are responsible for maintaining the confidentiality of your account and password, and for restricting access to your device. You agree to accept responsibility for all activities that occur under your account.
              </Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                You must provide accurate, current, and complete information during the registration process and keep your account information up-to-date.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>4. Product Information</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                All cannabis products are for recreational use only. Products have not been analyzed or approved by Health Canada. Products are not for use by or sale to persons under the age of 19 (or legal age in your province).
              </Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Product descriptions, images, and prices are subject to change without notice. We strive for accuracy but cannot guarantee that all information is complete or error-free.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>5. Order and Delivery</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                By placing an order through our Service, you warrant that you are legally capable of entering into binding contracts and are at least 19 years of age.
              </Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Valid government-issued photo identification is required for all deliveries and pickups. We reserve the right to refuse service to anyone who cannot provide valid ID or appears to be intoxicated.
              </Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Delivery times are estimates only and not guaranteed. We are not responsible for delays outside our control.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>6. Returns and Refunds</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Due to the nature of cannabis products and regulatory requirements, all sales are final. Products cannot be returned or exchanged once they have left the store.
              </Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Refunds may be issued at our discretion for orders that were not delivered or in cases of significant product defects. Please contact customer service for assistance.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>7. Privacy Policy</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                Your use of our Service is also governed by our Privacy Policy. Please review our Privacy Policy, which also governs the Service and informs users of our data collection practices.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>8. Prohibited Uses</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                You may not use our Service:
              </Text>
              <View style={styles.list}>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • For any unlawful purpose or to solicit others to perform unlawful acts
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • To violate any international, federal, provincial, or local laws or regulations
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • To transmit any malicious code, viruses, or disruptive technologies
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • To engage in any conduct that restricts or inhibits anyone's use of the Service
                </Text>
                <Text style={[styles.listItem, { color: theme.textSecondary }]}>
                  • To impersonate or attempt to impersonate WeedGo, a WeedGo employee, or another user
                </Text>
              </View>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>9. Disclaimer</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                The materials on WeedGo's app are provided on an 'as is' basis. WeedGo makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>10. Limitations</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                In no event shall WeedGo or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the Service, even if WeedGo has been notified of the possibility of such damage.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>11. Modifications</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                WeedGo may revise these terms of service at any time without notice. By using this Service, you are agreeing to be bound by the then current version of these terms of service.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>12. Governing Law</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                These terms and conditions are governed by and construed in accordance with the laws of Canada and you irrevocably submit to the exclusive jurisdiction of the courts in that location.
              </Text>
            </View>

            <View style={styles.section}>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>13. Contact Information</Text>
              <Text style={[styles.paragraph, { color: theme.textSecondary }]}>
                If you have any questions about these Terms of Service, please contact us at:
              </Text>
              <Text style={[styles.contactInfo, { color: theme.text }]}>
                Email: legal@weedgo.com{'\n'}
                Phone: 1-800-WEEDGO{'\n'}
                Address: 123 Cannabis Street, Toronto, ON M5V 3A9
              </Text>
            </View>

            <View style={[styles.footer, { backgroundColor: theme.card }]}>
              <Text style={[styles.footerText, { color: theme.textSecondary }]}>
                By using the WeedGo app, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
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