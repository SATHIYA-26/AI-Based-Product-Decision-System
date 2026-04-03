"use client";

import { useNavigate } from "react-router-dom";

export function Navbar() {
  const navigate = useNavigate();
  const navItems = [
    {
      name: "Features",
      link: "#features",
    },
    {
      name: "Pricing",
      link: "#pricing",
    },
    {
      name: "Contact",
      link: "#contact",
    },
  ];

  return (
    <div style={{ position: 'relative', width: '100%', zIndex: 100, backgroundColor: 'black' }}>
      {/* Desktop Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 24px', backgroundColor: 'black' }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ width: '32px', height: '32px', background: 'linear-gradient(to right, #3b82f6, #06b6d4)', borderRadius: '8px' }}></div>
          <span style={{ marginLeft: '12px', fontSize: '20px', fontWeight: 'bold', color: 'white' }}>Voice2Value</span>
        </div>

        {/* Nav Items */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          {navItems.map((item, idx) => (
            <a
              key={idx}
              href={item.link}
              style={{ color: '#d1d5db', textDecoration: 'none', fontSize: '14px', fontWeight: '500' }}
            >
              {item.name}
            </a>
          ))}
        </div>

        {/* Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button
            onClick={() => navigate('/login')}
            style={{ padding: '8px 16px', color: '#d1d5db', border: '1px solid #4b5563', borderRadius: '8px', fontSize: '14px', fontWeight: '500', backgroundColor: 'transparent', cursor: 'pointer' }}
          >
            Login
          </button>
          <button
            onClick={() => navigate('/signup')}
            style={{ padding: '8px 24px', background: 'linear-gradient(to right, #3b82f6, #06b6d4)', color: 'white', border: 'none', borderRadius: '8px', fontSize: '14px', fontWeight: '500', cursor: 'pointer' }}
          >
            Sign up
          </button>
        </div>
      </div>
    </div>
  );
}

export default Navbar;
