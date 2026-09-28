from rest_framework.permissions import BasePermission


def get_role(user):
    """Retourne le rôle de l'utilisateur : SUPERADMIN, ADMIN ou RESPONSABLE."""
    profil = getattr(user, 'profil', None)
    if profil:
        return profil.role
    return 'SUPERADMIN' if user.is_superuser else 'ADMIN'


class IsSuperAdmin(BasePermission):
    """Seul un SUPERADMIN peut gérer les comptes et les rôles."""
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and get_role(request.user) == 'SUPERADMIN'
        )