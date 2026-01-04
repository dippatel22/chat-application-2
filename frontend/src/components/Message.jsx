import React from 'react';

const Message = ({ message, isOwn, onMarkAsRead }) => {
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Sent':
        return '✓';
      case 'Delivered':
        return '✓✓';
      case 'Read':
        return '✓✓';
      default:
        return '';
    }
  };

  // Mark as read when message comes into view (for received messages)
  React.useEffect(() => {
    if (!isOwn && message.status !== 'Read' && onMarkAsRead) {
      const timer = setTimeout(() => {
        onMarkAsRead(message.message_id);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isOwn, message.message_id, message.status, onMarkAsRead]);

  return (
    <div className={`message ${isOwn ? 'sent' : 'received'}`}>
      <div className="message-bubble">
        <div className="message-content">{message.content}</div>
        <div className="message-footer">
          <span className="message-time">
            {formatTime(message.timestamp)}
          </span>
          {isOwn && (
            <span
              className={`message-status ${
                message.status === 'Read' ? 'read' : 
                message.status === 'Delivered' ? 'delivered' : ''
              }`}
            >
              {getStatusIcon(message.status)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;


