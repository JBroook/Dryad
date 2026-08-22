import { useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function Project() {
  const searchParams = useSearchParams()
  const projectID = searchParams.get("pid")

  useEffect(()=>{
    
  }, [])
  return (<>

  </>);
}
