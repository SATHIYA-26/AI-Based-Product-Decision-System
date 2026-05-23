"use client";

import React from "react";
import { useNavigate } from "react-router-dom";

export default function CTASection() {
  const navigate = useNavigate();
  return (
    <section className="cta-section">
      <div className="cta-content">
        <h2 className="cta-title">
          Start Fixing Your SaaS Today
        </h2>
        <p className="cta-description">
          Join thousands of SaaS companies that use Voice2Value to monitor, detect, and fix issues automatically.
        </p>
        
        <div className="cta-buttons">
          <button className="btn-cta-primary" onClick={() => navigate('/signup')}>
            Get Started Free
          </button>
          <button className="btn-cta-secondary" onClick={() => navigate('/login')}>
            Login
          </button>
        </div>
        
        <div className="cta-features">
          <div className="cta-feature">
            <div className="cta-feature-dot"></div>
            No credit card required
          </div>
          <div className="cta-feature">
            <div className="cta-feature-dot"></div>
            14-day free trial
          </div>
          <div className="cta-feature">
            <div className="cta-feature-dot"></div>
            Cancel anytime
          </div>
        </div>
      </div>
    </section>
  );
}
