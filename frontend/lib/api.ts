import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  session_id: string;
  error?: string;
}

export const chatAPI = {
  sendMessage: async (message: string, sessionId: string): Promise<ChatResponse> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message,
        session_id: sessionId,
      });
      return response.data;
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  },

  clearHistory: async (sessionId: string): Promise<void> => {
    try {
      await axios.post(`${API_BASE_URL}/chat/clear`, {
        session_id: sessionId,
      });
    } catch (error) {
      console.error('Clear history error:', error);
      throw error;
    }
  },
};

export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};
