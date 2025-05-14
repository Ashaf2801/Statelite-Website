import React from 'react';
import './Map.css'; // Import the CSS for styling the popup

const HeatmapPopup = ({ heatmapImage, onClose }) => {
    if (!heatmapImage) return null;

    return (
        <div className="heatmap-popup">
            <img src={heatmapImage} alt="Air Quality Heatmap" className="heatmap-image" />
        </div>
    );
};

export default HeatmapPopup;