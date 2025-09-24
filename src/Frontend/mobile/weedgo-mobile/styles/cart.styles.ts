import { StyleSheet } from 'react-native';
import { Colors, BorderRadius, Shadows, Gradients } from '@/constants/Colors';

const isDark = false; // Use light theme for colorful design
const theme = isDark ? Colors.dark : Colors.light;

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: theme.textSecondary,
  },
  section: {
    marginTop: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: theme.text,
    marginBottom: 12,
    marginHorizontal: 16,
  },
  itemsList: {
    marginBottom: 8,
  },
  checkoutButton: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 24,
    marginBottom: 16,
    paddingVertical: 18,
    paddingHorizontal: 24,
    borderRadius: BorderRadius.xxl,
    overflow: 'hidden',
    ...Shadows.colorful,
    elevation: 8,
  },
  checkoutButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  checkoutTotal: {
    fontSize: 18,
    fontWeight: '700',
    color: 'white',
    textShadowColor: 'rgba(0, 0, 0, 0.2)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  disabledButton: {
    opacity: 0.7,
  },
  minimumNotice: {
    backgroundColor: theme.warning + '20',
    marginHorizontal: 16,
    marginBottom: 20,
    padding: 14,
    borderRadius: BorderRadius.lg,
    borderLeftWidth: 4,
    borderLeftColor: theme.warning,
    ...Shadows.small,
  },
  minimumNoticeText: {
    fontSize: 14,
    color: theme.text,
    fontWeight: '500',
  },
});