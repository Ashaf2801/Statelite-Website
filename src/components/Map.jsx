import { useState } from 'react';
import { MapContainer, TileLayer, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './Map.css';

const Map = () => {
    const [popupPosition, setPopupPosition] = useState(null);

    // Static data to display in the popup
    const staticData = {
        temperature: 34.2,
        co2: 863.9,
        voc: 407.7,
        pm1_0: 20.1,
        pm2_5: 38.4,
        pm10: 48.9
    };

    // Component to handle map events
    const MapEvents = () => {
        useMapEvents({
            click(e) {
                const { lat, lng } = e.latlng;
                console.log('Map clicked at:', [lat, lng]);
                setPopupPosition([lat, lng]);
            },
        });
        return null;
    };

    return (
        <MapContainer
            className="map-container"
            center={[0, 0]}
            zoom={2}
            style={{ height: '100vh', width: '100%' }}
        >
            <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            <MapEvents />
            {popupPosition && (
                <Popup position={popupPosition} closeButton={false}>
                    <div className="popup-content">
                        <h3>Environmental Data</h3>
                        <p>Temperature: {staticData.temperature}°C</p>
                        <p>CO2: {staticData.co2} ppm</p>
                        <p>VOC: {staticData.voc} index</p>
                        <p>PM 1.0: {staticData.pm1_0} μg/m³</p>
                        <p>PM 2.5: {staticData.pm2_5} μg/m³</p>
                        <p>PM 10: {staticData.pm2_5} μg/m³</p>
                        <button
                            onClick={() => {
                                console.log('Closing popup');
                                setPopupPosition(null);
                            }}
                            className="popup-close"
                        >
                            Close
                        </button>
                    </div>
                </Popup>
            )}
        </MapContainer>
    );
};

export default Map;