import React, { useState, useEffect } from "react";
import Navbar from "./Components/Navbar/Navbar";
import Home from "./Pages/Home";
import Login from "./Pages/Login";
import Upload from "./Pages/Upload";
import History from "./Pages/History";
import Contact from "./Pages/Contact";
import About from "./Pages/About";

const App = () => {
  const [user, setUser] = useState(null); // Stores logged-in user info

  // 1. Check if user is logged in on page load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('http://127.0.0.1:5000/api/check-auth', {
          credentials: 'include' // Important to send the session cookie
        });
        const data = await response.json();
        if (data.authenticated) {
          setUser(data);
        }
      } catch (error) {
        console.error("Auth check failed:", error);
      }
    };
    checkAuth();
  }, []);

  return (
    <div>
      {/* Pass user state to Navbar to show/hide Login button */}
      <Navbar user={user} setUser={setUser} />
      
      <Home />
      <Upload />
      <History />
      <About />
      <Contact />
      
      {/* Pass setUser to Login so it can update state after successful login */}
      <Login setUser={setUser} />
    </div>
  );
};

export default App;