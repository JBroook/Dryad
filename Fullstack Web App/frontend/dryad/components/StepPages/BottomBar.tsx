import Link from "next/link";
import { FaArrowLeft, FaArrowRight } from "react-icons/fa";

interface BottomBarProps {
    formID : string;
    back : string;
    next : string;
    clickEvent : ()=> void;
}

export default function BottomBar(props: BottomBarProps) {
    return (
        <div className="bg-secondary w-full h-18 shrink-0 border-t border-t-white/8 flex flex-row items-center justify-between">
            <button 
                className="btn text-secondary-content font-medium ml-5"
                onClick={props.clickEvent}>
                <FaArrowLeft className="text-secondary-content"/>
                {props.back}
            </button>

            <button
                className="btn text-secondary-content font-medium mr-5"
                form={props.formID}
                type="submit"
                >
                {props.next}
                <FaArrowRight className="text-secondary-content"/>
            </button>
        </div>);
}