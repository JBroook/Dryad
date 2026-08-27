import React from "react";
import GlowButton from "./GlowButton";

interface ToggleGlowButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: ()=>void;
  active : boolean;
  color : string;
}

export default function ToggleGlowButton({
  children,
  className = "",
  onClick=()=>{},
  active,
  color,
}: ToggleGlowButtonProps) {
    return (<>
      {active ?
        <GlowButton color={color} className={className} onClick={onClick}>
            {children}
        </GlowButton>
        :
        <button 
        className={`btn border border-white/8 btn-secondary ${className}`}
        onClick={onClick}
        >
          {children}
        </button>
      }
    </>);
}