import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';
import HeatmapPopup from './HeatmapPopup';
import './Map.css';

// Fix Leaflet default icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Debounce utility
const debounce = (func, wait) => {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
    };
};

function MapClickHandler({ onPointClick, onHeatmapFetch, searchCoords }) {
    const map = useMap();

    useEffect(() => {
        // Center the map on search coordinates if provided
        if (searchCoords) {
            map.setView([searchCoords.latitude, searchCoords.longitude], 12);
        }

        const debouncedHandleMapClick = debounce(async (e) => {
            const { lat, lng } = e.latlng;
            try {
                // Get current date and time dynamically
                const now = new Date();
                const date = now.toISOString().split('T')[0].replace(/-/g, ''); // Format: YYYYMMDD (e.g., 20250514)
                const time = now.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    hour12: false
                }); // Format: HH:MM (e.g., 15:38)

                // Fetch prediction data
                const predictResponse = await axios.post('http://localhost:5000/predict', {
                    date,
                    latitude: lat,
                    longitude: lng,
                    time
                });

                const prediction = predictResponse.data;
                onPointClick({
                    latitude: lat,
                    longitude: lng,
                    prediction
                });

                // Fetch heatmap data (but don't display it here)
                const heatmapResponse = await axios.post('http://localhost:5000/heatmap-data', {
                    latitude: lat,
                    longitude: lng,
                    radius: 0.1
                });

                const heatmapImage = heatmapResponse.data.heatmap_image;
                onHeatmapFetch({ lat, lng, heatmapImage });
            } catch (error) {
                console.error('Error fetching data:', error);
                const errorMessage = error.response?.data?.error || 'Failed to fetch data. Please ensure the server is running.';
                onPointClick({
                    latitude: lat,
                    longitude: lng,
                    prediction: { error: errorMessage }
                });
                onHeatmapFetch(null);
            }
        }, 1000); // 1-second debounce

        // Add the click event listener
        map.on('click', debouncedHandleMapClick);

        // Cleanup: Remove the event listener when the component unmounts
        return () => {
            map.off('click', debouncedHandleMapClick);
        };
    }, [map, onPointClick, onHeatmapFetch, searchCoords]);

    return null;
}

function Sidebar({ selectedPoint, onClose, onViewHeatmap }) {
    if (!selectedPoint) return null;

    const { prediction } = selectedPoint;

    return (
        <div className="data-sidebar">
            <button className="data-sidebar-close" onClick={onClose}>×</button>
            <h2>Environmental Data</h2>
            <p><strong>Latitude:</strong> {selectedPoint.latitude.toFixed(4)}</p>
            <p><strong>Longitude:</strong> {selectedPoint.longitude.toFixed(4)}</p>
            {prediction.error ? (
                <p><strong>Error:</strong> {prediction.error}</p>
            ) : (
                <>
                    <p><strong>Temperature:</strong> {prediction.temperature}</p>
                    <p><strong>CO2:</strong> {prediction.CO2}</p>
                    <p><strong>VOC:</strong> {prediction.VOC}</p>
                    <p><strong>PM1.0:</strong> {prediction['PM1.0']}</p>
                    <p><strong>PM2.5:</strong> {prediction['PM2.5']}</p>
                    <p><strong>PM10:</strong> {prediction.PM10}</p>
                    <button onClick={onViewHeatmap} className="view-heatmap-button">
                        View Air Quality Map
                    </button>
                </>
            )}
        </div>
    );
}

function Map({ searchCoords }) {
    const [selectedPoint, setSelectedPoint] = useState(null);
    const [heatmapData, setHeatmapData] = useState(null);

    const handlePointClick = (point) => {
        setSelectedPoint(point);
    };

    const handleHeatmapFetch = (data) => {
        setHeatmapData(data);
    };

    const handleCloseSidebar = () => {
        setSelectedPoint(null);
        setHeatmapData(null);
    };

    const handleViewHeatmap = () => {
        if (heatmapData) {
            // Store the coordinates in localStorage (we'll fetch the heatmap image in AirQualityMapPage)
            localStorage.setItem('clickedCoords', JSON.stringify({
                latitude: heatmapData.lat,
                longitude: heatmapData.lng
            }));
            window.location.href = '/air-quality-map'; // Navigate to the new page
        }
    };

    return (
        <div className="map-container">
            <MapContainer center={[11.0168, 76.9558]} zoom={12} className="leaflet-map" minZoom={1}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <MapClickHandler
                    onPointClick={handlePointClick}
                    onHeatmapFetch={handleHeatmapFetch}
                    searchCoords={searchCoords}
                />
            </MapContainer>
            <Sidebar
                selectedPoint={selectedPoint}
                onClose={handleCloseSidebar}
                onViewHeatmap={handleViewHeatmap}
            />
        </div>
    );
}

export default Map;