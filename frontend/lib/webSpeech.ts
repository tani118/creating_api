// Voice to Text using Web Speech API

// Type definitions for Web Speech API
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

export class WebSpeechAPI {
  private recognition: any = null
  private isListening = false

  constructor() {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition()
        this.setupRecognition()
      }
    }
  }

  private setupRecognition() {
    if (!this.recognition) return

    this.recognition.continuous = false
    this.recognition.interimResults = false
    this.recognition.lang = 'en-US'
    this.recognition.maxAlternatives = 1
  }

  startListening(): Promise<string> {
    return new Promise((resolve, reject) => {
      if (!this.recognition) {
        reject(new Error('Speech recognition not supported in this browser'))
        return
      }

      let transcript = ''
      
      this.recognition.onresult = (event: any) => {
        transcript = ''
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
      }

      this.recognition.onerror = (event: any) => {
        this.isListening = false
        reject(new Error(`Speech recognition error: ${event.error}`))
      }

      this.recognition.onend = () => {
        this.isListening = false
        resolve(transcript)
      }

      try {
        this.recognition.start()
        this.isListening = true
      } catch (error) {
        this.isListening = false
        reject(error)
      }
    })
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      this.recognition.stop()
      this.isListening = false
    }
  }

  isSupported(): boolean {
    return this.recognition !== null
  }

  getIsListening(): boolean {
    return this.isListening
  }
}
