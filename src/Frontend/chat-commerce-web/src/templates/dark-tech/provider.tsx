import { BaseTemplateProvider } from '../../core/providers/template.provider';
import type {
  ILayout,
  IStyleProvider,
  ITheme,
  TemplateComponents,
} from '../../core/contracts/template.contracts';

// Import theme
import { darkTechTheme } from './theme';

// Import layout
import { Layout } from './layouts/Layout';

// Import styles
import { StyleProvider } from './styles/StyleProvider';

// Import components
import TopMenuBar from './components/layout/TopMenuBar';
import ConfigurationPanel from './components/panels/ConfigurationPanel';
import ConfigToggleButton from './components/common/ConfigToggleButton';
import HamburgerMenu from './components/layout/HamburgerMenu';
import TemplateSwitcher from './components/layout/TemplateSwitcher';
import ChatHeader from './components/chat/ChatHeader';
import ChatMessages from './components/chat/ChatMessages';
import ChatInputArea from './components/chat/ChatInputArea';
import LoginForm from './components/auth/Login';
import RegisterForm from './components/auth/Register';
import Notification from './components/common/Notification';
import LoadingSpinner from './components/common/LoadingSpinner';
import ErrorBoundary from './components/common/ErrorBoundary';

// Import granular chat components
import AIChatBubble from './components/chat/AIChatBubble';
import UserChatBubble from './components/chat/UserChatBubble';
import ChatMetadata from './components/chat/ChatMetadata';
import TextInputWindow from './components/chat/TextInputWindow';
import TranscriptWindow from './components/chat/TranscriptWindow';
import ChatButton from './components/chat/ChatButton';
import SpeakerButton from './components/chat/SpeakerButton';
import MicrophoneButton from './components/chat/MicrophoneButton';

// Import UI components
import Button from './components/ui/Button';
import Input from './components/ui/Input';
import Select from './components/ui/Select';
import Modal from './components/ui/Modal';
import Card from './components/ui/Card';
import Badge from './components/ui/Badge';
import Scrollbar from './components/ui/Scrollbar';

// Import legal components
import AgeGate from './components/legal/AgeGate';
import CookieDisclaimer from './components/legal/CookieDisclaimer';

// Import product components
import ProductDetails from './components/product/ProductDetails';
import ProductRecommendations from './components/product/ProductRecommendations';
import QuantitySelector from './components/product/QuantitySelector';


export class DarkTechTemplateProvider extends BaseTemplateProvider {
  private components: TemplateComponents;
  private layout: ILayout;
  private styles: IStyleProvider;

  constructor() {
    super('dark-tech');
    
    // Initialize components
    this.components = {
      TopMenuBar: TopMenuBar as any,
      ConfigurationPanel: ConfigurationPanel as any,
      ConfigToggleButton: ConfigToggleButton as any,
      HamburgerMenu: HamburgerMenu as any,
      TemplateSwitcher: TemplateSwitcher as any,
      ChatHeader: ChatHeader as any,
      ChatMessages: ChatMessages as any,
      ChatInputArea: ChatInputArea as any,
      AIChatBubble: AIChatBubble as any,
      UserChatBubble: UserChatBubble as any,
      ChatMetadata: ChatMetadata as any,
      TextInputWindow: TextInputWindow as any,
      TranscriptWindow: TranscriptWindow as any,
      ChatButton: ChatButton as any,
      SpeakerButton: SpeakerButton as any,
      MicrophoneButton: MicrophoneButton as any,
      Login: LoginForm as any,
      Register: RegisterForm as any,
      Notification: Notification as any,
      LoadingSpinner: LoadingSpinner as any,
      ErrorBoundary: ErrorBoundary as any,
      Button: Button as any,
      Input: Input as any,
      Select: Select as any,
      Modal: Modal as any,
      Card: Card as any,
      Badge: Badge as any,
      Scrollbar: Scrollbar as any,
      AgeGate: AgeGate as any,
      CookieDisclaimer: CookieDisclaimer as any,
      ProductDetails: ProductDetails as any,
      ProductRecommendations: ProductRecommendations as any,
      QuantitySelector: QuantitySelector as any,
    };
    
    // Initialize layout
    this.layout = Layout;
    
    // Initialize styles
    this.styles = new StyleProvider();
  }

  getComponent<T extends keyof TemplateComponents>(
    component: T
  ): TemplateComponents[T] {
    return this.components[component];
  }

  getLayout(): ILayout {
    return this.layout;
  }

  getStyles(): IStyleProvider {
    return this.styles;
  }

  getTheme(): ITheme {
    return darkTechTheme;
  }
}