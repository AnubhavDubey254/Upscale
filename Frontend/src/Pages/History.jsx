import React, { useState, useEffect } from 'react';
import { Trash2 } from 'lucide-react'; // Import trash icon
import './History.css';

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/history', {
        credentials: 'include' 
      });

      if (response.status === 401) {
        setError("Please log in to view your history.");
        setLoading(false);
        return;
      }

      if (!response.ok) throw new Error("Failed to fetch history");

      const data = await response.json();
      setHistory(data);
    } catch (err) {
      setError("Could not load history. Is the server running?");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // NEW: Delete Handler
  const handleDelete = async (fileId) => {
    if (!window.confirm("Are you sure you want to delete this image? This cannot be undone.")) {
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/history/${fileId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        if (response.ok) {
            // Optimistically remove from UI
            setHistory(prevHistory => prevHistory.filter(item => item.id !== fileId));
        } else {
            alert("Failed to delete the file.");
        }
    } catch (err) {
        console.error("Delete failed:", err);
        alert("Error occurred while deleting.");
    }
  };

  const getDownloadLink = (uniqueId) => {
    return `http://127.0.0.1:5000/api/download/${uniqueId}`;
  };

  const getPreviewLink = (uniqueId) => {
    return `http://127.0.0.1:5000/api/view/${uniqueId}`;
  };

  return (
    <div id="History" className="history-container">
      <div className="history-box">
        <h1 className="history-title">📂 Your Enhancement History</h1>
        
        {loading && <p className="status-text">Loading your files...</p>}
        
        {error && (
          <div className="error-box">
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && history.length === 0 && (
          <p className="empty-text">You haven't uploaded any files yet.</p>
        )}

        {!loading && !error && history.length > 0 && (
          <div className="history-grid">
            {history.map((item) => (
              <div key={item.id} className="history-card">
                
                <div className="card-preview">
                  <img 
                    src={getPreviewLink(item.unique_id)} 
                    alt={item.original_filename}
                    onError={(e) => {e.target.src = 'https://placehold.co/600x400?text=No+Preview'}} 
                  />
                </div>

                <div className="card-content">
                  <div className="card-header">
                    <span className="file-name" title={item.original_filename}>
                      {item.original_filename}
                    </span>
                    <span className={`status-badge ${item.status.toLowerCase()}`}>
                      {item.status}
                    </span>
                  </div>
                  
                  <div className="card-body">
                    <p className="file-date">📅 {item.date}</p>
                  </div>
                  
                  {/* Updated Footer with Delete Button */}
                  <div className="card-footer">
                    {item.status === 'COMPLETED' ? (
                      <a 
                        href={getDownloadLink(item.unique_id)} 
                        className="download-btn"
                      >
                        ⬇️ Download Result
                      </a>
                    ) : (
                      <button disabled className="processing-btn">
                        {item.status === 'FAILED' ? '❌ Failed' : '⏳ Processing...'}
                      </button>
                    )}
                    
                    {/* Delete Button */}
                    <button 
                        className="delete-btn" 
                        onClick={() => handleDelete(item.id)}
                        title="Delete Image"
                    >
                        <Trash2 size={20} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default History;