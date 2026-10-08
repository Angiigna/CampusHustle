"""
CampusRide Seeding Script
Initializes SQLite database tables and seeds locations, fares, and demo accounts.
"""

from app import create_app, db
from app.models.models import User, RiderProfile, Location, Fare
from app.services.fare_service import LOCATION_NAMES, LOCATION_CATEGORIES, calculate_fare

app = create_app()

def seed_database():
    with app.app_context():
        print("Recreating database tables...")
        db.drop_all()
        db.create_all()

        # Realistic Campus Coordinates (Pondicherry University Campus)
        LOCATION_COORDS = {
            "GATE_1": (12.0280, 79.8550),
            "GATE_2": (12.0180, 79.8540),
            "ADMIN_BLOCK": (12.0250, 79.8560),
            "LIBRARY_AND_READING_ROOM": (12.0240, 79.8555),
            "SJ_AND_UMISARC": (12.0230, 79.8545),
            "SCIENCE_BLOCK": (12.0220, 79.8565),
            "LAW_DEPARTMENT": (12.0210, 79.8570),
            "SOM": (12.0235, 79.8560),
            "PERFORMING_ARTS": (12.0245, 79.8575),
            "PONLAIT": (12.0265, 79.8555),
            "HEALTH_CENTRE": (12.0255, 79.8545),
            "THIRUVALLUR_STADIUM": (12.0270, 79.8535),
            "RAJIV_GANDHI_STADIUM": (12.0195, 79.8550),
            # Girls Hostels
            "KANNAGI": (12.0268, 79.8572),
            "SAVITRIBAI_PHULE": (12.0266, 79.8574),
            "NARMADA": (12.0264, 79.8576),
            "KALPANA_CHAWLA": (12.0262, 79.8578),
            "MADAM_CURIE": (12.0260, 79.8580),
            "YAMUNA": (12.0258, 79.8582),
            "GANGA": (12.0256, 79.8584),
            "SARASWATHI": (12.0254, 79.8586),
            "CAUVERY": (12.0252, 79.8588),
            # Boys Hostels
            "CV_RAMAN": (12.0202, 79.8528),
            "BHARATHIDASAN": (12.0204, 79.8530),
            "SUBRAMANIA_BHARATHI": (12.0206, 79.8532),
            "KALIDAS": (12.0208, 79.8534),
            "AUROBINDO": (12.0210, 79.8536),
            "MAKA": (12.0212, 79.8538),
            "VALMIKI": (12.0214, 79.8540),
            "BIRSA_MUNDA": (12.0216, 79.8542),
            "ILLANGO_ADIGAL": (12.0218, 79.8544),
            "TAGORE": (12.0220, 79.8546),
            "KABIRDAS": (12.0222, 79.8548),
            "KAMBAN": (12.0224, 79.8550),
            "KANNADASAN": (12.0226, 79.8552),
            "SRK": (12.0228, 79.8554),
            # Messes
            "MOTHER_THERESA": (12.0260, 79.8580),
            "AMUDHAM": (12.0205, 79.8525),
            "MEGA_MESS": (12.0225, 79.8540),
        }

        category_map = {}
        for cat_info in LOCATION_CATEGORIES:
            cat_name = cat_info["category"]
            for loc in cat_info["locations"]:
                category_map[loc["code"]] = cat_name

        code_to_location_obj = {}
        for code, name in LOCATION_NAMES.items():
            category = category_map.get(code, "Other Areas")
            lat, lng = LOCATION_COORDS.get(code, (12.0230, 79.8550))
            loc = Location(code=code, name=name, category=category, latitude=lat, longitude=lng, active=True)
            db.session.add(loc)
            code_to_location_obj[code] = loc

        db.session.commit()
        print(f"Seeded {len(LOCATION_NAMES)} campus locations with coordinates.")

        print("Seeding fare combinations...")
        location_list = list(code_to_location_obj.items())
        fare_count = 0
        for i in range(len(location_list)):
            for j in range(i + 1, len(location_list)):
                code1, loc1 = location_list[i]
                code2, loc2 = location_list[j]
                amount = calculate_fare(code1, code2)
                
                # Bidirectional Fare Entries
                f1 = Fare(pickup_location_id=loc1.id, drop_location_id=loc2.id, amount=amount)
                f2 = Fare(pickup_location_id=loc2.id, drop_location_id=loc1.id, amount=amount)
                db.session.add_all([f1, f2])
                fare_count += 2
        
        db.session.commit()
        print(f"Seeded {fare_count} bidirectional fare entries.")

        print("Seeding Admin account...")
        admin = User(name="Angiigna", email="sivangisankar12a@gmail.com", phone="9999999999", role="ADMIN")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

        print("Database seeding completed successfully!")
        print("\n--- ADMIN ACCOUNT ---")
        print("Admin: sivangisankar12a@gmail.com / admin123 (Name: Angiigna)")

if __name__ == "__main__":
    seed_database()
