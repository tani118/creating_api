'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Trash2, Mic, MicOff } from 'lucide-react';
import { Button } from './button';
import { Input } from './input';
import { Card } from './card';
import { chatAPI, generateSessionId, type ChatMessage } from '@/lib/api';
import { WebSpeechAPI } from '@/lib/webSpeech';

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => generateSessionId());
  const [mounted, setMounted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const webSpeechRef = useRef<WebSpeechAPI | null>(null);

  useEffect(() => {
    setMounted(true);
    // Initialize Web Speech API
    webSpeechRef.current = new WebSpeechAPI();
    setSpeechSupported(webSpeechRef.current.isSupported());
    
    // Only set initial message after mount to avoid hydration issues
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

  const handleVoiceInput = async () => {
    if (!webSpeechRef.current || !speechSupported) {
      alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isRecording) {
      webSpeechRef.current.stopListening();
      setIsRecording(false);
      return;
    }

    try {
      setIsRecording(true);
      const transcript = await webSpeechRef.current.startListening();
      
      if (transcript) {
        setInput(transcript);
      }
    } catch (error: any) {
      console.error('Voice input error:', error);
      if (error.message.includes('not-allowed')) {
        alert('Microphone access denied. Please allow microphone access in your browser settings.');
      } else if (error.message.includes('no-speech')) {
        alert('No speech detected. Please try again.');
      } else {
        alert('Voice input failed. Please try again.');
      }
    } finally {
      setIsRecording(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 relative overflow-hidden">
      {/* Modern Background Pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <div className="relative bg-slate-800/90 backdrop-blur-xl border-b border-slate-700/50">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-400 to-blue-500 rounded-2xl blur-md opacity-60"></div>
              <div className="relative bg-gradient-to-br from-emerald-500 to-blue-600 p-3 rounded-2xl">
                <Bot className="w-7 h-7 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Railway Assistant
              </h1>
              <p className="text-sm text-slate-400 flex items-center gap-2 mt-1">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                AI-powered booking assistant
              </p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={handleClear} 
            title="Clear chat"
            className="text-slate-400 hover:text-white hover:bg-slate-700/50 transition-all rounded-xl"
          >
            <Trash2 className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto relative">
        <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-4 animate-in slide-in-from-bottom duration-500 ${
                message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
              style={{ animationDelay: `${index * 50}ms` }}
            >
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center shadow-lg ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-blue-600 shadow-blue-500/30'
                    : 'bg-gradient-to-br from-emerald-500 to-blue-600 shadow-emerald-500/30'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="w-5 h-5 text-white" />
                ) : (
                  <Bot className="w-5 h-5 text-white" />
                )}
              </div>
              <Card
                className={`max-w-[75%] border-0 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-xl shadow-blue-900/30'
                    : 'bg-slate-800/60 backdrop-blur-sm border border-slate-700/50 shadow-xl shadow-black/20 text-slate-100'
                }`}
              >
                <div className="p-4">
                  <p className={`text-[15px] whitespace-pre-wrap break-words leading-relaxed ${
                    message.role === 'user' ? 'text-white' : 'text-slate-100'
                  }`}>
                    {message.content}
                  </p>
                  {mounted && (
                    <p
                      className={`text-[11px] mt-3 font-medium ${
                        message.role === 'user'
                          ? 'text-blue-200/70'
                          : 'text-slate-400'
                      }`}
                    >
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
            <div className="flex gap-4 animate-in slide-in-from-bottom">
              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-blue-600 flex items-center justify-center shadow-lg shadow-emerald-500/30">
                <Bot className="w-5 h-5 text-white animate-pulse" />
              </div>
              <Card className="bg-slate-800/60 backdrop-blur-sm border border-slate-700/50 shadow-xl shadow-black/20 text-slate-100">
                <div className="p-4 flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-100"></span>
                    <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce delay-200"></span>
                  </div>
                  <span className="text-sm text-slate-300 font-medium">Processing your request...</span>
                </div>
              </Card>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="relative bg-slate-800/90 backdrop-blur-xl border-t border-slate-700/50">
        <div className="max-w-5xl mx-auto px-6 py-6">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Type your message... (e.g., 'Find trains from Delhi to Mumbai tomorrow')"
                disabled={isLoading || isRecording}
                className="bg-slate-900/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 transition-all py-6 text-base rounded-xl"
              />
            </div>
            {speechSupported && (
              <Button
                onClick={handleVoiceInput}
                disabled={isLoading}
                title={isRecording ? "Stop recording" : "Voice input"}
                className={`h-12 w-12 rounded-xl shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95 ${
                  isRecording 
                    ? 'bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 shadow-red-500/40 animate-pulse' 
                    : 'bg-gradient-to-br from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 shadow-emerald-500/40'
                }`}
              >
                {isRecording ? (
                  <MicOff className="w-5 h-5" />
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </Button>
            )}
            <Button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="h-12 w-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 shadow-lg shadow-blue-500/40 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </Button>
          </div>
          <div className="flex items-center justify-center gap-2 mt-4">
            <div className="flex items-center gap-2.5 px-4 py-2 bg-slate-700/30 backdrop-blur-sm rounded-xl border border-slate-600/30">
              <span className="text-xs text-emerald-400 font-semibold">TIP</span>
              <div className="w-1 h-1 rounded-full bg-slate-600"></div>
              <p className="text-xs text-slate-400">
                Quick search with station codes: <span className="text-white font-semibold mx-1">NDLS</span><span className="text-slate-600">•</span><span className="text-white font-semibold mx-1">BCT</span><span className="text-slate-600">•</span><span className="text-white font-semibold mx-1">SBC</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
