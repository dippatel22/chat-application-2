import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { activityAPI } from '../api';
import '../styles/activity.css';

const ActivityLog = () => {
  const navigate = useNavigate();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); 

  useEffect(() => {
    loadActivities();
  }, [filter]);

  const loadActivities = async () => {
    setLoading(true);
    try {
      const data =
        filter === 'mine'
          ? await activityAPI.getMyActivities()
          : await activityAPI.getActivities();
      setActivities(data);
    } catch (error) {
      console.error('Failed to load activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="activity-container">
      <div className="activity-header">
        <button
          className="back-button"
          onClick={() => navigate('/chat')}
          aria-label="Back to chat"
        >
          ← Back
        </button>
        <h1>Activity Log</h1>
      </div>

      <div className="activity-filters">
        <button
          className={`filter-button ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Activities
        </button>
        <button
          className={`filter-button ${filter === 'mine' ? 'active' : ''}`}
          onClick={() => setFilter('mine')}
        >
          My Activities
        </button>
      </div>

      <div className="activity-list">
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner-large"></div>
          </div>
        ) : activities.length > 0 ? (
          activities.map((activity) => (
            <div key={activity.id} className="activity-item">
              <div className="activity-content">
                <div className="activity-header-item">
                  <span className="activity-user">{activity.user_email}</span>
                  <span className="activity-time">
                    {formatTime(activity.timestamp)}
                  </span>
                </div>
                <div className="activity-action">{activity.action}</div>
                {activity.details && (
                  <div className="activity-details">{activity.details}</div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <p>No activities to display</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActivityLog;







