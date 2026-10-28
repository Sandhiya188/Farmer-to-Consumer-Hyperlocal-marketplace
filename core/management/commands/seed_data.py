from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import UserProfile, Product


class Command(BaseCommand):
    help = "Populate authentic farmers with real GPS map coordinates and original crop photography"

    def handle(self, *args, **options):
        self.stdout.write("Connecting real farmers to the original interactive map...")

        # 1. Admin
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser("admin", "admin@farmconnect.local", "admin123")
            UserProfile.objects.create(
                user=admin,
                role="farmer",
                farm_name="Central Agro Hub",
                phone_number="9876543210",
                location="Tamil Nadu Central",
                latitude=11.0168,
                longitude=76.9558,
                is_verified=True
            )

        # 2. Real Farmers with accurate GPS coordinates for the Live Map
        real_farmers = [
            {
                "username": "muthu_velan",
                "farm_name": "Pollachi Green Valley Organic Farm",
                "email": "muthu@pollachiorganic.in",
                "phone": "+91 98421 77881",
                "location": "Pollachi, Coimbatore",
                "address": "Survey 112, Anaimalai Road, Pollachi",
                "lat": 10.6609,
                "lng": 77.0047,
                "products": [
                    {
                        "name": "Fresh Red Country Tomatoes",
                        "category": "vegetable",
                        "price": Decimal("35.00"),
                        "stock": Decimal("150.00"),
                        "unit": "kg",
                        "desc": "Freshly handpicked vine-ripened red country tomatoes.",
                        "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Crisp Garden Green Spinach",
                        "category": "vegetable",
                        "price": Decimal("25.00"),
                        "stock": Decimal("60.00"),
                        "unit": "bunch",
                        "desc": "Tender spinach leaves harvested fresh with morning dew.",
                        "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Green Bell Peppers (Capsicum)",
                        "category": "vegetable",
                        "price": Decimal("45.00"),
                        "stock": Decimal("80.00"),
                        "unit": "kg",
                        "desc": "Crunchy thick-walled greenhouse capsicum.",
                        "image_url": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=800&auto=format&fit=crop&q=80",
                    },
                ],
            },
            {
                "username": "kavitha_nilgiris",
                "farm_name": "Nilgiris Mountain Mist Organics",
                "email": "kavitha@nilgirishill.in",
                "phone": "+91 94432 55660",
                "location": "Ooty, The Nilgiris",
                "address": "Estate Road, Coonoor-Ooty Valley",
                "lat": 11.4102,
                "lng": 76.6950,
                "products": [
                    {
                        "name": "Fresh Sweet Ooty Carrots",
                        "category": "vegetable",
                        "price": Decimal("45.00"),
                        "stock": Decimal("180.00"),
                        "unit": "kg",
                        "desc": "Crunchy, sweet hill-grown carrots washed in mountain spring water.",
                        "image_url": "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Hillside Fresh Strawberries",
                        "category": "fruit",
                        "price": Decimal("160.00"),
                        "stock": Decimal("45.00"),
                        "unit": "box",
                        "desc": "Fragrant hand-picked strawberries grown at 2000m altitude.",
                        "image_url": "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=800&auto=format&fit=crop&q=80",
                    },
                ],
            },
            {
                "username": "selvam_orchards",
                "farm_name": "Salem Royal Mango & Fruit Belt",
                "email": "selvam@salemorchards.in",
                "phone": "+91 97890 33441",
                "location": "Salem",
                "address": "Shevaroy Foothills, Yercaud Road, Salem",
                "lat": 11.6643,
                "lng": 78.1460,
                "products": [
                    {
                        "name": "Salem Sweet Alphonso Mangoes",
                        "category": "fruit",
                        "price": Decimal("140.00"),
                        "stock": Decimal("70.00"),
                        "unit": "kg",
                        "desc": "Tree-ripened, naturally sweet fragrant Alphonso mangoes.",
                        "image_url": "https://images.unsplash.com/photo-1553279768-865429fa0078?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Seedless Sweet Black Grapes",
                        "category": "fruit",
                        "price": Decimal("90.00"),
                        "stock": Decimal("110.00"),
                        "unit": "kg",
                        "desc": "Sweet crispy table grapes harvested directly from vines.",
                        "image_url": "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=800&auto=format&fit=crop&q=80",
                    },
                ],
            },
            {
                "username": "murugan_agro",
                "farm_name": "Dindigul Traditional Agro Fields",
                "email": "murugan@dindigulcrops.in",
                "phone": "+91 96551 22339",
                "location": "Dindigul",
                "address": "Palani Highway, Dindigul Agro Belt",
                "lat": 10.3673,
                "lng": 77.9803,
                "products": [
                    {
                        "name": "Sun-Dried Red Onions",
                        "category": "vegetable",
                        "price": Decimal("32.00"),
                        "stock": Decimal("250.00"),
                        "unit": "kg",
                        "desc": "Export quality sun-cured red onions with high shelf-life.",
                        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=800&auto=format&fit=crop&q=80",
                    },
                ],
            },
        ]

        # Reset old data
        Product.objects.all().delete()
        User.objects.filter(username__in=[
            "farmer_ramesh", "farmer_suresh", "customer_anita",
            "ramesh_farmer", "suresh_agro", "priya_farms"
        ]).delete()

        for f_data in real_farmers:
            user, _ = User.objects.get_or_create(
                username=f_data["username"],
                defaults={"email": f_data["email"]}
            )
            user.set_password("password123")
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = "farmer"
            profile.farm_name = f_data["farm_name"]
            profile.phone_number = f_data["phone"]
            profile.location = f_data["location"]
            profile.address = f_data["address"]
            profile.latitude = f_data["lat"]
            profile.longitude = f_data["lng"]
            profile.is_verified = True
            profile.save()

            for p in f_data["products"]:
                Product.objects.create(
                    farmer=user,
                    name=p["name"],
                    category=p["category"],
                    price_per_kg=p["price"],
                    stock_quantity=p["stock"],
                    unit=p["unit"],
                    description=p["desc"],
                    image_url=p["image_url"],
                    harvest_date=timezone.now().date(),
                )

        # Customer account
        cust, _ = User.objects.get_or_create(username="customer_user", defaults={"email": "customer@live.in"})
        cust.set_password("password123")
        cust.save()
        cp, _ = UserProfile.objects.get_or_create(user=cust)
        cp.role = "customer"
        cp.phone_number = "+91 98401 23456"
        cp.location = "Coimbatore City"
        cp.address = "12, Crosscut Road, Gandhipuram, Coimbatore"
        cp.is_verified = True
        cp.save()

        self.stdout.write(self.style.SUCCESS("Original farmers connected on the live map successfully!"))
