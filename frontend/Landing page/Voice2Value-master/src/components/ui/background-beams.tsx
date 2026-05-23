"use client";

import React, { useEffect, useRef } from "react";

interface MousePosition {
  x: number;
  y: number;
}

export function BackgroundBeams() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mousePosition = useRef<MousePosition>({ x: 0, y: 0 });
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    const handleMouseMove = (e: MouseEvent) => {
      mousePosition.current = { x: e.clientX, y: e.clientY };
    };

    window.addEventListener("mousemove", handleMouseMove);

    const beams: Array<{
      x: number;
      y: number;
      length: number;
      speed: number;
      angle: number;
      opacity: number;
    }> = [];

    // Initialize beams
    for (let i = 0; i < 15; i++) {
      beams.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        length: Math.random() * 200 + 100,
        speed: Math.random() * 2 + 1,
        angle: Math.random() * Math.PI * 2,
        opacity: Math.random() * 0.5 + 0.1,
      });
    }

    const animate = () => {
      ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      beams.forEach((beam) => {
        // Update beam position
        beam.x += Math.cos(beam.angle) * beam.speed;
        beam.y += Math.sin(beam.angle) * beam.speed;

        // Wrap around edges
        if (beam.x < 0) beam.x = canvas.width;
        if (beam.x > canvas.width) beam.x = 0;
        if (beam.y < 0) beam.y = canvas.height;
        if (beam.y > canvas.height) beam.y = 0;

        // Calculate distance from mouse
        const dx = mousePosition.current.x - beam.x;
        const dy = mousePosition.current.y - beam.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Adjust opacity based on mouse proximity
        const maxDistance = 200;
        const proximityOpacity = Math.max(0, 1 - distance / maxDistance);
        const finalOpacity = beam.opacity + proximityOpacity * 0.3;

        // Draw beam
        const gradient = ctx.createLinearGradient(
          beam.x,
          beam.y,
          beam.x + Math.cos(beam.angle) * beam.length,
          beam.y + Math.sin(beam.angle) * beam.length
        );

        gradient.addColorStop(0, `rgba(71, 216, 245, 0)`);
        gradient.addColorStop(0.5, `rgba(71, 216, 245, ${finalOpacity})`);
        gradient.addColorStop(1, `rgba(47, 75, 192, 0)`);

        ctx.strokeStyle = gradient;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(beam.x, beam.y);
        ctx.lineTo(
          beam.x + Math.cos(beam.angle) * beam.length,
          beam.y + Math.sin(beam.angle) * beam.length
        );
        ctx.stroke();
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      window.removeEventListener("mousemove", handleMouseMove);
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 h-full w-full"
      style={{ background: "transparent" }}
    />
  );
}
