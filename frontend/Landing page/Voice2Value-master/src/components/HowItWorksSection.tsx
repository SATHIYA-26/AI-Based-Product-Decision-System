"use client";

import React from "react";

const steps = [
  {
    number: "1",
    title: "Connect Your SaaS",
    description: "Integrate Voice2Value with your existing infrastructure in minutes. We support all major SaaS platforms and frameworks.",
    details: ["API integration", "GitHub connection", "Revenue tracking setup"]
  },
  {
    number: "2", 
    title: "Detect Issues Instantly",
    description: "Our AI continuously monitors your application, identifying potential problems before they affect your users or revenue.",
    details: ["Real-time monitoring", "Anomaly detection", "Performance analysis"]
  },
  {
    number: "3",
    title: "Fix with One Click",
    description: "Review AI-generated solutions and apply fixes instantly or create pull requests for code changes.",
    details: ["One-click fixes", "Auto-generated PRs", "Manual review option"]
  }
];

export default function HowItWorksSection() {
  return (
    <section className="section section-dark">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">
            How It Works
          </h2>
          <p className="section-subtitle">
            Get started in minutes and protect your SaaS from day one.
          </p>
        </div>

        <div className="steps-grid">
          {steps.map((step, index) => (
            <div key={index} className="step-card">
              <div className="step-number">
                {step.number}
              </div>
              
              <h3 className="step-title">
                {step.title}
              </h3>
              
              <p className="step-description">
                {step.description}
              </p>
              
              <ul className="step-details">
                {step.details.map((detail, detailIndex) => (
                  <li key={detailIndex} className="step-detail">
                    {detail}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
