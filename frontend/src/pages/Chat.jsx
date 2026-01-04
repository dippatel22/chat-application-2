import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatListItem from '../components/ChatListItem';
import MessageList from '../components/MessageList';
import MessageInput from '../components/MessageInput';
import { messageAPI, userAPI, getCurrentUser } from '../api';
import { wsManager } from '../websocket';
import '../styles/chat.css';

const BOT_EMAIL = 'whatsease@bot.com';

const Chat = () => {
  const navigate = useNavigate();
  const [currentUser, setCurrentUser] = useState(null);
  const [chats, setChats] = useState([]);
  const [selectedChat, setSelectedChat] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [showSearch, setShowSearch] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showSidebar, setShowSidebar] = useState(true); // Mobile sidebar toggle

  useEffect(() => {
    const user = getCurrentUser();
    console.log(' Current user from localStorage:', user);
    if (!user) {
      navigate('/login');
      return;
    }
    setCurrentUser(user);
    console.log(' Set current user:', user.email);
    loadChats();

    // Ensure WebSocket is connected
    if (!wsManager.isConnected()) {
      wsManager.connect();
    }

    // Listen for new messages to update chat list
    const handleNewMessage = (message) => {
      // Update chat list locally instead of refetching
      updateChatListWithMessage(message);
    };

    wsManager.on('new_message', handleNewMessage);
    wsManager.on('message_sent', handleNewMessage);

    return () => {
      wsManager.off('new_message', handleNewMessage);
      wsManager.off('message_sent', handleNewMessage);
    };
  }, [navigate]);

  const updateChatListWithMessage = (message) => {
    setChats((prevChats) => {
      const contactEmail = message.sender === currentUser?.email 
        ? message.recipient 
        : message.sender;
      
      const updatedChats = prevChats.map((chat) => {
        if (chat.contact_email === contactEmail) {
          // Only increment unread_count if:
          // 1. Message is FROM the contact (received, not sent by current user)
          // 2. Message is not already marked as Read
          const isReceivedMessage = message.recipient === currentUser?.email;
          const isUnread = message.status !== 'Read';
          
          console.log(' Updating chat list:', {
            contactEmail,
            sender: message.sender,
            recipient: message.recipient,
            currentUser: currentUser?.email,
            isReceivedMessage,
            isUnread,
            willIncrement: isReceivedMessage && isUnread
          });
          
          return {
            ...chat,
            last_message: message.content,
            last_message_time: message.timestamp,
            unread_count: isReceivedMessage && isUnread 
              ? (chat.unread_count || 0) + 1 
              : chat.unread_count || 0,
          };
        }
        return chat;
      });

      // Sort by last message time
      return updatedChats.sort((a, b) => {
        const timeA = a.last_message_time ? new Date(a.last_message_time) : new Date(0);
        const timeB = b.last_message_time ? new Date(b.last_message_time) : new Date(0);
        return timeB - timeA;
      });
    });
  };

  const loadChats = async () => {
    setLoading(true);
    try {
      const chatList = await messageAPI.getChatList();
      
      // Ensure bot is in the list
      const hasBot = chatList.some((chat) => chat.contact_email === BOT_EMAIL);
      if (!hasBot) {
        chatList.unshift({
          contact_email: BOT_EMAIL,
          contact_name: 'WhatsEase',
          last_message: 'Start chatting with your AI assistant',
          last_message_time: new Date().toISOString(),
          unread_count: 0,
          is_bot: true,
        });
      }
      
      setChats(chatList);
    } catch (error) {
      console.error('Failed to load chats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    wsManager.disconnect();
    userAPI.logout();
    navigate('/login');
  };

  const handleChatSelect = async (chat) => {
    console.log(' Opening chat with:', chat.contact_email);
    
    setSelectedChat(chat);
    setShowSearch(false);
    setShowSidebar(false); // Hide sidebar on mobile when chat is selected
    
    // Clear unread count immediately in UI
    if (chat.unread_count > 0) {
      console.log(' Clearing', chat.unread_count, 'unread notifications for:', chat.contact_email);
      
      setChats((prevChats) =>
        prevChats.map((c) =>
          c.contact_email === chat.contact_email
            ? { ...c, unread_count: 0 }
            : c
        )
      );
    }
  };

  const handleSearchChange = async (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (query.trim().length > 2) {
      setShowSearch(true);
      try {
        const results = await userAPI.searchUsers(query);
        setSearchResults(results);
      } catch (error) {
        console.error('Search failed:', error);
      }
    } else {
      setShowSearch(false);
      setSearchResults([]);
    }
  };

  const handleUserSelect = (user) => {
    // Create or select chat with this user
    const existingChat = chats.find(
      (chat) => chat.contact_email === user.email
    );

    if (existingChat) {
      setSelectedChat(existingChat);
    } else {
      const newChat = {
        contact_email: user.email,
        contact_name: user.username,
        last_message: null,
        last_message_time: null,
        unread_count: 0,
        is_bot: user.is_bot,
      };
      setSelectedChat(newChat);
      setChats([newChat, ...chats]);
    }

    setSearchQuery('');
    setShowSearch(false);
    setSearchResults([]);
  };

  const handleActivityLog = () => {
    navigate('/activity');
  };

  const getInitials = (name) => {
    return name
      .split(' ')
      .map((word) => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  if (!currentUser) {
    return null;
  }

  return (
    <div className="chat-container">
      {/* Sidebar */}
      <div className={`chat-sidebar ${!showSidebar && selectedChat ? 'hidden' : ''}`}>
        <div className="sidebar-header">
          <h2>Chats</h2>
          <div className="sidebar-actions">
            <button
              className="icon-button"
              onClick={handleActivityLog}
              aria-label="Activity log"
              title="Activity log"
            >
              📋
            </button>
            <button
              className="icon-button"
              onClick={handleLogout}
              aria-label="Logout"
              title="Logout"
            >
              ⏻
            </button>
          </div>
        </div>

        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="Search users or chats..."
            value={searchQuery}
            onChange={handleSearchChange}
            aria-label="Search users or chats"
          />
        </div>

        <div className="chat-list">
          {loading ? (
            <div className="loading-container">
              <div className="loading-spinner-large"></div>
            </div>
          ) : showSearch ? (
            <>
              {searchResults.length > 0 ? (
                searchResults.map((user) => (
                  <div
                    key={user.email}
                    className="chat-list-item"
                    onClick={() => handleUserSelect(user)}
                    role="button"
                    tabIndex={0}
                    aria-label={`Start chat with ${user.username}`}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        handleUserSelect(user);
                      }
                    }}
                  >
                    <div className="chat-avatar">
                      {getInitials(user.username)}
                    </div>
                    <div className="chat-info">
                      <div className="chat-name">{user.username}</div>
                      <div className="chat-preview">{user.email}</div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <p>No users found</p>
                </div>
              )}
            </>
          ) : (
            <>
              {chats.length > 0 ? (
                chats.map((chat) => (
                  <ChatListItem
                    key={chat.contact_email}
                    chat={chat}
                    isActive={
                      selectedChat?.contact_email === chat.contact_email
                    }
                    onClick={() => handleChatSelect(chat)}
                  />
                ))
              ) : (
                <div className="empty-state">
                  <p>No chats yet</p>
                  <p>Search for users to start chatting</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className={`chat-area ${!selectedChat ? 'empty' : ''}`}>
        {selectedChat ? (
          <>
            <div className="chat-header-bar">
              {/* Mobile back button */}
              <button
                className="mobile-back-button"
                onClick={() => setShowSidebar(true)}
                aria-label="Back to chats"
                title="Back to chats"
              >
                ←
              </button>
              
              <div className="chat-header-info-bar">
                <div
                  className={`chat-avatar ${
                    selectedChat.is_bot ? 'bot' : ''
                  }`}
                >
                  {getInitials(selectedChat.contact_name)}
                </div>
                <div className="chat-header-text">
                  <div className="chat-header-name">
                    {selectedChat.contact_name}
                  </div>
                  <div className="chat-header-status">
                    {selectedChat.is_bot ? 'AI Assistant' : 'User'}
                  </div>
                </div>
              </div>
            </div>

            {currentUser && (
              <MessageList
                contact={selectedChat}
                currentUserEmail={currentUser.email}
              />
            )}

            <MessageInput contact={selectedChat} />
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">💬</div>
            <h3>WhatsApp-like Chat</h3>
            <p>Select a chat to start messaging</p>
            <p>Or search for users to begin a new conversation</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Chat;


