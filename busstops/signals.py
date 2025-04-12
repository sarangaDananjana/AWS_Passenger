from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from booking.models import BusTrip


@receiver(post_save, sender=BusTrip)
def clear_bus_trip_cache(sender, instance, created, **kwargs):
    if created:  # Only trigger if a new BusTrip is created
        # Get all boarding points for the route associated with the BusTrip
        boarding_points = instance.route.route_boarding_points.all()

        # Loop through all combinations of boarding points to find the cache keys
        for i, start_point in enumerate(boarding_points):
            # Ensure start_point comes before end_point
            for end_point in boarding_points[i + 1:]:
                # Generate the cache key format: booking_search_{start_point_id}_{end_point_id}
                cache_key = f"booking_search_{start_point.id}_{end_point.id}"

                # Delete the cache for this particular start and end point combination
                cache.delete(cache_key)
                print(f"Cache for {cache_key} has been cleared.")
