#!/usr/bin/env python3
import os
import django
from pymongo import MongoClient

# 1. Bootstrap Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "passenger.settings")  # ← change to your settings module
django.setup()

# 2. Import your model
from busstops.models import BoardingPoint  # ← change your_app to your Django app name

# 3. Use your MongoDB URI
MONGO_URI = "mongodb+srv://dananjanasaranga:A0763003258z@cluster0.fkjv2k4.mongodb.net/Passenger?retryWrites=true&w=majority&appName=Cluster0"
client   = MongoClient(MONGO_URI)
mdb      = client.get_default_database()   # will pick up “Passenger” from the URI
collection = mdb.BoardingPoints          # collection name: boarding_points

# 4. (Optional) ensure a geospatial index on location
collection.create_index([("location", "2dsphere")])


for bp in BoardingPoint.objects.all():
    filter_query = {
        "name": bp.name,
        "province": bp.province,
        "city": bp.city
    }
    update_data = {
        "$set": {
            "longitude": bp.longitude,
            "latitude": bp.latitude,
        }
    }
    collection.update_one(filter_query, update_data, upsert=True)

print("✅ Boarding points upserted into MongoDB.")
