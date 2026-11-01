import Link from "next/link";

interface NotFoundPageProps {
    title: string;
    description: string;
}

export default function NotFoundPage({ title, description }: NotFoundPageProps) {
    return (
        <main className="flex min-h-screen items-center justify-center bg-base-100 px-6">
            <div className="max-w-lg text-center">
                <p className="text-sm font-semibold uppercase tracking-widest text-accent">
                    404 · Not found
                </p>
                <h1 className="mt-3 text-3xl font-bold">{title}</h1>
                <p className="mt-3 text-secondary-content">{description}</p>
                <Link href="/home/projects" className="btn btn-primary mt-6">
                    Back to Projects
                </Link>
            </div>
        </main>
    );
}
