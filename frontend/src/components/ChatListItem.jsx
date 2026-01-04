import React, { useState, useEffect } from 'react';

const ChatListItem = ({ chat, isActive, onClick }) => {
  const [currentTime, setCurrentTime] = useState(Date.now());

  // Update time every minute to keep it accurate
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  const getInitials = (name) => {
    return name
      .split(' ')
      .map((word) => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    
    // Parse timestamp - handle both ISO string and Date object
    const date = new Date(timestamp);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return '';
    }
    
    const now = new Date(currentTime);
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      className={`chat-list-item ${isActive ? 'active' : ''}`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`Chat with ${chat.contact_name}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <div className={`chat-avatar ${chat.is_bot ? 'bot' : ''}`}>
        {getInitials(chat.contact_name)}
      </div>
      <div className="chat-info">
        <div className="chat-header-info">
          <span className="chat-name">{chat.contact_name}</span>
          <div className="chat-meta">
            <span className="chat-time">
              {formatTime(chat.last_message_time)}
            </span>
            {chat.unread_count > 0 && (
              <div className="chat-badge-dot"></div>
            )}
          </div>
        </div>
        <div className="chat-preview">
          {chat.last_message || 'No messages yet'}
        </div>
      </div>
    </div>
  );
};

export default ChatListItem;


