import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import NavBar from './components/NavBar';
import Map from './components/Map';
import AirQualityMapPage from './pages/AirQualityMapPage';
import './App.css';

const App = () => {
  const [searchCoords, setSearchCoords] = useState(null);

  const handleSearch = (coords) => {
    console.log('App received coords:', coords);
    setSearchCoords(coords);
  };

  return (
    <Router>
      <div className="app">
        <NavBar onSearch={handleSearch} />
        <Routes>
          <Route path="/" element={<Map searchCoords={searchCoords} />} />
          <Route path="/air-quality-map" element={<AirQualityMapPage />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;