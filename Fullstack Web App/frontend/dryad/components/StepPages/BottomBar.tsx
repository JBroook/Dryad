import Link from "next/link";
import { FaArrowLeft, FaArrowRight } from "react-icons/fa";

interface BottomBarProps {
    formID : string;
    back : string;
    next : string;
    backEvent : ()=> void;
    nextEvent? : ()=> void;
    ready : boolean;
}

export default function BottomBar(props: BottomBarProps) {
    return (
        <div className="bg-secondary w-full h-18 shrink-0 border-t border-t-white/8 flex flex-row items-center justify-between">
            <button 
                className="btn text-secondary-content font-medium ml-5"
                onClick={props.backEvent}>
                <FaArrowLeft className="text-secondary-content"/>
                {props.back}
            </button>

            <button
                className={props.ready ? "btn btn-primary font-medium mr-5" : "btn font-medium mr-5"}
                disabled={!props.ready}
                form={props.formID}
                type="submit"
                onClick={props.nextEvent ? props.nextEvent : ()=>{}}
                >
                {props.next}
                <FaArrowRight/>
            </button>
        </div>);
}