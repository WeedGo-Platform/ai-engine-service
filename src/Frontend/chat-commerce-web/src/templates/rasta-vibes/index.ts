// Export the template provider
export { RastaVibesTemplateProvider } from './provider';

// Export theme
export { rastaVibesTheme } from './theme';

// Export layout
export { Layout } from './layouts/Layout';

// Export style provider
export { StyleProvider } from './styles/StyleProvider';

// Export types
export * from './types';

// Export all components for individual use if needed
export { default as TopMenuBar } from './components/layout/TopMenuBar';
export { default as ConfigurationPanel } from './components/panels/ConfigurationPanel';
export { default as ConfigToggleButton } from './components/common/ConfigToggleButton';
export { default as HamburgerMenu } from './components/layout/HamburgerMenu';
export { default as TemplateSwitcher } from './components/layout/TemplateSwitcher';
export { default as ChatHeader } from './components/chat/ChatHeader';
export { default as ChatMessages } from './components/chat/ChatMessages';
export { default as ChatInputArea } from './components/chat/ChatInputArea';
export { default as AIChatBubble } from './components/chat/AIChatBubble';
export { default as UserChatBubble } from './components/chat/UserChatBubble';
export { default as ChatMetadata } from './components/chat/ChatMetadata';
export { default as TextInputWindow } from './components/chat/TextInputWindow';
export { default as TranscriptWindow } from './components/chat/TranscriptWindow';
export { default as ChatButton } from './components/chat/ChatButton';
export { default as SpeakerButton } from './components/chat/SpeakerButton';
export { default as MicrophoneButton } from './components/chat/MicrophoneButton';
export { default as Login } from './components/auth/Login';
export { default as Register } from './components/auth/Register';
export { default as Notification } from './components/common/Notification';
export { default as LoadingSpinner } from './components/common/LoadingSpinner';
export { default as ErrorBoundary } from './components/common/ErrorBoundary';
export { default as Button } from './components/ui/Button';
export { default as Input } from './components/ui/Input';
export { default as Select } from './components/ui/Select';
export { default as Modal } from './components/ui/Modal';
export { default as Card } from './components/ui/Card';
export { default as Badge } from './components/ui/Badge';
export { default as AgeGate } from './components/legal/AgeGate';
export { default as CookieDisclaimer } from './components/legal/CookieDisclaimer';