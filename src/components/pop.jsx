// src/components/pop.jsx
import { Popup } from 'react-leaflet';
import './pop.css';

const pop = ({ position, data, onClose }) => {
    console.log('pop component rendered with position:', position, 'and data:', data);
    if (!data) {
        console.log('No data available for popup');
        return (
            <Popup position={position} closeButton={false}>
                <div className="popup-content">
                    <h3>No Data Available</h3>
                    <button onClick={onClose} className="popup-close">
                        Close
                    </button>
                </div>
            </Popup>
        );
    }

    return (
        <Popup position={position} closeButton={false}>
            <div className="popup-content">
                <h3>Data at ({position[0].toFixed(2)}, {position[1].toFixed(2)})</h3>
                {typeof data.PM1_0 === 'number' && (
                    <p>PM1.0: {data.PM1_0.toFixed(2)} μg/m³</p>
                )}
                {typeof data.PM2_5 === 'number' ? (
                    <p>PM2.5: {data.PM2_5.toFixed(2)} μg/m³</p>
                ) : typeof data.bccmass === 'number' ? (
                    <p>BCCMASS: {data.bccmass.toFixed(2)} μg/m³</p>
                ) : null}
                {typeof data.CO2 === 'number' && (
                    <p>CO2: {data.CO2.toFixed(2)}</p>
                )}
                {typeof data.VOC === 'number' && (
                    <p>VOC: {data.VOC.toFixed(2)}</p>
                )}
                {data.time && <p>Time: {data.time}</p>}
                <button onClick={onClose} className="popup-close">
                    Close
                </button>
            </div>
        </Popup>
    );
};

export default pop;