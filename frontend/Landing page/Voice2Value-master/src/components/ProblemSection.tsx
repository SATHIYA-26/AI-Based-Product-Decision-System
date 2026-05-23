"use client";

import React from "react";

const problems = [
  {
    icon: "💰",
    title: "Revenue Leaks",
    description: "Silent issues in your SaaS that drain revenue without you knowing until it's too late."
  },
  {
    icon: "🐛",
    title: "Hidden Bugs",
    description: "Critical bugs hiding in your codebase that affect user experience and customer satisfaction."
  },
  {
    icon: "😤",
    title: "Customer Complaints",
    description: "Frustrated customers leaving bad reviews because issues weren't caught and fixed in time."
  }
];

export default function ProblemSection() {
  return (
    <section className="section section-dark">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">
            The Silent Killers of Your SaaS
          </h2>
          <p className="section-subtitle">
            Most SaaS failures don't happen overnight. They're the result of small issues that compound over time.
          </p>
        </div>

        <div className="problem-grid">
          {problems.map((problem, index) => (
            <div
              key={index}
              className="problem-card"
            >
              <div className="problem-icon">{problem.icon}</div>
              <h3 className="problem-title">
                {problem.title}
              </h3>
              <p className="problem-description">
                {problem.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
