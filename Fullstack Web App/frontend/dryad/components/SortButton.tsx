import React from "react";
import GlowButton from "./GlowButton";
import { TbArrowsSort } from "react-icons/tb";
import { IoIosArrowDown, IoIosArrowUp } from "react-icons/io";

interface SortButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: ()=>void;
  active : boolean;
  ascending : boolean;
}

export default function SortButton({
  children,
  className = "",
  onClick=()=>{},
  active,
  ascending=true
}: SortButtonProps) {
    return (<>
      {active ?
        <GlowButton color="#4ADE80" className={className} onClick={onClick}>
            {children}
            {ascending ?
              <IoIosArrowUp />
              :
              <IoIosArrowDown />
            }
        </GlowButton>
        :
        <button 
        className={`btn border border-white/8 btn-secondary ${className}`}
        onClick={onClick}
        >
          {children}
          <TbArrowsSort />
        </button>
      }
    </>);
}