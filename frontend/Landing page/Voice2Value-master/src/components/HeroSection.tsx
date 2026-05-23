"use client";

import React, { useRef } from "react";
import { useScroll, useTransform } from "motion/react";
import { useNavigate } from "react-router-dom";
import { GoogleGeminiEffect } from "./ui/google-gemini-effect";

export default function HeroSection() {
  const ref = useRef(null);
  const navigate = useNavigate();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });

  const pathLengthFirst = useTransform(scrollYProgress, [0, 0.8], [0.2, 1.2]);
  const pathLengthSecond = useTransform(scrollYProgress, [0, 0.8], [0.15, 1.2]);
  const pathLengthThird = useTransform(scrollYProgress, [0, 0.8], [0.1, 1.2]);
  const pathLengthFourth = useTransform(scrollYProgress, [0, 0.8], [0.05, 1.2]);
  const pathLengthFifth = useTransform(scrollYProgress, [0, 0.8], [0, 1.2]);

  return (
    <div 
      className="min-h-screen bg-black w-full relative overflow-hidden"
      ref={ref}
    >
      <GoogleGeminiEffect
        pathLengths={[
          pathLengthFirst,
          pathLengthSecond,
          pathLengthThird,
          pathLengthFourth,
          pathLengthFifth,
        ]}
      />
      
      <div style={{
        position: 'absolute',
        top: '240px',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 50,
        textAlign: 'center',
        width: '100%',
        maxWidth: '1200px',
        padding: '0 24px',
        pointerEvents: 'none'
      }}>
        <h1 style={{
          fontSize: 'clamp(2.5rem, 8vw, 5rem)',
          fontWeight: 'bold',
          background: 'linear-gradient(to right, #60a5fa, #67e8f9, #3b82f6)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          color: 'transparent',
          marginBottom: '24px',
          letterSpacing: '-0.025em',
          marginLeft: '280px',
          marginTop: '100px'
        }}>
          Voice2Value
        </h1>

        <p style={{
          fontSize: 'clamp(1.125rem, 3vw, 1.5rem)',
          color: '#e5e7eb',
          marginTop: '24px',
          maxWidth: '900px',
          marginLeft: '280px',
          marginRight: 'auto',
          lineHeight: '1.75',
          fontWeight: '300',
          marginBottom: '30px'
        }}>
          AI-Powered SaaS Monitoring & Automated Issue Resolution
        </p>

        <div style={{
          display: 'flex',
          flexDirection: 'row',
          gap: '24px',
          justifyContent: 'center',
          alignItems: 'center',
          flexWrap: 'wrap',
          pointerEvents: 'auto'
        }}>
          <button 
            onClick={() => navigate('/login')}
            style={{
              padding: '16px 32px',
              background: 'linear-gradient(to right, #3b82f6, #06b6d4)',
              color: 'white',
              border: 'none',
              borderRadius: '12px',
              fontSize: '18px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.3)',
              marginTop: '1.8px',
              marginLeft: '280px'
            }}>
              Get Started Free
            </button>
          <button style={{
            padding: '16px 32px',
            background: 'transparent',
            color: 'white',
            border: '2px solid #6b7280',
            borderRadius: '12px',
            fontSize: '18px',
            fontWeight: '600',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            marginTop: '1.8px'
          }}>
            Watch Demo
          </button>
        </div>
      </div>
    </div>
  );
}
