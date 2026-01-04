
//API configuration and HTTP client
 

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';


// Get authentication token from localStorage
 
export const getToken = () => {
  return localStorage.getItem('token');
};


// Set authentication token in localStorage
 
export const setToken = (token) => {
  localStorage.setItem('token', token);
};


// Remove authentication token from localStorage
 
export const removeToken = () => {
  localStorage.removeItem('token');
};


// Get current user from localStorage

export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};


// Set current user in localStorage

export const setCurrentUser = (user) => {
  localStorage.setItem('user', JSON.stringify(user));
};


// Remove current user from localStorage
 
export const removeCurrentUser = () => {
  localStorage.removeItem('user');
};


// Make authenticated API request

const apiRequest = async (endpoint, options = {}) => {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    // Token expired or invalid
    removeToken();
    removeCurrentUser();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'API request failed');
  }

  return data;
};


// User API

export const userAPI = {
  register: async (userData) => {
    const data = await apiRequest('/api/users/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
    setToken(data.access_token);
    setCurrentUser(data.user);
    return data;
  },

  login: async (credentials) => {
    const data = await apiRequest('/api/users/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    setToken(data.access_token);
    setCurrentUser(data.user);
    return data;
  },

  logout: () => {
    removeToken();
    removeCurrentUser();
  },

  getCurrentUser: async () => {
    return await apiRequest('/api/users/me');
  },

  searchUsers: async (query) => {
    return await apiRequest(`/api/users/search?query=${encodeURIComponent(query)}`);
  },

  getContacts: async () => {
    return await apiRequest('/api/users/contacts');
  },
};

/**
 * Message API
 */
export const messageAPI = {
  getMessages: async (contactEmail, limit = 50, skip = 0) => {
    return await apiRequest(
      `/api/messages/?contact_email=${encodeURIComponent(contactEmail)}&limit=${limit}&skip=${skip}`
    );
  },

  sendMessage: async (messageData) => {
    return await apiRequest('/api/messages/', {
      method: 'POST',
      body: JSON.stringify(messageData),
    });
  },

  updateMessage: async (messageId, updateData) => {
    return await apiRequest(`/api/messages/${messageId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData),
    });
  },

  getChatList: async () => {
    return await apiRequest('/api/messages/chats');
  },

  searchMessages: async (query, contactEmail = null) => {
    let url = `/api/messages/search?query=${encodeURIComponent(query)}`;
    if (contactEmail) {
      url += `&contact_email=${encodeURIComponent(contactEmail)}`;
    }
    return await apiRequest(url);
  },
};

/**
 * Activity API
 */
export const activityAPI = {
  getActivities: async (limit = 50) => {
    return await apiRequest(`/api/activities?limit=${limit}`);
  },

  getMyActivities: async (limit = 20) => {
    return await apiRequest(`/api/activities/me?limit=${limit}`);
  },

  getBotHistory: async (count = 10) => {
    return await apiRequest(`/api/bot/history?count=${count}`);
  },

  clearBotHistory: async () => {
    return await apiRequest('/api/bot/history', {
      method: 'DELETE',
    });
  },
};







