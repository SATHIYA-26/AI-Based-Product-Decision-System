"use client";

import React from "react";

export default function CodeFixSection() {
  return (
    <section className="section section-medium">
      <div className="container">
        <div className="section-header">
          <h2 className="section-title">
            AI Generates Pull Requests to Fix Your Backend Automatically
          </h2>
          <p className="section-subtitle">
            Our AI analyzes your codebase, identifies issues, and creates ready-to-merge pull requests.
          </p>
        </div>

        <div className="code-fix-container">
          {/* Mock GitHub PR Interface */}
          <div className="github-pr">
            <div className="pr-header">
              <div className="pr-author">
                <div className="pr-avatar"></div>
                <div className="pr-info">
                  <div className="pr-name">voice2value-ai</div>
                  <div className="pr-action">wants to merge 1 commit into main</div>
                </div>
              </div>
              <div className="pr-status">
                <span className="status-badge">Ready to merge</span>
              </div>
            </div>

            <div className="pr-content">
              <h3 className="pr-title">
                Fix: Resolve memory leak in user authentication service
              </h3>
              <p className="pr-description">
                This PR fixes a critical memory leak in the authentication service that was causing performance degradation during peak usage.
              </p>

              <div className="pr-stats">
                <div className="stat-line">
                  <div className="stat-dot red"></div>
                  <div className="stat-number">-1</div>
                  <div className="stat-file">src/services/auth.js</div>
                </div>
                <div className="stat-line">
                  <div className="stat-dot green"></div>
                  <div className="stat-number green">+3</div>
                  <div className="stat-file">src/services/auth.js</div>
                </div>
              </div>

              {/* Code diff mock */}
              <div className="code-diff">
                <div className="diff-line">
                  <span className="diff-marker neutral">@@ -45,7 +45,9 @@</span>
                </div>
                <div className="diff-line">
                  <span className="diff-marker red">-</span>
                  <span className="diff-content red">const session = new UserSession();</span>
                </div>
                <div className="diff-line">
                  <span className="diff-marker green">+</span>
                  <span className="diff-content green">const session = new UserSession();</span>
                </div>
                <div className="diff-line">
                  <span className="diff-marker green">+</span>
                  <span className="diff-content green">session.setMaxAge(3600000); // 1 hour</span>
                </div>
                <div className="diff-line">
                  <span className="diff-marker green">+</span>
                  <span className="diff-content green">session.enableAutoCleanup();</span>
                </div>
                <div className="diff-line">
                  <span className="diff-marker neutral"> </span>
                  <span className="diff-content neutral">return session.authenticate(token);</span>
                </div>
              </div>

              <div className="pr-actions">
                <button className="btn-merge">
                  Merge Pull Request
                </button>
                <button className="btn-view">
                  View Changes
                </button>
              </div>
            </div>
          </div>

          {/* Features explanation */}
          <div className="code-features">
            <div className="code-feature">
              <div className="code-feature-icon">
                <div className="feature-icon-inner"></div>
              </div>
              <h3 className="code-feature-title">
                Intelligent Code Analysis
              </h3>
              <p className="code-feature-description">
                Our AI analyzes your entire codebase to identify patterns, detect potential issues, and understand your application architecture.
              </p>
            </div>

            <div className="code-feature">
              <div className="code-feature-icon">
                <div className="feature-icon-inner"></div>
              </div>
              <h3 className="code-feature-title">
                Context-Aware Fixes
              </h3>
              <p className="code-feature-description">
                Each fix is generated with full context of your codebase, ensuring compatibility and following your coding standards.
              </p>
            </div>

            <div className="code-feature">
              <div className="code-feature-icon">
                <div className="feature-icon-inner"></div>
              </div>
              <h3 className="code-feature-title">
                Ready-to-Merge PRs
              </h3>
              <p className="code-feature-description">
                Get pull requests that are tested, documented, and ready for production deployment with minimal review.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
