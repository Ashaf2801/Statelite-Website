import React, { useState, useEffect } from 'react';
import { FaSearch } from "react-icons/fa";
import "./SearchBar.css";

function SearchBar() {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [countries, setCountries] = useState([]);

    useEffect(() => {
        fetch("https://restcountries.com/v3.1/all")
            .then(response => response.json())
            .then(data => {
                const countryNames = data.map(country => country.name.common);
                setCountries(countryNames);
            })
            .catch(error => console.error("Error fetching country data:", error));
    }, []);

    const handleSearch = (e) => {
        const value = e.target.value;
        setQuery(value);

        if (value.length > 0) {
            // First preference: countries that start with the query
            const startsWithQuery = countries.filter(country =>
                country.toLowerCase().startsWith(value.toLowerCase())
            );

            // Second preference: countries that include the query (but don't start with it)
            const includesQuery = countries.filter(country =>
                country.toLowerCase().includes(value.toLowerCase()) &&
                !country.toLowerCase().startsWith(value.toLowerCase())
            );

            // Concatenate both arrays and take the first 5 results
            const combinedSuggestions = [...startsWithQuery, ...includesQuery].slice(0, 4);
            setSuggestions(combinedSuggestions);
        } else {
            setSuggestions([]);
        }
    };

    const handleSuggestionClick = (suggestion) => {
        setQuery(suggestion);
        setSuggestions([]);
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

            {/* Suggestion List */}
            {suggestions.length > 0 && (
                <ul className="result-Box">
                    {suggestions.map((item, index) => (
                        <li key={index} onClick={() => handleSuggestionClick(item)}>{item}</li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default SearchBar;
