import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import './App.css';

// Pages
import HomePage from './pages/HomePage';
import CurrentAQI from './pages/CurrentAQI';
import Prediction from './pages/Prediction';
import SignIn from './pages/SignIn';
import SignUp from './pages/SignUp';
import { auth } from './firebaseConfig';
import { onAuthStateChanged, signOut } from 'firebase/auth';

// Create Location Context
export const LocationContext = createContext();
export const useLocationData = () => useContext(LocationContext);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
    const [userLocation, setUserLocation] = useState(null);
    const [locationName, setLocationName] = useState('Detecting location...');
    const [locationError, setLocationError] = useState(null);
    const [isLoadingLocation, setIsLoadingLocation] = useState(true);
    const [user, setUser] = useState(null);
    const routeLocation = useLocation();

    // Track user auth state
    useEffect(() => {
        if (!auth) return undefined;
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
        });
        return () => unsubscribe();
    }, []);

    const requestLocation = useCallback(() => {
        setIsLoadingLocation(true);
        setLocationError(null);

        if (!navigator.geolocation) {
            setLocationError('Geolocation is not supported by your browser');
            setIsLoadingLocation(false);
            setUserLocation({ lat: 17.6868, lon: 83.2185 });
            setLocationName('Visakhapatnam (Default)');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                setUserLocation({ lat: latitude, lon: longitude });

                try {
                    const response = await fetch(
                        `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`
                    );
                    if (!response.ok) throw new Error('Reverse geocoding failed');
                    const data = await response.json();
                    const city = data.city || data.locality || data.principalSubdivision || 'Your Location';
                    setLocationName(city);
                } catch (err) {
                    setLocationName('Your Location');
                }

                setIsLoadingLocation(false);
            },
            (error) => {
                console.error('Location error:', error);
                setLocationError('Location access denied. Using default location.');
                setUserLocation({ lat: 17.6868, lon: 83.2185 });
                setLocationName('Visakhapatnam (Default)');
                setIsLoadingLocation(false);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            }
        );
    }, []);

    useEffect(() => {
        requestLocation();
    }, [requestLocation]);

    const contextValue = {
        userLocation,
        locationName,
        locationError,
        isLoadingLocation,
        requestLocation,
        API_URL
    };

    return (
        <LocationContext.Provider value={contextValue}>
            <div className="app">
                {/* Navigation */}
                <nav className="navbar">
                    <div className="nav-container">
                        <Link to="/" className="nav-brand">
                            <span className="brand-icon">🌍</span>
                            <span className="brand-text">AQI Forecast</span>
                        </Link>

                        <div className="nav-links">
                            <Link
                                to="/"
                                className={`nav-link ${routeLocation.pathname === '/' ? 'active' : ''}`}
                            >
                                Home
                            </Link>
                            <Link
                                to="/current"
                                className={`nav-link ${routeLocation.pathname === '/current' ? 'active' : ''}`}
                            >
                                Current AQI
                            </Link>
                            <Link
                                to="/prediction"
                                className={`nav-link ${routeLocation.pathname === '/prediction' ? 'active' : ''}`}
                            >
                                Prediction
                            </Link>
                        </div>

                        <div className="nav-auth">
                            {user ? (
                                <div className="user-profile">
                                    <span className="user-email">{user.email?.split('@')[0] || 'User'}</span>
                                    <button onClick={() => { if (auth) signOut(auth); }} className="logout-btn">Logout</button>
                                </div>
                            ) : (
                                <div className="auth-links">
                                    <Link to="/signin" className="nav-link">Sign In</Link>
                                    <Link to="/signup" className="nav-btn">Sign Up</Link>
                                </div>
                            )}
                        </div>

                        <div className="nav-location" onClick={requestLocation}>
                            <span className="location-icon">📍</span>
                            <span className="location-text">
                                {isLoadingLocation ? 'Detecting...' : locationName}
                            </span>
                        </div>
                    </div>
                </nav>

                {/* Location Error Banner */}
                {locationError && (
                    <div className="location-error">
                        ⚠️ {locationError}
                        <button onClick={requestLocation}>Try Again</button>
                    </div>
                )}

                {/* Page Routes */}
                <main className="main-content">
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/current" element={<CurrentAQI />} />
                        <Route path="/prediction" element={<Prediction />} />
                        <Route path="/signin" element={<SignIn />} />
                        <Route path="/signup" element={<SignUp />} />
                    </Routes>
                </main>

                {/* Footer */}
                {routeLocation.pathname !== '/' && (
                    <footer className="footer">
                        <p>Powered by <strong>GA-KELM</strong> Machine Learning | Real-Time AQI Prediction System</p>
                    </footer>
                )}
            </div>
        </LocationContext.Provider>
    );
}

export default App;
