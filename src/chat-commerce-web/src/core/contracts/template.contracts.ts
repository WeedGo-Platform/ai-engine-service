import type { ReactNode } from 'react';
import type { Message, AIConfig, VoiceSettings } from '../../types';

// Template Provider Contract
export interface ITemplateProvider {
  name: string;
  getComponent<T extends keyof TemplateComponents>(
    component: T
  ): TemplateComponents[T];
  getLayout(): ILayout;
  getStyles(): IStyleProvider;
  getTheme(): ITheme;
}

// Component Contracts
export interface TemplateComponents {
  // Layout Components
  TopMenuBar: ITopMenuBarComponent;
  ConfigurationPanel: IConfigurationPanelComponent;
  ConfigToggleButton: IConfigToggleButtonComponent;
  
  // Chat Components
  ChatHeader: IChatHeaderComponent;
  ChatMessages: IChatMessagesComponent;
  ChatInputArea: IChatInputAreaComponent;
  
  // Granular Chat Components
  AIChatBubble: IAIChatBubbleComponent;
  UserChatBubble: IUserChatBubbleComponent;
  ChatMetadata: IChatMetadataComponent;
  TextInputWindow: ITextInputWindowComponent;
  TranscriptWindow: ITranscriptWindowComponent;
  ChatButton: IChatButtonComponent;
  SpeakerButton: ISpeakerButtonComponent;
  MicrophoneButton: IMicrophoneButtonComponent;
  
  // Auth Components
  LoginForm: ILoginFormComponent;
  RegisterForm: IRegisterFormComponent;
  
  // Common Components
  Notification: INotificationComponent;
  LoadingSpinner: ILoadingSpinnerComponent;
  ErrorBoundary: IErrorBoundaryComponent;
  
  // UI Components
  Button: IButtonComponent;
  Input: IInputComponent;
  Select: ISelectComponent;
  Modal: IModalComponent;
  Card: ICardComponent;
  Badge: IBadgeComponent;
}

// Layout Contract
export interface ILayout {
  (props: LayoutProps): ReactNode;
}

export interface LayoutProps {
  children: ReactNode;
  theme?: string;
}

// Component Interfaces
export interface ITopMenuBarComponent {
  (props: TopMenuBarProps): ReactNode;
}

export interface TopMenuBarProps {
  onShowLogin: () => void;
  onShowRegister: () => void;
  onLogout: () => void;
  isLoggedIn: boolean;
  onTemplateChange?: (template: string) => void;
  currentTemplate?: string;
  availableTemplates?: string[];
}

export interface IConfigurationPanelComponent {
  (props: ConfigurationPanelProps): ReactNode;
}

export interface ConfigurationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  config: AIConfig;
  onConfigChange: (config: Partial<AIConfig>) => void;
  voiceSettings: VoiceSettings;
  onVoiceChange: (settings: Partial<VoiceSettings>) => void;
  availableVoices: Array<{ id: string; name: string }>;
  onTestVoice: () => void;
  usageStats: {
    inputTokens: number;
    outputTokens: number;
    totalCost: number;
  };
}

export interface IConfigToggleButtonComponent {
  (props: ConfigToggleButtonProps): ReactNode;
}

export interface ConfigToggleButtonProps {
  isPanelOpen: boolean;
  onClick: () => void;
}

export interface IChatHeaderComponent {
  (props: ChatHeaderProps): ReactNode;
}

export interface ChatHeaderProps {
  isModelLoaded: boolean;
  isSending: boolean;
  onNewConversation: () => void;
  onTogglePanel: () => void;
}

export interface IChatMessagesComponent {
  (props: ChatMessagesProps): ReactNode;
}

export interface ChatMessagesProps {
  messages: Message[];
  isTyping: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

export interface IChatInputAreaComponent {
  (props: ChatInputAreaProps): ReactNode;
}

export interface ChatInputAreaProps {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onVoiceRecord: () => void;
  isModelLoaded: boolean;
  isSending: boolean;
  isRecording: boolean;
  voiceSettings: VoiceSettings;
}

export interface ILoginFormComponent {
  (props: LoginFormProps): ReactNode;
}

export interface LoginFormProps {
  onClose: () => void;
  onSubmit: (data: { email: string; password?: string; otp?: string }) => Promise<void>;
  onRegister: () => void;
}

export interface IRegisterFormComponent {
  (props: RegisterFormProps): ReactNode;
}

export interface RegisterFormProps {
  onClose: () => void;
  onSubmit: (data: any) => Promise<void>;
  onLogin: () => void;
}

export interface INotificationComponent {
  (props: NotificationProps): ReactNode;
}

export interface NotificationProps {
  show: boolean;
  message: string;
}

export interface ILoadingSpinnerComponent {
  (props: LoadingSpinnerProps): ReactNode;
}

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export interface IErrorBoundaryComponent {
  new (props: ErrorBoundaryProps): React.Component<ErrorBoundaryProps, ErrorBoundaryState>;
}

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// UI Component Interfaces
export interface IButtonComponent {
  (props: ButtonProps): ReactNode;
}

export interface ButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export interface IInputComponent {
  (props: InputProps): ReactNode;
}

export interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'date';
  value?: string | number;
  placeholder?: string;
  label?: string;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  onChange?: (value: string) => void;
  className?: string;
}

