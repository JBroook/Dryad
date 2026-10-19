"use client"

import PatrolCard from "@/components/PatrolCard";
import ToggleGlowButton from "@/components/ToggleGlowButton";
import { apiFetch } from "@/library/api";
import { useEffect, useState } from "react";
import { IncidentType } from "../project/page";
import { Project } from "../projects/new/page";
import { TbMapRoute } from "react-icons/tb";
import RoutinePatrolCard from "@/components/RoutinePatrolCard";
import type { RoutinePatrol } from "@/components/ProjectView/PatrolsView";

export type Patrol = {
  id : number;
  incident : IncidentType;
  target : { type : string; coordinates : number[]};
  assignedMembers : {
    id : number;
    firstName : string;
    lastName : string;
    role : string;
  }[];
  project : Project;
  assignedBy : {
    firstName : string;
    lastName : string;
    role : string;
  };
  assignedAt : string;
  status : string;
}

export type SerializedPatrolMember = {
  id : number;
  role : string;
  user : {
    first_name : string;
    last_name : string;
  };
}

export default function Patrols() {
  const [patrols, setPatrols] = useState<Patrol[]>([]);
  const [routinePatrols, setRoutinePatrols] = useState<RoutinePatrol[]>([]);
  const [routineFetchError, setRoutineFetchError] = useState("");
  const [filterIndex, setFilterIndex] = useState<number>(1);
  const [patrolIndex, setPatrolIndex] = useState<number>(-1);
  const [confirmationCoordinates, setConfirmationCoordinates] = useState({
    latitude: "",
    longitude: ""
  });
  const [locationError, setLocationError] = useState("");

  const filterOptions = [
    {title : "All", key : "all", count : patrols.length + routinePatrols.length},
    {title : "Pending", key : "pending", count : patrols.reduce((count, patrol)=> {return patrol.status === "pending" ? (count + 1) : count}, 0)},
    {title : "Completed", key : "completed", count : patrols.reduce((count, patrol)=> {return patrol.status === "completed" ? (count + 1) : count}, 0)},
    {title : "Cancelled", key : "cancelled", count : patrols.reduce((count, patrol)=> {return patrol.status === "cancelled" ? (count + 1) : count}, 0)},
    // {title : "Routine", key : "routine", count : routinePatrols.length},
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
        assignedMembers : patrol.members.map((member : SerializedPatrolMember) => ({
          id : member.id,
          firstName : member.user.first_name,
          lastName : member.user.last_name,
          role : member.role,
        })),
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

  const resetConfirmationFields = () => {
    setConfirmationCoordinates({ latitude: "", longitude: "" });
    setLocationError("");
  }

  const validateConfirmationCoordinates = () => {
    const latitude = Number(confirmationCoordinates.latitude);
    const longitude = Number(confirmationCoordinates.longitude);

    return (
      confirmationCoordinates.latitude !== "" &&
      confirmationCoordinates.longitude !== "" &&
      !Number.isNaN(latitude) &&
      !Number.isNaN(longitude) &&
      latitude >= -90 &&
      latitude <= 90 &&
      longitude >= -180 &&
      longitude <= 180
    );
  }

  const fillWithCurrentLocation = () => {
    if (!navigator.geolocation) {
      setLocationError("Geolocation is not supported by this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setConfirmationCoordinates({
          latitude: position.coords.latitude.toString(),
          longitude: position.coords.longitude.toString(),
        });
        setLocationError("");
      },
      () => {
        setLocationError("Unable to access your location. Please enter the coordinates manually.");
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  }

  const confirmPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
      e.preventDefault();

      if (!validateConfirmationCoordinates()) {
        setLocationError("Please enter a valid latitude and longitude before confirming.");
        return;
      }

      const selectedPatrol = matchingPatrols[patrolIndex];
      if (!selectedPatrol) {
        return;
      }

      const latitude = Number(confirmationCoordinates.latitude);
      const longitude = Number(confirmationCoordinates.longitude);
      const patrolIndexInFullList = patrols.findIndex((patrol) => patrol.id === selectedPatrol.id);

      await apiFetch(`http://127.0.0.1:8000/api/patrols/${selectedPatrol.id}/complete_patrol`, {
          method : "POST",
          body : JSON.stringify({
            patrol_status : "completed",
            incident_status : "confirmed",
            latitude,
            longitude
          })
      })
      .then(async (res) => {
          if (!res.ok) throw new Error(await res.text());
          return res.json();
      })
      .then(()=>{
        if (patrolIndexInFullList === -1) {
          return;
        }

        const newPatrols = [...patrols]
        newPatrols[patrolIndexInFullList].status = "completed"
        setPatrols(newPatrols)
      })
      .catch((err) => console.error("Fetch failed:", err));

      const modal = document.getElementById('confirmModal') as HTMLDialogElement;
      modal.close();
      resetConfirmationFields();
  }

  const dismissPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    const selectedPatrol = matchingPatrols[patrolIndex];
    if (!selectedPatrol) {
      return;
    }

    const patrolIndexInFullList = patrols.findIndex((patrol) => patrol.id === selectedPatrol.id);

    await apiFetch(`http://127.0.0.1:8000/api/patrols/${selectedPatrol.id}/complete_patrol`, {
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
      if (patrolIndexInFullList === -1) {
        return;
      }

      const newPatrols = [...patrols]
      newPatrols[patrolIndexInFullList].status = "completed"
      setPatrols(newPatrols)
    })
    .catch((err) => console.error("Fetch failed:", err));

    const modal = document.getElementById('dismissModal') as HTMLDialogElement;
    modal.close();
  }

  const cancelPatrol = async (e : React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    const selectedPatrol = matchingPatrols[patrolIndex];
    if (!selectedPatrol) {
      return;
    }

    const patrolIndexInFullList = patrols.findIndex((patrol) => patrol.id === selectedPatrol.id);

    await apiFetch(`http://127.0.0.1:8000/api/patrols/${selectedPatrol.id}/complete_patrol`, {
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
      if (patrolIndexInFullList === -1) {
        return;
      }

      const newPatrols = [...patrols]
      newPatrols[patrolIndexInFullList].status = "cancelled"
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
    if (id === "confirmModal") {
      resetConfirmationFields();
    }
  }

  const closeModal = (id : string) => {
    const modal = document.getElementById(id) as HTMLDialogElement;
    modal.close();
    if (id === "confirmModal") {
      resetConfirmationFields();
    }
  }

  useEffect(()=>{
    const userID = localStorage.getItem("userID")
    if (!userID) {
      return;
    }

    apiFetch(`http://127.0.0.1:8000/api/users/${userID}/patrols/`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data)=>extractPatrols(data))
      .catch((err) => console.error("Fetch failed:", err));

    apiFetch(`http://127.0.0.1:8000/api/users/${userID}/routine_patrols/`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then((data: RoutinePatrol[]) => setRoutinePatrols(data))
      .catch((err) => {
        console.error("Routine patrol fetch failed:", err);
        setRoutineFetchError("Unable to load routine patrols.");
      });
  },[])

  const selectedFilter = filterOptions[filterIndex].key;
  const matchingPatrols = selectedFilter === "all"
    ? patrols
    : patrols.filter((patrol) => patrol.status === selectedFilter);
  const matchingRoutinePatrols = selectedFilter === "all" || selectedFilter === "routine"
    ? routinePatrols
    : [];
  const hasMatchingPatrols = matchingPatrols.length > 0 || matchingRoutinePatrols.length > 0;

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
        <h3 className="font-bold text-lg">Confirm Incident</h3>
        <p className="pt-4 text-sm text-secondary-content">
          By pressing "Confirm", you agree that you have personally validated this incident.
        </p>

        <div className="modal-action">
        <form onSubmit={confirmPatrol} className="w-full">
          <div className="pb-4">
            <label className="form-control w-full">
              <span className="label-text text-sm">Longitude</span>
              <input
                type="number"
                step="any"
                min={-180}
                max={180}
                value={confirmationCoordinates.longitude}
                onChange={(e) => {
                  setConfirmationCoordinates((prev) => ({ ...prev, longitude: e.target.value }));
                  setLocationError("");
                }}
                placeholder="-79.3832"
                className="input input-bordered w-full my-2"
                required
              />
            </label>

            <label className="form-control w-full">
              <span className="label-text text-sm mb-2">Latitude</span>
              <input
                type="number"
                step="any"
                min={-90}
                max={90}
                value={confirmationCoordinates.latitude}
                onChange={(e) => {
                  setConfirmationCoordinates((prev) => ({ ...prev, latitude: e.target.value }));
                  setLocationError("");
                }}
                placeholder="43.6532"
                className="input input-bordered w-full my-2"
                required
              />
            </label>

            <button
              type="button"
              className="btn btn-primary mt-2 btn-sm"
              onClick={fillWithCurrentLocation}
            >
              Fill with my location
            </button>

            {locationError && (
              <p className="text-error text-xs">{locationError}</p>
            )}
          </div>

          <button type="submit" className="btn btn-primary mr-2" disabled={!validateConfirmationCoordinates()}>Confirm</button>
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
          By pressing "Dismiss", you agree that you have personally witnessed that this report is inaccurate.
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

    <div className="flex w-full flex-row items-center justify-between border-b border-b-white/8 px-4 py-5 md:pl-8">
      <div className="min-w-0">
        <h1 className="font-bold text-2xl">
          My Patrols
        </h1>
        <p className="text-sm text-secondary-content">
          Field and routine patrols from your projects
        </p>
      </div>
    </div>

    <div className="mx-4 mt-4 flex flex-wrap items-center gap-2 md:mx-6">
      {filterOptions.map((option, index)=>{
        return <ToggleGlowButton
        key={index}
        color="#34D399"
        active={filterIndex===index}
        onClick={()=>setFilterIndex(index)}
        >
          {option.title} ({option.count})
        </ToggleGlowButton>
      })}

      <p className="ml-auto text-secondary-content">
        {patrols.length + routinePatrols.length} patrols
      </p>
    </div>

    <div className="mx-4 mt-5 md:mx-6">
      {routineFetchError && (selectedFilter === "all" || selectedFilter === "routine") && (
        <p role="alert" className="text-error">{routineFetchError}</p>
      )}
      {hasMatchingPatrols ?
        <>
        {matchingPatrols.map((patrol, index)=>(
          <PatrolCard
            key={`patrol-${patrol.id}`}
            color="#F97316"
            patrol={patrol}
            confirmPatrol={()=>openModal("confirmModal", index)}
            cancelPatrol={()=>openModal("cancelModal", index)}
            dismissPatrol={()=>openModal("dismissModal", index)}
          />
        ))}
        {matchingRoutinePatrols.map((patrol) => (
          <RoutinePatrolCard key={`routine-${patrol.id}`} patrol={patrol} />
        ))}
        </>
      :
      <div className="w-full flex flex-col justify-center items-center text-secondary-content pt-30">
        <TbMapRoute className="text-4xl"/>
        
        {selectedFilter!=="all" ?
          <h1>You have no {selectedFilter} patrols</h1>
          :
          <h1>You have no patrols</h1>
        }
        <p className="text-sm">Assign a patrol to yourself in a project to start</p>
      </div>
      }
  </div>
  </>
  );
}
