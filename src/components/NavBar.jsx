import React from 'react';
import SearchBar from './SearchBar';
import './NavBar.css';
import logo from '../assets/20250401_111002.jpg';

const NavBar = ({ onSearch }) => {
  return (
    <nav className="navbar">
      <div className="logo">
        <a href="/">
          <img src={logo} alt="Logo" />
        </a>
      </div>
      <ul className="navLinks">
        <li><a href="/">Home</a></li>
        <li><a href="/about">About</a></li>
        <li><a href="/contact">Contact</a></li>
      </ul>
      <div>
        <SearchBar onSearch={onSearch} />
      </div>
      <div className="authButtons">
        <button className="login">Login</button>
        <button className="signup">Sign Up</button>
      </div>
    </nav>
  );
};

export default NavBar;