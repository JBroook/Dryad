"use client";

import React, { useEffect, useState } from "react";
import { useTheme } from "next-themes";

interface GlowButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: ()=>void;
  disabled? : boolean;
  color : string;
}

export default function GlowButton({
  children,
  className = "",
  color,
  onClick=()=>{},
  disabled=false
}: GlowButtonProps) {
    const { theme } = useTheme();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
      setMounted(true);
    }, []);

    const isLightTheme = mounted && theme === "mytheme-light";

    return (
      <button 
      className={`btn border ${className}`}
      onClick={onClick}
      disabled={disabled}
      style={{
        backgroundColor : isLightTheme ? `${color}1f` : `${color}26`,
        border : isLightTheme ? `1px solid ${color}66` : `1px solid ${color}40`,
        color : isLightTheme ? "#183F2F" : color,
        boxShadow: isLightTheme ? `0 0 0 1px ${color}33, 0 8px 22px ${color}1a` : "none",
      }}
      >
        {children}
      </button>
    );
}