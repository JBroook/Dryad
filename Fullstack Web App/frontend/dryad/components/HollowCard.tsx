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
    <div
      className={`rounded-xl border border-base-300 bg-base-200 shadow-[0_1px_0_rgba(18,43,31,0.04),0_10px_24px_rgba(18,43,31,0.04)] ${className}`}
      onClick={onClick}
    >
        {children}
    </div>);
}