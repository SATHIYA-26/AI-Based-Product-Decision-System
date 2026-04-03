import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import FloatingLines from './FloatingLines';
import Form from './Form';
import Signup from './Signup';
import Navbar from './components/Navbar';
import HeroSection from './components/HeroSection';
import ProblemSection from './components/ProblemSection';
import FeaturesSection from './components/FeaturesSection';
import HowItWorksSection from './components/HowItWorksSection';
import CodeFixSection from './components/CodeFixSection';
import CTASection from './components/CTASection';
import Footer from './components/Footer';
import './App.css';

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
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={
          <>
            <div id="background-canvas"></div>
            <FloatingLines
              enabledWaves={['top', 'middle', 'bottom']}
              lineCount={7}
              lineDistance={5}
              bendRadius={5}
              bendStrength={-0.5}
              interactive={true}
              parallax={true}
              mixBlendMode="screen"
              linesGradient={["#47d8f5", "#2F4BC0", "#47aaf5"]}
            />
            <Form />
          </>
        } />
        <Route path="/signup" element={
          <>
            <div id="background-canvas"></div>
            <FloatingLines
              enabledWaves={['top', 'middle', 'bottom']}
              lineCount={7}
              lineDistance={5}
              bendRadius={5}
              bendStrength={-0.5}
              interactive={true}
              parallax={true}
              mixBlendMode="screen"
              linesGradient={["#47d8f5", "#2F4BC0", "#47aaf5"]}
            />
            <Signup />
          </>
        } />
        <Route path="/dashboard/*" element={<Navigate to="/dashboard.html" replace />} />
      </Routes>
    </Router>
  );
}

export default App;