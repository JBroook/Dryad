export type ProjectRole = "viewer" | "manager" | "admin" | "owner";

const roleLevels: Record<ProjectRole, number> = {
    viewer: 0,
    manager: 1,
    admin: 2,
    owner: 3,
};

export function hasProjectRole(
    role: ProjectRole | null,
    minimumRole: ProjectRole
): boolean {
    return role !== null && roleLevels[role] >= roleLevels[minimumRole];
}
