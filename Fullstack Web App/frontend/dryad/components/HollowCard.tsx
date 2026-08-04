import React from "react";

interface HollowCardProps {
  children: React.ReactNode;
}

export default function HollowCard({ children }: HollowCardProps) {
    return (
    <div className="rounded-xl border border-white/8 bg-white/5">
        {children}
    </div>);
}