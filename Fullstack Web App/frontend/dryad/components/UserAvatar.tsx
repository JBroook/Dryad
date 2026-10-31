type UserAvatarProps = {
    firstName?: string | null;
    lastName?: string | null;
    email?: string | null;
    profilePicture?: string | null;
    sizeClassName?: string;
};

export default function UserAvatar({
    firstName = "",
    lastName = "",
    email = "",
    profilePicture,
    sizeClassName = "w-8",
}: UserAvatarProps) {
    const initials = (
        `${(firstName ?? "").trim().charAt(0)}${(lastName ?? "").trim().charAt(0)}` ||
        (email ?? "").trim().charAt(0) ||
        "?"
    ).toUpperCase();
    const name = `${firstName ?? ""} ${lastName ?? ""}`.trim();

    return (
        <div className="avatar shrink-0">
            <div className={`${sizeClassName} rounded-full`}>
                {profilePicture ? (
                    <img
                        src={profilePicture}
                        alt={name ? `${name} profile picture` : "Profile picture"}
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-primary font-semibold text-primary-content">
                        {initials}
                    </div>
                )}
            </div>
        </div>
    );
}