export interface ISelectComponent {
  (props: SelectProps): ReactNode;
}

export interface SelectProps {
  options: Array<{ value: string; label: string }>;
  value?: string;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
  onChange?: (value: string) => void;
  className?: string;
}

export interface IModalComponent {
  (props: ModalProps): ReactNode;
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export interface ICardComponent {
  (props: CardProps): ReactNode;
}

export interface CardProps {
  children: ReactNode;
  variant?: 'elevated' | 'outlined' | 'filled';
  className?: string;
}

export interface IBadgeComponent {
  (props: BadgeProps): ReactNode;
}

export interface BadgeProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// Granular Chat Component Interfaces
export interface IAIChatBubbleComponent {
  (props: AIChatBubbleProps): ReactNode;
}

export interface AIChatBubbleProps {
  content: string;
  timestamp?: Date;
  isTyping?: boolean;
  personality?: string;
  agent?: string;
}

export interface IUserChatBubbleComponent {
  (props: UserChatBubbleProps): ReactNode;
}

export interface UserChatBubbleProps {
  content: string;
  timestamp?: Date;
}

export interface IChatMetadataComponent {
  (props: ChatMetadataProps): ReactNode;
}

export interface ChatMetadataProps {
  timestamp: Date;
  responseTime?: number;
  tokens?: number;
  agent?: string;
  personality?: string;
  toolsUsed?: string[];
}

export interface ITextInputWindowComponent {
  (props: TextInputWindowProps): ReactNode;
}

export interface TextInputWindowProps {
  value: string;
  onChange: (value: string) => void;
  onKeyPress: (e: React.KeyboardEvent) => void;
  placeholder?: string;
  disabled?: boolean;
  inputRef?: React.RefObject<HTMLInputElement>;
}

export interface ITranscriptWindowComponent {
  (props: TranscriptWindowProps): ReactNode;
}

export interface TranscriptWindowProps {
  children: ReactNode;
  isModelLoaded: boolean;
  isEmpty?: boolean;
  messagesEndRef?: React.RefObject<HTMLDivElement>;
}

export interface IChatButtonComponent {
  (props: ChatButtonProps): ReactNode;
}

export interface ChatButtonProps {
  onClick: () => void;
  disabled?: boolean;
  isSending?: boolean;
}

export interface ISpeakerButtonComponent {
  (props: SpeakerButtonProps): ReactNode;
}

export interface SpeakerButtonProps {
  isEnabled: boolean;
  isSpeaking?: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export interface IMicrophoneButtonComponent {
  (props: MicrophoneButtonProps): ReactNode;
}

export interface MicrophoneButtonProps {
  isRecording: boolean;
  onClick: () => void;
  disabled?: boolean;
}

// Style Provider Contract
export interface IStyleProvider {
  getGlobalStyles(): string;
  getComponentStyles(component: string): string;
}

// Theme Contract
export interface ITheme {
  name: string;
  mode: 'light' | 'dark';
  colors: IThemeColors;
  typography: IThemeTypography;
  spacing: IThemeSpacing;
  borderRadius: IThemeBorderRadius;
  shadows: IThemeShadows;
}

export interface IThemeColors {
  primary: string;
  primaryLight: string;
  primaryDark: string;
  secondary: string;
  accent: string;
  
  success: string;
  warning: string;
  error: string;
  info: string;
  
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  
  // Chat specific
  userMessage: string;
  assistantMessage: string;
  systemMessage: string;
}

export interface IThemeTypography {
  fontFamily: {
    body: string;
    heading: string;
    mono: string;
  };
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  fontWeight: {
    normal: number;
    medium: number;
    semibold: number;
    bold: number;
  };
}

export interface IThemeSpacing {
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  '2xl': string;
  '3xl': string;
}

export interface IThemeBorderRadius {
  sm: string;
  md: string;
  lg: string;
  xl: string;
  full: string;
}

export interface IThemeShadows {
  sm: string;
  md: string;
  lg: string;
  xl: string;
  '2xl': string;
}

// Template Factory
export interface ITemplateFactory {
  create(templateName: string): ITemplateProvider;
  register(templateName: string, provider: ITemplateProvider): void;
  getAvailableTemplates(): string[];
}