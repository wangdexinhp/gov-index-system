def system_admin(request):
    """当前用户是否为系统管理员（superuser 或 membership_level=admin）。"""
    user = request.user
    is_admin = False
    if user.is_authenticated:
        if user.is_superuser:
            is_admin = True
        else:
            profile = getattr(user, "profile", None)
            if profile and profile.membership_level == "admin":
                is_admin = True
    return {"is_system_admin": is_admin}
