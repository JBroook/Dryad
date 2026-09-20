"use client"

import PatrolCard from "@/components/PatrolCard";
import ToggleGlowButton from "@/components/ToggleGlowButton";
import { apiFetch } from "@/lib/api";
import { useEffect, useState } from "react";
import { IncidentType } from "../project/page";
import { Member, Project } from "../projects/new/page";

export type Patrol = {
  id : number;
  incident : IncidentType;
  target : { type : string; coordinates : number[]};
  member : number;
  project : Project;
  assignedBy : {
    firstName : string;
    lastName : string;
    role : string;
  };
  assignedAt : string;
  status : string;
}

export default function Patrols() {
  const [patrols, setPatrols] = useState<Patrol[]>([]);
  const [filterIndex, setFilterIndex] = useState<number>(1);
  const [patrolIndex, setPatrolIndex] = useState<number>(-1);

  const filterOptions = [
    {title : "All", key : "all"},
    {title : "Pending", key : "pending"},
    {title : "Completed", key : "completed"},
    {title : "Cancelled", key : "cancelled"},
  ]
  
  const extractPatrols = (data : any)=>{
    setPatrols(data.map((patrol : any)=>{
      const incident = patrol.incident;
      return {...patrol,
        assignedBy : {
          ...patrol.assigned_by,
          firstName : patrol.assigned_by.user.first_name,
          lastName : patrol.assigned_by.user.last_name,
        },
        assignedAt : patrol.assigned_at,
        incident : {
          ...incident,
          threatClass : incident.threat_class,
          coordinates : {
            lat : parseFloat(incident.coordinates.coordinates[0]),
            lng : parseFloat(incident.coordinates.coordinates[1])
          }
        }
      }
    }))
  }

  const confirmPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
      e.preventDefault();

      await apiFetch(`http://127.0.0.1:8000/api/patrols/${patrols[patrolIndex].id}/complete_patrol`, {
          method : "POST",
          body : JSON.stringify({
            patrol_status : "completed",
            incident_status : "confirmed"
          })
      })
      .then(async (res) => {
          if (!res.ok) throw new Error(await res.text());
          return res.json();
      })
      .then(()=>{
        const newPatrols = [...patrols]
        newPatrols[patrolIndex].status = "completed"
        setPatrols(newPatrols)
      })
      .catch((err) => console.error("Fetch failed:", err));

      const modal = document.getElementById('confirmModal') as HTMLDialogElement;
      modal.close();
  }

  const dismissPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    await apiFetch(`http://127.0.0.1:8000/api/patrols/${patrols[patrolIndex].id}/complete_patrol`, {
      method : "POST",
      body : JSON.stringify({
        patrol_status : "completed",
        incident_status : "dismissed"
      })
    })
    .then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    })
    .then(()=>{
      const newPatrols = [...patrols]
      newPatrols[patrolIndex].status = "completed"
      setPatrols(newPatrols)
    })
    .catch((err) => console.error("Fetch failed:", err));

    const modal = document.getElementById('dismissModal') as HTMLDialogElement;
    modal.close();
  }

  const cancelPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    await apiFetch(`http://127.0.0.1:8000/api/patrols/${patrols[patrolIndex].id}/complete_patrol`, {
      method : "POST",
      body : JSON.stringify({
        patrol_status : "cancelled"
      })
    })
    .then(async (res) => {
      if (!res.ok) throw new Error(await res.text());
      return res.json();
    })
    .then(()=>{
      const newPatrols = [...patrols]
      newPatrols[patrolIndex].status = "cancelled"
      setPatrols(newPatrols)
    })
    .catch((err) => console.error("Fetch failed:", err));

    const modal = document.getElementById('cancelModal') as HTMLDialogElement;
    modal.close();
  }

  const openModal = (id : string, index : number)=>{
    const modal = document.getElementById(id) as HTMLDialogElement;
    modal.showModal();
    setPatrolIndex(index);
  }

  const closeModal = (id : string) => {
    const modal = document.getElementById(id) as HTMLDialogElement;
    modal.close();
  }

  useEffect(()=>{
    // fetch project incidents
    apiFetch(`http://127.0.0.1:8000/api/users/${1}/patrols/`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>{console.log(data); return data})
      .then((data)=>extractPatrols(data))
      .catch((err) => console.error("Fetch failed:", err));
  },[])

  let matchingPatrols = patrols;

  if(filterIndex!=0){
    matchingPatrols = patrols.filter(patrol => patrol.status===filterOptions[filterIndex].key)
  }

  return (<>
    <dialog id="cancelModal" className="modal">
      <div className="modal-box bg-base-200 border border-white/8">
        <h3 className="font-bold text-lg">Cancel Patrol?</h3>
        <p className="py-4 text-sm text-secondary-content">
          Do you want to cancel this patrol? Cancelling it will neither confirm nor dismiss the associated incident.
        </p>
        <div className="modal-action">
        <form onSubmit={cancelPatrol}>
          <button type="submit" className="btn btn-primary mr-2">Cancel Patrol</button>
          <button 
          type="button"
          onClick={() => closeModal("cancelModal")} className="btn btn-secondary">Close</button>
        </form>
        </div>
      </div>
    </dialog>

    <dialog id="confirmModal" className="modal">
      <div className="modal-box bg-base-200 border border-white/8">
        <h3 className="font-bold text-lg">Confirm Incident?</h3>
        <p className="py-4 text-sm text-secondary-content">
          By pressing "Confirm", you agree that you have personally validated this incident.
        </p>
        <p className="text-warning text-sm"><i>
          False confirmations may affect Dryad's predictions    
        </i></p>
        <div className="modal-action">
        <form onSubmit={confirmPatrol}>
          <button type="submit" className="btn btn-primary mr-2">Confirm</button>
          <button 
          type="button"
          onClick={() => closeModal("confirmModal")} className="btn btn-secondary">Cancel</button>
        </form>
        </div>
      </div>
    </dialog>

    <dialog id="dismissModal" className="modal">
      <div className="modal-box bg-base-200 border border-white/8">
        <h3 className="font-bold text-lg">Dismiss Incident?</h3>
        <p className="py-4 text-sm text-secondary-content">
          By pressing "Dimiss", you agree that you have personally witnessed that this report is inaccurate.
        </p>
        <p className="text-warning text-sm"><i>
          False dismissals may reduce Dryad's predictive capabilities.
        </i></p>
        <div className="modal-action">
        <form onSubmit={dismissPatrol}>
          <button type="submit" className="btn btn-error mr-2">Dismiss</button>
          <button 
          type="button"
          onClick={() => closeModal("dismissModal")} className="btn btn-secondary">Cancel</button>
        </form>
        </div>
      </div>
    </dialog>

    <div className="w-full py-5 pl-8 border-b-white/8 border-b border-b-width-[2px] flex flex-row items-center justify-between ">
      <div>
        <h1 className="font-bold text-2xl">
          My Patrols
        </h1>
        <p className="text-sm text-secondary-content">
          Field patrols dispatched to you
        </p>
      </div>
    </div>

    <div className="flex gap-2 mx-6 mt-4 items-center">
      {filterOptions.map((option, index)=>{
        return <ToggleGlowButton
        key={index}
        color="#34D399"
        active={filterIndex===index}
        onClick={()=>setFilterIndex(index)}
        >
          {option.title}
        </ToggleGlowButton>
      })}

      <p className="text-secondary-content ml-auto">
        {patrols.length} patrols
      </p>
    </div>

    <div className="mx-6 mt-5">
      {
        matchingPatrols.map((patrol, index)=>{
          return <PatrolCard
            key={index}
            color="#F97316"
            patrol={patrol}
            confirmPatrol={()=>openModal("confirmModal", index)}
            cancelPatrol={()=>openModal("cancelModal", index)}
            dismissPatrol={()=>openModal("dismissModal", index)}
          />
      })
      }
  </div>
  </>
  );
}
