import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { IChatMessage } from '@templates/types';

interface ChatState {
  messages: IChatMessage[];
  isTyping: boolean;
  isConnected: boolean;
  sessionId: string | null;
  isOpen: boolean;
}

const initialState: ChatState = {
  messages: [],
  isTyping: false,
  isConnected: false,
  sessionId: null,
  isOpen: false,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage: (state, action: PayloadAction<IChatMessage>) => {
      state.messages.push(action.payload);
    },
    setTyping: (state, action: PayloadAction<boolean>) => {
      state.isTyping = action.payload;
    },
    setConnected: (state, action: PayloadAction<boolean>) => {
      state.isConnected = action.payload;
    },
    setSessionId: (state, action: PayloadAction<string>) => {
      state.sessionId = action.payload;
    },
    clearMessages: (state) => {
      state.messages = [];
    },
    toggleChat: (state) => {
      state.isOpen = !state.isOpen;
    },
    setOpen: (state, action: PayloadAction<boolean>) => {
      state.isOpen = action.payload;
    },
  },
});

export const {
  addMessage,
  setTyping,
  setConnected,
  setSessionId,
  clearMessages,
  toggleChat,
  setOpen,
} = chatSlice.actions;

export default chatSlice.reducer;