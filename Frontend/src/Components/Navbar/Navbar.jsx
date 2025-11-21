import React, { useState } from 'react';
import { Menu, X, Home, History, Info, Upload, Mail, LogIn, LogOut, User } from 'lucide-react';
import './Navbar.css';
import AnchorLink from "react-anchor-link-smooth-scroll";

const Navbar = ({ user, setUser }) => { // 👈 Accept user props
  const [isOpen, setIsOpen] = useState(false);
  const [menu, setMenu] = useState(""); 

  const handleClose = () => setIsOpen(false);

  const handleLogout = async () => {
    try {
      await fetch('http://127.0.0.1:5000/api/logout', { 
        method: 'POST',
        credentials: 'include'
      });
      setUser(null); // Update App state to logged out
      alert("Logged out successfully");
    } catch (error) {
      console.error("Logout failed", error);
    }
  };

  const navItems = [
    { name: 'Home', href: '#Home', icon: Home },
    { name: 'History', href: '#History', icon: History },
    { name: 'About', href: '#About', icon: Info },
    { name: 'Upload', href: '#Upload', icon: Upload },
    { name: 'Contact', href: '#Contact', icon: Mail }
  ];

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="navbar-container">
        <div className="navbar-logo">
          <div className="brand-box">US</div>
          <h1 className="brand-title">Upscale</h1>
        </div>

        {/* Desktop Links */}
        <div className="navbar-links">
          {navItems.map(item => {
            const Icon = item.icon;
            return (
              <a key={item.name} href={item.href} className="nav-link">
                <Icon size={18} />
                <span>{item.name}</span>
              </a>
            );
          })}

          {/* Conditional Rendering: Login or Logout */}
          <div className="nav-link login-link">
             {user ? (
               // LOGGED IN VIEW
               <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
                 <span style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#4CAF50', fontWeight: 'bold' }}>
                    <User size={18} /> {user.username}
                 </span>
                 <button 
                    onClick={handleLogout}
                    style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                 >
                    <LogOut size={18} /> Logout
                 </button>
               </div>
             ) : (
               // GUEST VIEW
               <AnchorLink
                  className="anchor-link"
                  href="#log"
                  offset={50}
                  onClick={() => {
                    setMenu("Login");
                    handleClose();
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: 'inherit' }}
                >
                  <LogIn size={18} />
                  <span>Log in</span>
                </AnchorLink>
             )}
          </div>
        </div>

        {/* Mobile Menu Toggle */}
        <button
          className="menu-toggle"
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
          aria-label="Toggle menu"
        >
          {isOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {isOpen && (
        <div className="mobile-menu">
          {navItems.map(item => {
            const Icon = item.icon;
            return (
              <a
                key={item.name}
                href={item.href}
                className="mobile-link"
                onClick={() => setIsOpen(false)}
              >
                <Icon size={20} />
                <span>{item.name}</span>
              </a>
            );
          })}
          
          {/* Mobile Auth */}
          <div className="mobile-link login-mobile">
             {user ? (
               <button 
                  onClick={() => { handleLogout(); handleClose(); }}
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', width: '100%', padding: 0, font: 'inherit' }}
               >
                  <LogOut size={20} />
                  <span>Logout ({user.username})</span>
               </button>
             ) : (
               <AnchorLink
                  className="anchor-link"
                  href="#log"
                  offset={50}
                  onClick={() => {
                    setMenu("Login");
                    handleClose();
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: 'inherit', width: '100%' }}
                >
                  <LogIn size={20} />
                  <span>Log in</span>
                </AnchorLink>
             )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;