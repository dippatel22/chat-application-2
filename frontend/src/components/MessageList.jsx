import React, { useState, useEffect, useRef, useCallback } from 'react';
import Message from './Message';
import { messageAPI } from '../api';
import { wsManager } from '../websocket';

const MessageList = ({ contact, currentUserEmail }) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [typingUsers, setTypingUsers] = useState(new Set());
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const currentContactRef = useRef(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const loadMessages = async (contactEmail) => {
    if (!contactEmail) return;

    console.log('Loading messages for:', contactEmail);
    setLoading(true);
    
    try {
      const data = await messageAPI.getMessages(contactEmail, 200, 0);
      console.log('Loaded', data.length, 'messages:', data);
      
      // Only update if we're still on the same contact
      if (currentContactRef.current === contactEmail) {
        setMessages(data);
        console.log('Set messages state with', data.length, 'messages');
        scrollToBottom();
      } else {
        console.log('Contact changed during load, discarding');
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('Contact changed:', contact?.contact_email);
    
    if (contact?.contact_email) {
      currentContactRef.current = contact.contact_email;
      setMessages([]);
      setLoading(true);
      loadMessages(contact.contact_email);
    } else {
      currentContactRef.current = null;
      setMessages([]);
    }
  }, [contact?.contact_email]);

  useEffect(() => {
    if (!contact?.contact_email) return;

    console.log('Setting up WebSocket handlers for:', contact.contact_email);

    // WebSocket event handlers
    const handleNewMessage = (message) => {
      console.log('Received new_message event:', message);
      
      // Only add message if it's for the currently active contact
      if (
        (message.sender === contact?.contact_email &&
          message.recipient === currentUserEmail) ||
        (message.sender === currentUserEmail &&
          message.recipient === contact?.contact_email)
      ) {
        setMessages((prev) => {
          const exists = prev.some((m) => m.message_id === message.message_id);
          if (!exists) {
            console.log('Adding new message to state. Previous count:', prev.length);
            return [...prev, message];
          }
          console.log('Message already exists, skipping');
          return prev;
        });
        scrollToBottom();
      } else {
        console.log('Message not for current contact, skipping');
      }
    };

    const handleMessageSent = (message) => {
      console.log('Received message_sent event:', message);
      
      // Only add if it's for the current contact
      if (
        (message.sender === contact?.contact_email &&
          message.recipient === currentUserEmail) ||
        (message.sender === currentUserEmail &&
          message.recipient === contact?.contact_email)
      ) {
        setMessages((prev) => {
          const exists = prev.some((m) => m.message_id === message.message_id);
          if (!exists) {
            console.log('Adding sent message to state. Previous count:', prev.length);
            return [...prev, message];
          }
          console.log('Message already exists, skipping');
          return prev;
        });
        scrollToBottom();
      }
    };

    const handleMessageRead = (data) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.message_id === data.message_id
            ? { ...msg, status: 'Read' }
            : msg
        )
      );
    };

    const handleMessageDelivered = (data) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.message_id === data.message_id
            ? { ...msg, status: 'Delivered' }
            : msg
        )
      );
    };

    const handleUserTyping = (data) => {
      if (data.sender === contact?.contact_email) {
        setTypingUsers((prev) => {
          const newSet = new Set(prev);
          if (data.is_typing) {
            newSet.add(data.sender);
          } else {
            newSet.delete(data.sender);
          }
          return newSet;
        });

        if (data.is_typing) {
          setTimeout(() => {
            setTypingUsers((prev) => {
              const newSet = new Set(prev);
              newSet.delete(data.sender);
              return newSet;
            });
          }, 3000);
        }
      }
    };

    wsManager.on('new_message', handleNewMessage);
    wsManager.on('message_sent', handleMessageSent);
    wsManager.on('message_read', handleMessageRead);
    wsManager.on('message_delivered', handleMessageDelivered);
    wsManager.on('user_typing', handleUserTyping);

    return () => {
      console.log('Cleaning up WebSocket handlers');
      wsManager.off('new_message', handleNewMessage);
      wsManager.off('message_sent', handleMessageSent);
      wsManager.off('message_read', handleMessageRead);
      wsManager.off('message_delivered', handleMessageDelivered);
      wsManager.off('user_typing', handleUserTyping);
    };
  }, [contact?.contact_email, currentUserEmail]);

  const handleMarkAsRead = (messageId) => {
    wsManager.markAsRead(messageId);
  };

  const groupMessagesByDate = (messages) => {
    const groups = {};
    
    console.log('Grouping', messages.length, 'messages');
    
    // Check for duplicate IDs and log them
    const idCounts = {};
    messages.forEach((msg) => {
      idCounts[msg.message_id] = (idCounts[msg.message_id] || 0) + 1;
    });
    
    const duplicates = Object.entries(idCounts).filter(([id, count]) => count > 1);
    if (duplicates.length > 0) {
      console.error('DUPLICATE MESSAGE IDS FOUND:', duplicates);
    }
    
    messages.forEach((msg) => {
      const date = new Date(msg.timestamp);
      const dateKey = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
      
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(msg);
    });
    
    return groups;
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner-large"></div>
      </div>
    );
  }

  const messageGroups = groupMessagesByDate(messages);
  console.log('Rendering with', messages.length, 'messages in state');

  return (
    <div className="messages-container" ref={messagesContainerRef}>
      {Object.keys(messageGroups).length === 0 ? (
        <div className="empty-state">
          <p>No messages yet. Start the conversation!</p>
        </div>
      ) : (
        <>
          {Object.entries(messageGroups).map(([date, msgs]) => (
            <React.Fragment key={date}>
              <div className="message-date-separator">
                <span>{date}</span>
              </div>
              {msgs.map((msg, index) => {
                const isOwn = msg.sender === currentUserEmail;
                console.log('Rendering message:', {
                  message_id: msg.message_id,
                  sender: msg.sender,
                  currentUserEmail: currentUserEmail,
                  isOwn: isOwn,
                  content: msg.content.substring(0, 30)
                });
                return (
                  <Message
                    key={msg.message_id}
                    message={msg}
                    isOwn={isOwn}
                    onMarkAsRead={handleMarkAsRead}
                  />
                );
              })}
            </React.Fragment>
          ))}
        </>
      )}
      
      {typingUsers.size > 0 && (
        <div className="typing-indicator">
          {contact.contact_name} is typing...
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
