import React, { useState, useRef, useEffect } from 'react';
import { wsManager } from '../websocket';

const MessageInput = ({ contact }) => {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const textareaRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  useEffect(() => {
    // Reset on contact change
    setMessage('');
    adjustTextareaHeight();
  }, [contact]);

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  };

  const handleChange = (e) => {
    setMessage(e.target.value);
    adjustTextareaHeight();

    // Send typing indicator
    if (contact && wsManager.isConnected()) {
      wsManager.sendTyping(contact.contact_email, true);

      // Clear previous timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }

      // Set timeout to stop typing indicator
      typingTimeoutRef.current = setTimeout(() => {
        wsManager.sendTyping(contact.contact_email, false);
      }, 2000);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const trimmedMessage = message.trim();
    if (!trimmedMessage || !contact) return;

    setSending(true);

    try {
      // Send via WebSocket
      const success = wsManager.sendMessage(
        contact.contact_email,
        trimmedMessage
      );

      if (success) {
        setMessage('');
        adjustTextareaHeight();
        
        // Stop typing indicator
        if (typingTimeoutRef.current) {
          clearTimeout(typingTimeoutRef.current);
        }
        wsManager.sendTyping(contact.contact_email, false);
      } else {
        console.error('Failed to send message via WebSocket');
      }
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="input-container" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          ref={textareaRef}
          className="message-input"
          placeholder="Type a message..."
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={!contact || sending}
          aria-label="Message input"
          rows={1}
        />
      </div>
      <button
        type="submit"
        className="send-button"
        disabled={!message.trim() || !contact || sending}
        aria-label="Send message"
      >
        {sending ? '⏳' : '➤'}
      </button>
    </form>
  );
};

export default MessageInput;





