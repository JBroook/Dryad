import { Ref } from "react";

interface ProjectCreatorProps {
  ref : Ref<HTMLDialogElement> | null;
}

export default function ProjectCreator(props: ProjectCreatorProps) {
    return (
      <dialog ref={props.ref} className="modal">
        <div className="modal-box bg-base-300 border border-white/8 border-width-[2px] p-0">
          <div className="w-full p-6 border-b border-b-white/8 border-width-[2px]">
            <h3 className="font-semibold text-lg">Create New Project</h3>
            <p className="text-secondary-content">Set up a forest monitoring area</p>
          </div>
          <div className="modal-action flex flex-col justify-start px-6 mt-3">
            <form method="dialog">
              <fieldset className="fieldset">
                <legend className="fieldset-legend font-medium text-[#A3ADA6]">Project Name*</legend>
                <input
                  type="text"
                  className="input w-full bg-[#273F2F]"
                  placeholder="Title"
                  // value={email}
                  // onChange={(e)=>setEmail(e.target.value)}
                />
              </fieldset>

              <fieldset className="fieldset">
                <legend className="fieldset-legend font-medium text-[#A3ADA6]">Project Name*</legend>
                <input
                  type="text"
                  className="input w-full bg-[#273F2F]"
                  placeholder="Title"
                  // value={email}
                  // onChange={(e)=>setEmail(e.target.value)}
                />
              </fieldset>
            </form>
          </div>
        </div>
      </dialog>
    );
}