import React from "react";

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
  onClick=()=>{}
}: GlowButtonProps) {
    return (
      <button 
      className={`btn border ${className}`}
      onClick={onClick}
      style={{
        backgroundColor : `${color}26`,
        border : `1px solid ${color}40`,
        color : color
      }}
      >
        {children}
      </button>
    );
}