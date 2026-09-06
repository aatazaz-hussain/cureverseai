"use client";

import { useEffect, useState } from "react";

export default function IntroAnimation() {
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const alreadyPlayed = sessionStorage.getItem("cureverse-intro-played");

    if (alreadyPlayed) {
      return;
    }

    setVisible(true);
    sessionStorage.setItem("cureverse-intro-played", "true");

    return () => {};
  }, []);

  const handleVideoEnd = () => {
    setExiting(true);

    window.setTimeout(() => {
      setVisible(false);
    }, 850);
  };

  if (!visible) return null;

  return (
    <div
      className={`cv-intro ${exiting ? "cv-intro-exiting" : ""}`}
      aria-hidden="true"
    >
      <video
        className="cv-intro-video cv-intro-video-bg"
        src="/intro/cureverse-intro.mp4"
        autoPlay
        muted
        playsInline
        preload="auto"
        aria-hidden="true"
      />

      <video
        className="cv-intro-video cv-intro-video-main"
        src="/intro/cureverse-intro.mp4"
        autoPlay
        muted
        playsInline
        preload="auto"
        onEnded={handleVideoEnd}
      />

      <div className="cv-intro-overlay" />

      <div className="cv-intro-brand">
        <div className="cv-intro-mark">
          <i />
          <i />
        </div>

        <div className="cv-intro-name">
          <strong>CureVerse</strong>
          <b>AI</b>
        </div>

        <span>THE BIOLOGICAL INTELLIGENCE LAYER</span>
      </div>
    </div>
  );
}
