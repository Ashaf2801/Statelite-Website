import React, { useState, useEffect } from 'react';
import axios from 'axios';
import HeatmapPopup from 'C:/Users/Ashaf/Desktop/Project/Ideathon/Statelite-Website/src/components/HeatmapPopup.jsx';
import 'C:/Users/Ashaf/Desktop/Project/Ideathon/Statelite-Website/src/components/Map.css'; // Import the CSS for styling

const AirQualityMapPage = () => {
    const [heatmapImage, setHeatmapImage] = useState(null);
    const [error, setError] = useState(null);
    const [showPopup, setShowPopup] = useState(false);

    // Get coordinates from localStorage (set by Map.jsx)
    const clickedCoords = JSON.parse(localStorage.getItem('clickedCoords')) || {
        latitude: 11.0168,  // Default to Coimbatore if not set
        longitude: 76.9558
    };
    const { latitude, longitude } = clickedCoords;

    useEffect(() => {
        const fetchHeatmapData = async () => {
            try {
                // Get current date and time dynamically
                const now = new Date();
                const date = now.toISOString().split('T')[0].replace(/-/g, ''); // Format: YYYYMMDD (e.g., 20250514)
                const time = now.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                }); // Format: HH:MM (e.g., 15:38)

                const response = await axios.post('http://localhost:5000/heatmap-data', {
                    latitude,
                    longitude,
                    radius: 0.1
                });

                const heatmapImage = response.data.heatmap_image;
                setHeatmapImage(heatmapImage);
                setError(null);
            } catch (err) {
                console.error('Error fetching heatmap data:', err);
                const errorMessage = err.response?.data?.error || 'Failed to fetch heatmap data. Please ensure the server is running.';
                setError(errorMessage);
                setHeatmapImage(null);
            }
        };

        fetchHeatmapData();
    }, [latitude, longitude]); // Re-fetch if coordinates change

    const togglePopup = () => {
        setShowPopup(!showPopup);
    };

    return (
        <div className="air-quality-map-page">
            <h2>Air Quality Map</h2>
            <p>
                Showing air quality for Latitude: {latitude.toFixed(4)}, Longitude: {longitude.toFixed(4)}
            </p>
            {error ? (
                <p className="error-message">Error: {error}</p>
            ) : heatmapImage ? (
                <>
                    <div className="heatmap-container">
                        <img src={heatmapImage} alt="Air Quality Heatmap" className="heatmap-image" />
                    </div>
                    <HeatmapPopup
                        heatmapImage={showPopup ? heatmapImage : null}
                        onClose={() => setShowPopup(false)}
                    />
                </>
            ) : (
                <p>Loading air quality map...</p>
            )}
        </div>
    );
};

export default AirQualityMapPage;