/**
 * WebSocket manager for real-time messaging using Socket.IO
 */
import { io } from 'socket.io-client';
import { getToken } from './api';

const WS_URL = import.meta.env.PROD
  ? 'wss://chat-application-2-o160.onrender.com'
  : 'http://localhost:8000';

class WebSocketManager {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.listeners = {};
  }

  /**
   * Connect to WebSocket server
   */
  connect(token = null) {
    if (this.connected) {
      console.log('Already connected to WebSocket');
      return;
    }

    const authToken = token || getToken();
    if (!authToken) {
      console.error('No authentication token available');
      return;
    }

    this.socket = io(WS_URL, {
      auth: {
        token: authToken,
      },
      transports: ['websocket', 'polling'],
    });

    this.socket.on('connect', () => {
      console.log(' Connected to WebSocket');
      console.log('   Socket ID:', this.socket.id);
      this.connected = true;
      this.emit('ws_connected');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket');
      this.connected = false;
      this.emit('ws_disconnected');
    });

    this.socket.on('connected', (data) => {
      console.log('Server confirmed connection:', data);
    });

    this.socket.on('new_message', (message) => {
      console.log('📨 NEW MESSAGE EVENT:', {
        from: message.sender,
        to: message.recipient,
        content: message.content.substring(0, 50),
        message_id: message.message_id
      });
      this.emit('new_message', message);
    });

    this.socket.on('message_sent', (message) => {
      console.log('Message sent confirmation:', message);
      this.emit('message_sent', message);
    });

    this.socket.on('message_read', (data) => {
      console.log('Message read:', data);
      this.emit('message_read', data);
    });

    this.socket.on('message_delivered', (data) => {
      console.log('Message delivered:', data);
      this.emit('message_delivered', data);
    });

    this.socket.on('user_typing', (data) => {
      console.log('User typing:', data);
      this.emit('user_typing', data);
    });

    this.socket.on('online_status', (data) => {
      console.log('Online status:', data);
      this.emit('online_status', data);
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      this.emit('connect_error', error);
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  /**
   * Send message via WebSocket
   */
  sendMessage(recipient, content) {
    if (!this.connected || !this.socket) {
      console.error(' Not connected to WebSocket');
      return false;
    }

    console.log(' Sending message via WebSocket:', {
      to: recipient,
      content: content.substring(0, 50)
    });
    
    this.socket.emit('send_message', {
      recipient,
      content,
    });
    return true;
  }

  /**
   * Mark message as read
   */
  markAsRead(messageId) {
    if (!this.connected || !this.socket) {
      return false;
    }

    this.socket.emit('mark_as_read', {
      message_id: messageId,
    });
    return true;
  }

  /**
   * Send typing indicator
   */
  sendTyping(recipient, isTyping = true) {
    if (!this.connected || !this.socket) {
      return false;
    }

    this.socket.emit('typing', {
      recipient,
      is_typing: isTyping,
    });
    return true;
  }

  /**
   * Get online status of a user
   */
  getOnlineStatus(email) {
    if (!this.connected || !this.socket) {
      return false;
    }

    this.socket.emit('get_online_status', {
      email,
    });
    return true;
  }

  /**
   * Register event listener
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * Unregister event listener
   */
  off(event, callback) {
    if (!this.listeners[event]) {
      return;
    }

    this.listeners[event] = this.listeners[event].filter(
      (cb) => cb !== callback
    );
  }

  /**
   * Emit event to registered listeners
   */
  emit(event, data) {
    if (!this.listeners[event]) {
      return;
    }

    this.listeners[event].forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in listener for ${event}:`, error);
      }
    });
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.connected;
  }
}

// Export singleton instance
export const wsManager = new WebSocketManager();
export default wsManager;


