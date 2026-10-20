"use client"

import { Member } from "@/app/home/projects/new/page";
import GlowButton from "../GlowButton";
import { FaPlus } from "react-icons/fa";
import { useEffect, useState } from "react";
import { RxCross2 } from "react-icons/rx";
import { IoSearch } from "react-icons/io5";
import { apiFetch } from "@/library/api";
import { AiOutlineTeam } from "react-icons/ai";
import MemberCard from "../MemberCard";
import { useToast } from "../ToastProvider";

interface TeamViewProps {
    projectID : string | null;
    members : Member[];
    setMembers : (members : Member[])=>void;
    canManageMembers: boolean;
    canInviteMembers: boolean;
    canManageOwner: boolean;
}


export default function TeamView(props: TeamViewProps) {
    const { showToast } = useToast();
    const [openInviteTab, setOpenInviteTab] = useState<boolean>(false);
    const [searchMember, setSearchMember] = useState<string | null>(null);
    const [memberIndex, setMemberIndex] = useState(-1);
    const [currentUserID, setCurrentUserID] = useState<number | null>(null);

    const apiSearchMember = async (nameEmail : string) => {
        await apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/members?search=${nameEmail}`)
        .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
        })
        .then((data)=>props.setMembers(data.map((member : any)=>{
        return {...member, 
            firstName : member.user.first_name, 
            lastName : member.user.last_name,
            email : member.user.email,
            joinDate : member.join_date
        }
        })))
        .catch((err) => console.error("Fetch failed:", err));
    }

    const changeMemberRole = async (id : number, newRole : string) => {
        try {
            const response = await apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/members/${id}/`, {
                method: "PATCH",
                body: JSON.stringify({ role: newRole }),
            });
            if (!response.ok) throw new Error(await response.text());
            const data = await response.json();
            const newMembers = [...props.members];
            const editedMemberIndex = newMembers.findIndex(member=>member.id===id);
            newMembers[editedMemberIndex].role = newRole;
            props.setMembers(newMembers);
            showToast(data.message ?? "Member role updated successfully.");
        } catch (err) {
            console.error("Member role update failed:", err);
            showToast("Unable to update the member role.", "error");
        }
    }

    const closeModal = (id : string) => {
        const modal = document.getElementById(id) as HTMLDialogElement;
        modal.close();
    }

    const openModal = (index : number)=>{
        const modal = document.getElementById('removeModal') as HTMLDialogElement;
        modal.showModal();
        setMemberIndex(index);
    }
    
    const addMember: React.SubmitEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();

        const formData = new FormData(e.currentTarget);
        const email = formData.get("email");

        if (email && email.toString().length > 0) {
            apiFetch(
                `http://127.0.0.1:8000/api/projects/${props.projectID}/invite?email=${email}`,
                {
                    method: "POST"
                }
            )
                .then(async (res) => {
                    const data = await res.json();

                    if (!res.ok) {
                        throw new Error(data.details || "Something went wrong");
                    }

                    return data;
                })
                .then((data) => {
                    const newMember: Member = {
                        id: data.id,
                        firstName: data.user.first_name,
                        lastName: data.user.last_name,
                        email: data.user.email,
                        joinDate: data.join_date,
                        role: data.role
                    };

                    props.setMembers([...props.members, newMember]);
                    showToast(data.message ?? "Invitation sent successfully.");
                })
                .catch((err) => {
                    console.error("Fetch failed:", err);
                    showToast("Unable to send the project invitation.", "error");
                });
        } else {
            showToast("Please enter a valid email address.", "warning");
        }
    };

    
    const removeMember = (e : React.SubmitEvent<HTMLFormElement>) => {
        e.preventDefault();

        apiFetch(`http://127.0.0.1:8000/api/projects/${props.projectID}/members/${props.members[memberIndex].id}/`, {
            method: "DELETE",
        })
        .then(async (res) => {
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        })
        .then((data) => {
            props.setMembers(props.members.filter((_, i) => i !== memberIndex));
            showToast(data.message ?? "Member removed successfully.");
        })
        .catch((err) => {
            console.error("Member removal failed:", err);
            showToast("Unable to remove this member.", "error");
        });

        closeModal("removeModal")
    }

    useEffect(() => {
        const userID = Number(localStorage.getItem("userID"));
        setCurrentUserID(Number.isNaN(userID) ? null : userID);
    }, []);

    useEffect(() => {
        if(searchMember===null){
            return;
        }

        const timeout = setTimeout(() => {
            apiSearchMember(searchMember)
        }, 250);

        return () => clearTimeout(timeout);
    }, [searchMember]);

    return (<>
        <dialog id="removeModal" className="modal">
            <div className="modal-box bg-base-200 border border-white/8">
                {(memberIndex!==-1 && props.members.length>memberIndex) &&
                    <>
                    <h3 className="font-bold text-lg">Remove {props.members[memberIndex].firstName} {props.members[memberIndex].lastName}?</h3>
                    <p className="pt-4 text-sm text-secondary-content">
                        Removing this member is not a permanent action. The member can be reinvited later.
                    </p>
                    </>
                }
                <div className="modal-action">
                <form onSubmit={removeMember}>
                    <button type="submit" className="btn btn-error mr-2">Remove</button>
                    <button 
                    type="button"
                    onClick={() => closeModal("removeModal")} className="btn btn-secondary">Cancel</button>
                </form>
                </div>
            </div>
        </dialog>

        <div className="flex flex-row justify-between items-center mx-6 mt-6">
            <h1 className="font-semibold text-xl">
                Team Members ({props.members.length})
            </h1>

            {props.canInviteMembers && <div className="flex flex-row items-center">
                <GlowButton className="btn btn-accent" color="#4ADE80" onClick={()=>setOpenInviteTab(!openInviteTab)}>
                    <FaPlus />
                    Invite Member
                </GlowButton>
            </div>}
        </div>

        {props.canInviteMembers && openInviteTab &&
            <div className="flex flex-row items-center justify-between mx-6 mt-3 p-4 rounded-xl bg-primary/10 border border-primary/25">
                <IoSearch className="mr-3 text-secondary-content"/>

                <form onSubmit={addMember} className="flex flex-row w-full">
                    <input
                    name="email"
                    type="email"
                    className="input w-full bg-accent/15 flex-1"
                    placeholder="colleague@organization.org"
                    />

                    <button 
                    className="btn btn-primary ml-2"
                    type="submit">
                        Send
                    </button>
                </form>

                <button className="btn btn-secondary text-lg mx-2" onClick={()=>setOpenInviteTab(false)}>
                    <RxCross2/>
                </button>
            </div>}

        <div className="mx-6 mt-2">
            <label className="input bg-secondary w-full border border-white/8 mt-2">
                <IoSearch />
                <input type="search" className="grow" placeholder="Search by name or email..." onChange={(e)=>setSearchMember(e.target.value)} />
            </label>

            <div>
                {props.members.length>0 ?
                    <div className="mb-10">
                    {props.members.map((member, index)=>{
                        
                        return <MemberCard 
                        member={member} 
                        key={index} 
                        changeMemberRole={changeMemberRole}
                        removeModal={()=>openModal(index)}
                        canManage={props.canManageMembers}
                        canManageOwner={props.canManageOwner}
                        isCurrentUser={member.user?.id === currentUserID}
                        />;
                    })}
                    </div>
                :
                    <div className="w-full flex flex-col justify-center items-center text-secondary-content py-10">
                        <AiOutlineTeam className="text-4xl"/>
                        {searchMember===null ?
                        <>
                            <h1>No team members found</h1>
                            <p className="text-sm">You can invite members by clicking on "Invite Member"</p>
                        </> :
                            <h1>"{searchMember}" couldn't be found</h1>
                        }
                    </div>
                }
            </div>
        </div>
    </>);
}