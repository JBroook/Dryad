"use client"

import GlowButton from "@/components/GlowButton"
import { apiFetch, logoutRequest } from "@/library/api"
import { useRouter } from "next/navigation"
import { useEffect, useRef, useState } from "react"
import { FaRegTrashAlt } from "react-icons/fa"
import { useToast } from "@/components/ToastProvider";
import UserAvatar from "@/components/UserAvatar";

export default function Account() {
  const { showToast } = useToast();
  const [firstName, setFirstName] = useState<string>("")
  const [lastName, setLastName] = useState<string>("")
  const [firstNameInput, setFirstNameInput] = useState<string>("")
  const [lastNameInput, setLastNameInput] = useState<string>("")
  const [email, setEmail] = useState<string>("")
  const [joinDate, setJoinDate] = useState<string>("")
  const [profilePicture, setProfilePicture] = useState<string | null>(null)
  const [pictureFile, setPictureFile] = useState<File | null>(null)
  const [picturePreview, setPicturePreview] = useState<string | null>(null)
  const pictureInputRef = useRef<HTMLInputElement>(null)
  
  const setUserInfo = (data : any) => {
    setFirstName(data.first_name);
    setLastName(data.last_name);
    setFirstNameInput(data.first_name);
    setLastNameInput(data.last_name);
    setEmail(data.email);
    setProfilePicture(data.profile_picture);
    const newJoinDate = new Date(data.date_joined);
    setJoinDate(newJoinDate.toLocaleDateString("en-US", {
      month: "long",
      year: "numeric",
    }));
  }

  useEffect(() => {
    if (!pictureFile) {
      setPicturePreview(null);
      return;
    }

    const previewUrl = URL.createObjectURL(pictureFile);
    setPicturePreview(previewUrl);
    return () => URL.revokeObjectURL(previewUrl);
  }, [pictureFile]);

  const router = useRouter()
  const logout = async ()=> {
    try {
      await logoutRequest();
    } catch (error) {
      console.error("Logout failed:", error);
    }
    router.push("/login");
    showToast("Signed out");
  }

  const saveProfile = async (e : React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    const userID = localStorage.getItem("userID")
    try {
      const response = await apiFetch(`users/${userID}/`, {
        method: "PATCH",
        body: JSON.stringify({
          first_name: firstNameInput,
          last_name: lastNameInput,
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setFirstName(firstNameInput);
      setLastName(lastNameInput);
      window.dispatchEvent(new Event("user-profile-updated"));
      showToast(data.message ?? "Profile updated successfully.");
    } catch (err) {
      console.error("Profile update failed:", err);
      showToast("Unable to update your profile.", "error");
    }
  }

  const uploadProfilePicture = async () => {
    if (!pictureFile) return;

    const userID = localStorage.getItem("userID");
    const formData = new FormData();
    formData.append("profile_picture", pictureFile);

    try {
      const response = await apiFetch(`users/${userID}/`, {
        method: "PATCH",
        body: formData,
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setProfilePicture(data.profile_picture);
      setPictureFile(null);
      if (pictureInputRef.current) pictureInputRef.current.value = "";
      window.dispatchEvent(new Event("user-profile-updated"));
      showToast(data.message ?? "Profile picture updated successfully.");
    } catch (err) {
      console.error("Profile picture upload failed:", err);
      showToast("Unable to upload your profile picture.", "error");
    }
  }

  const removeProfilePicture = async () => {
    const userID = localStorage.getItem("userID");

    try {
      const response = await apiFetch(`users/${userID}/`, {
        method: "PATCH",
        body: JSON.stringify({ profile_picture: null }),
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setProfilePicture(data.profile_picture);
      setPictureFile(null);
      if (pictureInputRef.current) pictureInputRef.current.value = "";
      window.dispatchEvent(new Event("user-profile-updated"));
      showToast(data.message ?? "Profile picture removed.");
    } catch (err) {
      console.error("Profile picture removal failed:", err);
      showToast("Unable to remove your profile picture.", "error");
    }
  }

  const deleteAccount = async (e : React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      const response = await apiFetch(`delete_account/`, {
        method: "POST",
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      try {
        await logoutRequest();
      } catch (error) {
        console.error("Session cleanup failed:", error);
      }
      showToast(data.message ?? "Account deleted successfully.");
      router.push("/login");
    } catch (err) {
      console.error("Account deletion failed:", err);
      showToast("Unable to delete your account.", "error");
    }
  }

  const openModal = (id : string)=>{
    const modal = document.getElementById(id) as HTMLDialogElement;
    modal.showModal();
  }

  const closeModal = (id : string) => {
    const modal = document.getElementById(id) as HTMLDialogElement;
    modal.close();
  }

  useEffect(()=>{
    const userID = localStorage.getItem("userID")
    apiFetch(`users/${userID}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      })
      .then(setUserInfo)
      .catch((err) => console.error("Fetch failed:", err));
  }, [])

  return (<>
    <dialog id="deleteModal" className="modal">
      <div className="modal-box bg-base-200 border border-white/8">
        <h3 className="font-bold text-lg">Delete Account?</h3>
        <p className="py-4 text-sm text-secondary-content">
          Are you sure you want to delete your account? This action is <strong>permanent</strong>. All data related to this account will be removed.
        </p>
        <div className="modal-action">
        <form onSubmit={deleteAccount}>
          <button type="submit" className="btn btn-error mr-2">Delete Account</button>
          <button 
          type="button"
          onClick={() => closeModal("deleteModal")} className="btn btn-secondary">Close</button>
        </form>
        </div>
      </div>
    </dialog>

    <div className="w-full py-5 pl-8 border-b-white/8 border-b border-b-width-[2px] flex flex-row items-center justify-between ">
      <div>
        <h1 className="font-bold text-2xl">
          My Account
        </h1>
        <p className="text-sm text-secondary-content">
          Manage your profile and security
        </p>
      </div>
    </div>

    <div className="mx-30 mb-30">
      <div className="bg-base-200 rounded-2xl border border-white/8 mt-6 flex py-4 px-8 items-center">
        <UserAvatar
          firstName={firstName}
          lastName={lastName}
          email={email}
          profilePicture={picturePreview ?? profilePicture}
          sizeClassName="w-20"
        />

        <div className="flex-1 ml-4">
          <h1 className="text-xl font-semibold">{firstName} {lastName}</h1>
          <p className="text-sm text-secondary-content">{email}</p>
        </div>

        <p className="text-sm text-secondary-content">Member since {joinDate}</p>
      </div>

      <div className="card bg-base-200 rounded-2xl border border-white/8 mt-4">
        <div className="card-body">
          <h2 className="card-title text-lg">Profile Information</h2>
          <p className="text-secondary-content">Update your personal details</p>

        <div className="mt-4 flex flex-wrap items-end gap-3">
          <fieldset className="fieldset min-w-64 flex-1">
            <legend className="fieldset-legend font-medium text-secondary-content">
              Profile Picture
            </legend>
            <input
              ref={pictureInputRef}
              type="file"
              accept="image/*"
              className="file-input w-full bg-base-200"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                if (file && file.size > 5 * 1024 * 1024) {
                  showToast("Profile pictures must be 5 MB or smaller.", "error");
                  event.target.value = "";
                  return;
                }
                setPictureFile(file);
              }}
            />
          </fieldset>
          <button
            type="button"
            className="btn btn-primary"
            disabled={!pictureFile}
            onClick={uploadProfilePicture}
          >
            Upload Picture
          </button>
          {profilePicture && (
            <button
              type="button"
              className="btn btn-ghost text-error"
              onClick={removeProfilePicture}
            >
              Remove Picture
            </button>
          )}
        </div>

        <form className="flex flex-col" onSubmit={saveProfile}>
          <div className="flex gap-4">
            <fieldset className="fieldset flex-1">
              <legend className="fieldset-legend font-medium text-secondary-content">First Name</legend>
              <input
                type="text"
                className="input w-full bg-base-200 border border-base-300 text-base-content"
                placeholder="Jane"
                value={firstNameInput}
                onChange={(e)=>setFirstNameInput(e.target.value)}
              />
            </fieldset>

            <fieldset className="fieldset flex-1">
              <legend className="fieldset-legend font-medium text-secondary-content">Last Name</legend>
              <input
                type="text"
                className="input w-full bg-base-200 border border-base-300 text-base-content"
                placeholder="Smith"
                value={lastNameInput}
                onChange={(e)=>setLastNameInput(e.target.value)}
              />
            </fieldset>
          </div>

          <fieldset className="fieldset">
            <legend className="fieldset-legend font-medium text-secondary-content">Email Address</legend>
            <input
              type="email"
              className="input w-full bg-base-200 border border-base-300 text-secondary-content"
              value={email}
              disabled={true}
            />
          </fieldset>

          <button className="btn btn-primary mt-4 ml-auto">
            Save Profile
          </button>
        </form>
        </div>
      </div>

      <div className="card bg-base-200 rounded-2xl border border-error/50 mt-4">
        <div className="card-body">
          <h2 className="card-title text-lg text-error">Danger Zone</h2>
          <p className="text-secondary-content">Permanent and irreversible actions</p>

          <div className="flex mt-4">
            <div className="flex-1">
              <h1 className="font-semibold text-base">Sign Out</h1>
              <p className="text-secondary-content text-sm">End your current session on this device</p>
            </div>

            <button className="btn btn-warning" onClick={logout}>
              Sign Out
            </button>
          </div>

          <div className="mt-4">
              <h1 className="font-semibold text-base">Delete Account</h1>
              <p className="text-secondary-content text-sm">Permanently delete your account and all associated data. This cannot be undone and will remove you from all projects.</p>

            <GlowButton className="btn btn-error mt-4" color="#EF4444" onClick={()=>openModal("deleteModal")}>
              <FaRegTrashAlt />
              Delete Account
            </GlowButton>
          </div>
        </div>
      </div>
      
    </div>
  </>
  );
}
