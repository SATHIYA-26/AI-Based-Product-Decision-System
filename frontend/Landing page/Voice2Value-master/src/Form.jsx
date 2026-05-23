import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Form.css';

const Form = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();

    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const result = await response.json();
      if (!response.ok || !result.ok) {
        const code = result?.code;
        const msg = {
          missing: 'Please fill in all fields.',
          invalid: 'Invalid email or password.',
          server: 'Server error. Check database connection.',
        }[code] || 'Login failed.';
        setError(msg);
        return;
      }

      window.location.href = '/dashboard.html';
    } catch (err) {
      setError('Unable to connect to server.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="form-overlay">
      <div className="login-card">
        <h2 className="login-title">Login</h2>

        <form className="login-form" onSubmit={handleLogin}>
          {error ? <p style={{ color: '#ef4444', marginBottom: '8px' }}>{error}</p> : null}
          <input 
            type="email" 
            placeholder="Email address" 
            className="login-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input 
            type="password" 
            placeholder="Password" 
            className="login-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <div className="login-options">
            <label className="remember-me">
              <input type="checkbox" />
              Remember me
            </label>
            <a href="/login.html" className="forgot-link">Forgot password?</a>
          </div>

          <p className="signup-text">
            Don't have an account?{' '}
            <a href="/signup" className="signup-link">Signup</a>
          </p>

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Form;