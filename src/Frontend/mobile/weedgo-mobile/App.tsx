import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { ThemeProvider } from './components/templates/ThemeProvider';
import { TemplateTestScreen } from './screens/TemplateTestScreen';

export default function App() {
  return (
    <ThemeProvider defaultTemplate="pot-palace">
      <StatusBar style="auto" />
      <TemplateTestScreen />
    </ThemeProvider>
  );
}
