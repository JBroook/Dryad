interface Props {
  children: React.ReactNode;
}

export default function CenteredCard(props : Props) {
    return (
    <>
    <div className="rounded-xl bg-base-300 py-2 border border-white/8 flex flex-col items-center justify-center">
        {props.children}
    </div>
    </>);
}