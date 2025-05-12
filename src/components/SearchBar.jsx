import React, { useState, useEffect } from 'react';
import { FaSearch } from 'react-icons/fa';
import './SearchBar.css';

function SearchBar({ onSearch }) {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [countries, setCountries] = useState([]);

    useEffect(() => {
        fetch('https://restcountries.com/v3.1/all')
            .then((response) => response.json())
            .then((data) => {
                const countryNames = data.map((country) => country.name.common);
                setCountries(countryNames);
            })
            .catch((error) => console.error('Error fetching country data:', error));
    }, []);

    const handleSearch = (e) => {
        const value = e.target.value;
        setQuery(value);

        if (value.length > 0) {
            const startsWithQuery = countries.filter((country) =>
                country.toLowerCase().startsWith(value.toLowerCase())
            );
            const includesQuery = countries.filter(
                (country) =>
                    country.toLowerCase().includes(value.toLowerCase()) &&
                    !country.toLowerCase().startsWith(value.toLowerCase())
            );
            const combinedSuggestions = [...startsWithQuery, ...includesQuery].slice(0, 4);
            setSuggestions(combinedSuggestions);
        } else {
            setSuggestions([]);
        }
    };

    const handleSuggestionClick = async (suggestion) => {
        setQuery('');
        setSuggestions([]);
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(suggestion)}&format=json&limit=1`
            );
            const data = await response.json();
            if (data.length > 0) {
                onSearch({ lat: parseFloat(data[0].lat), lon: parseFloat(data[0].lon) });
            } else {
                console.error('Location not found');
            }
        } catch (error) {
            console.error('Error fetching coordinates:', error);
        }
    };

    return (
        <div className="searchBar">
            <FaSearch id="searchIcon" />
            <input
                className="input"
                placeholder="Search..."
                value={query}
                onChange={handleSearch}
            />
            {suggestions.length > 0 && (
                <ul className="result-Box">
                    {suggestions.map((item, index) => (
                        <li key={index} onClick={() => handleSuggestionClick(item)}>
                            {item}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default SearchBar;