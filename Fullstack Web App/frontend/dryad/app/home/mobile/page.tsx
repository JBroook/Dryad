import Link from "next/link";
import { TbMapRoute } from "react-icons/tb";
import { IoWarningOutline } from "react-icons/io5";

export default function MobileHome() {
  return (
    <section className="mx-auto flex w-full max-w-lg flex-col gap-4 px-4 py-8">
      <div className="mb-2">
        <h1 className="text-2xl font-bold">Mobile home</h1>
        <p className="mt-1 text-secondary-content">
          Choose an area to continue.
        </p>
      </div>
      <Link
        href="/home/incidents"
        className="flex min-h-20 items-center gap-4 rounded-2xl border border-base-300 bg-base-200 p-5 text-lg font-semibold"
      >
        <IoWarningOutline className="text-2xl text-accent" />
        Incidents
      </Link>
      <Link
        href="/home/patrols"
        className="flex min-h-20 items-center gap-4 rounded-2xl border border-base-300 bg-base-200 p-5 text-lg font-semibold"
      >
        <TbMapRoute className="text-2xl text-accent" />
        Patrols
      </Link>
    </section>
  );
}
