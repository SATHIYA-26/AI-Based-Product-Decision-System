import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';
import ProblemSection from './components/ProblemSection';
import FeaturesSection from './components/FeaturesSection';
import HowItWorksSection from './components/HowItWorksSection';
import CodeFixSection from './components/CodeFixSection';
import CTASection from './components/CTASection';
import Footer from './components/Footer';
import Form from './Form';
import Signup from './Signup';
import DashboardRouter from './components/dashboard/DashboardRouter';

function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <Navbar />
      <HeroSection />
      <ProblemSection />
      <FeaturesSection />
      <HowItWorksSection />
      <CodeFixSection />
      <CTASection />
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Form />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/dashboard/*" element={<DashboardRouter />} />
    </Routes>
  );
}

export default App;
