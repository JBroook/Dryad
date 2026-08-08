import React from "react";

interface HollowCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: ()=>void
}

export default function HollowCard({
  children,
  className = "",
  onClick=()=>{}
}: HollowCardProps) {
    return (
    <div className={`rounded-xl border border-white/8 bg-white/5 ${className}`} onClick={onClick}>
        {children}
    </div>);
}