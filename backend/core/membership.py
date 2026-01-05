from .models import MembershipLevel

def update_membership_level(passenger):
    pts = passenger.membership_points or 0
    if pts >= 10:
        name, min_pts, perks = "Platinum", 10, "Lounge access, extra baggage"
    elif pts >= 6:
        name, min_pts, perks = "Gold", 6, "Free checked bag, priority boarding"
    elif pts >= 3:
        name, min_pts, perks = "Silver", 3, "Standard boarding"
    else:
        name, min_pts, perks = "Bronze", 0, "Welcome aboard"

    lvl, _ = MembershipLevel.objects.get_or_create(
        level_name=name,
        defaults={"min_points_required": min_pts, "perks_description": perks},
    )
    passenger.membership_level = lvl
    passenger.save()