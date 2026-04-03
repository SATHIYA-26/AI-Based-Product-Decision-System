import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Form.css';   // Reuse the same CSS for consistent styling

const Signup = () => {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSignup = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ fullName, email, password }),
      });

      const result = await response.json();
      if (!response.ok || !result.ok) {
        const code = result?.code;
        const msg = {
          missing: 'Please fill in all fields.',
          exists: 'An account with this email already exists.',
          server: 'Server error. Check database connection.',
        }[code] || 'Registration failed.';
        setError(msg);
        return;
      }

      navigate('/login');
    } catch (err) {
      setError('Unable to connect to server.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="form-overlay">
      <div className="login-card">
        <h2 className="login-title">Sign Up</h2>

        <form className="login-form" onSubmit={handleSignup}>
          {error ? <p style={{ color: '#ef4444', marginBottom: '8px' }}>{error}</p> : null}
          <input 
            type="text" 
            placeholder="Full Name" 
            className="login-input"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
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
          <input 
            type="password" 
            placeholder="Confirm Password" 
            className="login-input"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <div className="login-options">
            <label className="remember-me">
              <input type="checkbox" />
              I agree to the Terms and Conditions
            </label>
          </div>

          <p className="signup-text">
            Already have an account?{' '}
            <a href="/login" className="signup-link">Login</a>
          </p>

          <button type="submit" className="login-button" disabled={isLoading}>
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Signup;