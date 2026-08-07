import React from "react";

interface HollowCardProps {
  children: React.ReactNode;
  className?: string;
}

export default function HollowCard({
  children,
  className = "",
}: HollowCardProps) {
    return (
    <div className={`rounded-xl border border-white/8 bg-white/5 ${className}`}>
        {children}
    </div>);
}