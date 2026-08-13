import Sidebar from "@/components/Sidebar";

export default function HomeLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (<>
    <div className="flex flex-row">
      <Sidebar />
      <main className="flex-1 min-w-0 ml-64">
        {children}
      </main>
    </div>
  </>);
}
