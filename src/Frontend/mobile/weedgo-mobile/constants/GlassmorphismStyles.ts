import { StyleSheet, Platform } from 'react-native';
import { Colors, BorderRadius, Shadows } from './Colors';

const isDark = true;
const theme = isDark ? Colors.dark : Colors.light;

export const glassChatStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    paddingTop: Platform.OS === 'ios' ? 50 : 16,
    backgroundColor: theme.glass,
    borderBottomWidth: 1,
    borderBottomColor: theme.glassBorder,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.text,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: BorderRadius.full,
    marginLeft: 8,
  },
  connected: {
    backgroundColor: theme.primary,
    shadowColor: theme.primary,
    shadowOpacity: 0.5,
    shadowRadius: 4,
  },
  disconnected: {
    backgroundColor: theme.error,
  },
  clearButton: {
    padding: 8,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  speakerButton: {
    padding: 8,
    marginRight: 8,
  },
  speakerButtonOff: {
    opacity: 0.5,
  },
  keyboardAvoid: {
    flex: 1,
  },
  transcriptIndicator: {
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.lg,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.small,
  },
  transcriptHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  listeningDot: {
    width: 8,
    height: 8,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.error,
    marginRight: 8,
    shadowColor: theme.error,
    shadowOpacity: 0.5,
    shadowRadius: 4,
  },
  transcriptLabel: {
    fontSize: 12,
    color: theme.textSecondary,
    fontWeight: '600',
  },
  transcriptText: {
    fontSize: 14,
    color: theme.text,
    lineHeight: 20,
  },
  messagesList: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 16,
  },
  inputContainer: {
    backgroundColor: theme.glass,
    borderTopWidth: 1,
    borderTopColor: theme.glassBorder,
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingBottom: Platform.OS === 'ios' ? 100 : 80,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: theme.inputBackground,
    borderRadius: BorderRadius.xxl,
    paddingHorizontal: 16,
    paddingVertical: 10,
    minHeight: 48,
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: theme.text,
    maxHeight: 100,
    paddingTop: Platform.OS === 'ios' ? 4 : 0,
    paddingBottom: Platform.OS === 'ios' ? 4 : 0,
  },
  voiceButton: {
    width: 40,
    height: 40,
    borderRadius: BorderRadius.full,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.2)',
  },
  recording: {
    backgroundColor: 'rgba(239, 68, 68, 0.9)',
    borderColor: 'rgba(239, 68, 68, 0.5)',
    ...Shadows.medium,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
    ...Shadows.small,
  },
  sendButtonDisabled: {
    backgroundColor: theme.disabled,
    opacity: 0.5,
  },
});

export const glassHomeStyles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    paddingHorizontal: 16,
    height: 48,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.small,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: theme.text,
    marginLeft: 8,
  },
  cartButton: {
    width: 48,
    height: 48,
    borderRadius: BorderRadius.full,
    backgroundColor: theme.glass,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
});

export const glassButtonStyles = StyleSheet.create({
  primaryButton: {
    backgroundColor: theme.primary,
    borderRadius: BorderRadius.xl,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    ...Shadows.medium,
  },
  secondaryButton: {
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: theme.glassBorder,
  },
  ghostButton: {
    backgroundColor: 'transparent',
    borderRadius: BorderRadius.xl,
    paddingVertical: 14,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: theme.border,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.text,
  },
});

export const glassCardStyles = StyleSheet.create({
  card: {
    backgroundColor: theme.glass,
    borderRadius: BorderRadius.xl,
    padding: 16,
    borderWidth: 1,
    borderColor: theme.glassBorder,
    ...Shadows.medium,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.text,
  },
  cardSubtitle: {
    fontSize: 14,
    color: theme.textSecondary,
    marginTop: 4,
  },
  cardContent: {
    marginTop: 12,
  },
  cardFooter: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: theme.glassBorder,
  },
});