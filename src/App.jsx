// src/App.jsx
import { useState } from 'react';
import NavBar from './components/NavBar';
import Map from './components/Map';
import './App.css';

const App = () => {
  const [searchCoords, setSearchCoords] = useState(null);

  const handleSearch = (coords) => {
    console.log('App received coords:', coords);
    setSearchCoords(coords);
  };

  return (
    <div className="app">
      <NavBar onSearch={handleSearch} />
      <Map searchCoords={searchCoords} />
    </div>
  );
};

export default App;