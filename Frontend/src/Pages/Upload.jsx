import React, { useState } from "react";
import "./Upload.css";

function Upload() {
    // State to hold the actual File object for upload
    const [fileToUpload, setFileToUpload] = useState(null); 
    // State to hold the temporary URL for the preview image
    const [previewURL, setPreviewURL] = useState(null); 
    const [isUploading, setIsUploading] = useState(false);
    const [uploadMessage, setUploadMessage] = useState("Ready for Enhancement");
    // NEW STATE: Holds the unique file ID needed for download
    const [downloadId, setDownloadId] = useState(null); 

    const handleImageChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setFileToUpload(file); // Store the actual file object
            setPreviewURL(URL.createObjectURL(file)); // Store the preview URL
            setUploadMessage(`File selected: ${file.name}`);
            setDownloadId(null); // Reset download link when a new file is chosen
        }
    };

    const handleUpload = async () => {
        if (!fileToUpload) {
            setUploadMessage("Please select an image first.");
            return;
        }

        setIsUploading(true);
        setUploadMessage("Uploading and Processing...");
        setDownloadId(null); // Clear previous download link

        // 1. Prepare FormData to send the file binary
        const formData = new FormData();
        formData.append("file", fileToUpload); 

        try {
            // 2. Make the real API POST request to your Flask endpoint
            const response = await fetch('http://127.0.0.1:5000/api/upload', {
                method: 'POST',
                credentials: 'include',
                body: formData, 
            });

            const data = await response.json();

            if (response.ok) {
                // Success: Processing status is COMPLETE (as simulated in processor.py)
                setUploadMessage(`Success! Image enhancement is ${data.status.toUpperCase()}.`);
                
                // 3. Save the unique file ID for the download link
                if (data.status === 'completed') {
                    setDownloadId(data.filename); 
                }
                setFileToUpload(null);
            } else {
                // Failure: Handle 400, 500 errors, or custom Flask error messages
                setUploadMessage(`Upload Failed: ${data.message || 'Server error occurred.'}`);
                console.error("Flask API Error:", data.message);
                setDownloadId(null);
            }
        } catch (error) {
            console.error("Network Error:", error);
            setUploadMessage("Network connection failed. Is the Flask server running?");
        } finally {
            setIsUploading(false);
        }
    };

    // Helper function to generate the download URL
    const getDownloadURL = (id) => {
        // Must match the Flask download route definition
        return `http://127.0.0.1:5000/api/download/${id}`;
    };

    // Sample image URLs for floating background (kept for styling)
    const floatingImages = [
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='80' viewBox='0 0 120 80'%3E%3Crect width='120' height='80' fill='%23e0f2fe'/%3E%3Crect x='10' y='20' width='100' height='40' fill='%23b3e5fc' rx='5'/%3E%3Ccircle cx='25' cy='30' r='8' fill='%23ffeb3b'/%3E%3Cpath d='M40 50L60 35L80 45L100 40L100 60L40 60Z' fill='%234caf50'/%3E%3C/svg%3E",
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='80' viewBox='0 0 120 80'%3E%3Crect width='120' height='80' fill='%23fce4ec'/%3E%3Crect x='10' y='20' width='100' height='40' fill='%23f8bbd9' rx='5'/%3E%3Ccircle cx='30' cy='35' r='6' fill='%23ff9800'/%3E%3Cpath d='M45 50L65 30L85 40L95 35L95 60L45 60Z' fill='%239c27b0'/%3E%3C/svg%3E",
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='80' viewBox='0 0 120 80'%3E%3Crect width='120' height='80' fill='%23e8f5e8'/%3E%3Crect x='15' y='15' width='90' height='50' fill='%23a5d6a7' rx='5'/%3E%3Ccircle cx='35' cy='30' r='7' fill='%23ffeb3b'/%3E%3Cpath d='M50 50L70 35L85 45L95 40L95 60L50 60Z' fill='%232196f3'/%3E%3C/svg%3E",
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='80' viewBox='0 0 120 80'%3E%3Crect width='120' height='80' fill='%23fff3e0'/%3E%3Crect x='10' y='15' width='100' height='50' fill='%23ffcc02' rx='5'/%3E%3Ccircle cx='25' cy='28' r='8' fill='%23f44336'/%3E%3Cpath d='M40 55L60 40L80 50L100 45L100 65L40 65Z' fill='%23ff5722'/%3E%3C/svg%3E"
    ];


    return (
        <div id="Upload" className="upload-container">
            {/* Animated Background with Floating Images (Keep this original styling) */}
            <div className="floating-bg">
                {Array.from({ length: 20 }, (_, i) => (
                    <div
                        key={i}
                        className="floating-image"
                        style={{
                            left: `${Math.random() * 100}%`,
                            animationDelay: `${Math.random() * 10}s`,
                            animationDuration: `${15 + Math.random() * 10}s`
                        }}
                    >
                        <img 
                            src={floatingImages[i % floatingImages.length]} 
                            alt=""
                            style={{
                                width: `${60 + Math.random() * 40}px`,
                                opacity: 0.1 + Math.random() * 0.2
                            }}
                        />
                    </div>
                ))}
            </div>
            
            <div className="gradient-overlay"></div>

            {/* Main Upload Box */}
            <div className="upload-box">
                <div className="upload-header">
                    <h1 className="main-title">✨ AI Image Enhancer</h1>
                    <p className="subtitle">Transform your images with cutting-edge AI technology</p>
                </div>

                <div className="upload-section">
                    <label htmlFor="file-upload" className="upload-label">
                        <input
                            id="file-upload"
                            type="file"
                            accept="image/png, image/jpeg"
                            onChange={handleImageChange}
                            style={{ display: 'none' }}
                        />
                        <div className="upload-icon">📸</div>
                        <span className="upload-text">{fileToUpload ? "Image Selected" : "Choose Your Image"}</span>
                        <div className="upload-hint">PNG, JPG up to 16MB</div>
                    </label>

                    {/* Image Preview */}
                    {previewURL && (
                        <div className="preview-container">
                            <div className="preview-box">
                                <img src={previewURL} alt="Preview" className="preview-img" />
                                <div className="preview-overlay">
                                    <span>{uploadMessage}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Upload Button */}
                    <button 
                        className={`upload-btn ${isUploading ? 'uploading' : ''}`}
                        onClick={handleUpload}
                        disabled={isUploading || !fileToUpload} 
                    >
                        {isUploading ? (
                            <>
                                <div className="spinner"></div>
                                Processing...
                            </>
                        ) : (
                            <>
                                🚀 Enhance Image
                            </>
                        )}
                    </button>
                    
                    {/* 🟢 Status and Download Section 🟢 */}
                    <p style={{marginTop: '15px', fontWeight: 'bold'}}>{uploadMessage}</p>
                    
                    {downloadId && (
                        <div style={{ marginTop: '20px' }}>
                            <a 
                                href={getDownloadURL(downloadId)} 
                                className="download-link"
                                style={{ 
                                    textDecoration: 'none', 
                                    padding: '10px 20px', 
                                    backgroundColor: '#4CAF50', 
                                    color: 'white', 
                                    borderRadius: '8px', 
                                    display: 'inline-block',
                                    fontWeight: 'bold'
                                }}
                            >
                                ✨ Download Enhanced Image
                            </a>
                        </div>
                    )}
                    {/* --------------------------------- */}
                </div>
                
                {/* Features */}
                <div className="features">
                    <div className="feature">
                        <span className="feature-icon">⚡</span>
                        <span>Lightning Fast</span>
                    </div>
                    <div className="feature">
                        <span className="feature-icon">🎯</span>
                        <span>AI Powered</span>
                    </div>
                    <div className="feature">
                        <span className="feature-icon">🔒</span>
                        <span>Secure Upload</span>
                    </div>
                </div>
            </div>
            
        </div>
    );
}

export default Upload;