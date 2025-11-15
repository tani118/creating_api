'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Trash2 } from 'lucide-react';
import { Button } from './button';
import { Input } from './input';
import { Card } from './card';
import { chatAPI, generateSessionId, type ChatMessage } from '@/lib/api';

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    setMessages([
      {
        role: 'assistant',
        content: 'Hello! I\'m your train booking assistant. I can help you search for trains, find the best options, and guide you through the booking process. Where would you like to travel?',
        timestamp: new Date(),
      },
    ]);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatAPI.sendMessage(input, sessionId);
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClear = async () => {
    try {
      await chatAPI.clearHistory(sessionId);
      setMessages([
        {
          role: 'assistant',
          content: 'Chat history cleared. How can I help you with train bookings today?',
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-800 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <div className="relative bg-gradient-to-r from-indigo-800/80 to-purple-800/80 backdrop-blur-lg border-b border-white/10 shadow-2xl">
        <div className="max-w-4xl mx-auto px-4 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-2xl blur-lg opacity-75 animate-pulse"></div>
              <div className="relative bg-gradient-to-br from-blue-500 to-purple-600 p-3 rounded-2xl shadow-lg">
                <Bot className="w-7 h-7 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-blue-200 bg-clip-text text-transparent">
                Train Booking Assistant
              </h1>
              <p className="text-sm text-blue-200 flex items-center gap-2">
                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                Powered by AI • Online
              </p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={handleClear} 
            title="Clear chat"
            className="text-white hover:bg-white/10 transition-all duration-300 hover:scale-110"
          >
            <Trash2 className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto relative">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 animate-in slide-in-from-bottom duration-500 ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-110 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-purple-600'
                    : 'bg-gradient-to-br from-indigo-600 to-purple-700'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>
              <Card
                className={`max-w-[80%] transform transition-all hover:scale-[1.02] ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-purple-600 text-white border-none shadow-xl shadow-blue-500/50'
                    : 'bg-white/95 backdrop-blur-sm border-white/20 shadow-xl text-gray-900'
                }`}
              >
                <div className="p-4">
                  <p className={`text-sm whitespace-pre-wrap break-words leading-relaxed ${
                    message.role === 'user' ? 'text-white' : 'text-gray-900'
                  }`}>
                    {message.content}
                  </p>
                  {mounted && (
                    <p
                      className={`text-xs mt-2 flex items-center gap-1 ${
                        message.role === 'user'
                          ? 'text-blue-100'
                          : 'text-gray-500'
                      }`}
                    >
                      <span className="w-1 h-1 rounded-full bg-current"></span>
                      {message.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  )}
                </div>
              </Card>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3 animate-in slide-in-from-bottom">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center shadow-lg">
                <Bot className="w-5 h-5 text-white animate-bounce" />
              </div>
              <Card className="bg-white/95 backdrop-blur-sm border-white/20 shadow-xl text-gray-900">
                <div className="p-4 flex items-center gap-3">
                  <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-purple-600 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-purple-600 rounded-full animate-bounce delay-100"></span>
                    <span className="w-2 h-2 bg-purple-600 rounded-full animate-bounce delay-200"></span>
                  </div>
                  <span className="text-sm text-gray-900 font-medium">AI is thinking...</span>
                </div>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="relative bg-gradient-to-r from-indigo-800/90 to-purple-800/90 backdrop-blur-xl border-t border-white/10 shadow-2xl">
        <div className="max-w-4xl mx-auto px-4 py-5">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask me about trains... (e.g., 'Find trains from Delhi to Mumbai tomorrow')"
                disabled={isLoading}
                className="bg-white/95 backdrop-blur-sm border-white/20 shadow-lg focus:shadow-purple-500/50 focus:border-purple-500 transition-all pr-4 py-6 text-base text-gray-900 placeholder:text-gray-500"
              />
            </div>
            <Button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg shadow-purple-500/50 transform transition-all hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
          <div className="flex items-center justify-center gap-2 mt-3">
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white/10 backdrop-blur-sm rounded-full">
              <span className="text-xs text-blue-200 font-medium">💡 Tip:</span>
              <p className="text-xs text-white/80">
                Use codes like <span className="font-semibold text-white">NDLS</span>, <span className="font-semibold text-white">BCT</span>, <span className="font-semibold text-white">SBC</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
