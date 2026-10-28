
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import UserProfile, Product


class Command(BaseCommand):
    help = "Safely add missing FarmConnect sample products without deleting existing data"

    def handle(self, *args, **options):
        farmers_data = [
            {
                "username": "muthu_velan",
                "email": "muthu@pollachiorganic.in",
                "farm_name": "Pollachi Green Valley Organic Farm",
                "location": "Pollachi, Coimbatore",
                "lat": 10.6609,
                "lng": 77.0047,
                "products": [
                    {
                        "name": "Fresh Red Country Tomatoes",
                        "category": "vegetable",
                        "price": "35.00",
                        "stock": "150.00",
                        "unit": "kg",
                        "description": "Fresh red country tomatoes.",
                        "image_url": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Crisp Garden Green Spinach",
                        "category": "vegetable",
                        "price": "25.00",
                        "stock": "60.00",
                        "unit": "bunch",
                        "description": "Fresh green spinach leaves.",
                        "image_url": "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Green Bell Peppers (Capsicum)",
                        "category": "vegetable",
                        "price": "45.00",
                        "stock": "80.00",
                        "unit": "kg",
                        "description": "Fresh green capsicum.",
                        "image_url": "https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=800&auto=format&fit=crop&q=80",
                    },
                ],
            },
            {
                "username": "kavitha_nilgiris",
                "email": "kavitha@nilgirishill.in",
                "farm_name": "Nilgiris Mountain Mist Organics",
                "location": "Ooty, The Nilgiris",
                "lat": 11.4102,
                "lng": 76.6950,
                "products": [
                    {
                        "name": "Fresh Sweet Ooty Carrots",
                        "category": "vegetable",
                        "price": "45.00",
                        "stock": "180.00",
                        "unit": "kg",
                        "description": "Fresh hill-grown carrots.",
                        "image_url": "https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Hillside Fresh Strawberries",
                        "category": "fruit",
                        "price": "160.00",
                        "stock": "45.00",
                        "unit": "box",
                        "description": "Fresh strawberries.",
                        "image_url": "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=800&auto=format&fit=crop&q=80",
                    },
                ],
            },
            {
                "username": "selvam_orchards",
                "email": "selvam@salemorchards.in",
                "farm_name": "Salem Royal Mango & Fruit Belt",
                "location": "Salem",
                "lat": 11.6643,
                "lng": 78.1460,
                "products": [
                    {
                        "name": "Salem Sweet Alphonso Mangoes",
                        "category": "fruit",
                        "price": "140.00",
                        "stock": "70.00",
                        "unit": "kg",
                        "description": "Naturally sweet mangoes.",
                        "image_url": "https://images.unsplash.com/photo-1553279768-865429fa0078?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Seedless Sweet Black Grapes",
                        "category": "fruit",
                        "price": "90.00",
                        "stock": "110.00",
                        "unit": "kg",
                        "description": "Fresh sweet black grapes.",
                        "image_url": "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=800&auto=format&fit=crop&q=80",
                    },
                ],
            },
            {
                "username": "murugan_agro",
                "email": "murugan@dindigulcrops.in",
                "farm_name": "Dindigul Traditional Agro Fields",
                "location": "Dindigul",
                "lat": 10.3673,
                "lng": 77.9803,
                "products": [
                    {
                        "name": "Sun-Dried Red Onions",
                        "category": "vegetable",
                        "price": "32.00",
                        "stock": "250.00",
                        "unit": "kg",
                        "description": "Fresh red onions.",
                        "image_url": "https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=800&auto=format&fit=crop&q=80",
                    },
                    {
                        "name": "Fresh Ladies Finger",
                        "category": "vegetable",
                        "price": "35.00",
                        "stock": "50.00",
                        "unit": "kg",
                        "description": "Fresh green ladies finger.",
                        "image_url": "",
                    },
                ],
            },
        ]

        added = 0
        skipped = 0

        for farmer_data in farmers_data:
            farmer, created = User.objects.get_or_create(
                username=farmer_data["username"],
                defaults={"email": farmer_data["email"]},
            )

            # Change only profiles for newly created demo farmers.
            if created:
                profile, _ = UserProfile.objects.get_or_create(
                    user=farmer,
                    defaults={
                        "role": "farmer",
                        "farm_name": farmer_data["farm_name"],
                        "location": farmer_data["location"],
                        "district": farmer_data["location"],
                        "latitude": farmer_data["lat"],
                        "longitude": farmer_data["lng"],
                        "is_verified": True,
                    },
                )
                if profile.role != "farmer":
                    profile.role = "farmer"
                    profile.save(update_fields=["role"])

            for item in farmer_data["products"]:
                product, created = Product.objects.get_or_create(
                    farmer=farmer,
                    name=item["name"],
                    defaults={
                        "category": item["category"],
                        "price_per_kg": Decimal(item["price"]),
                        "stock_quantity": Decimal(item["stock"]),
                        "unit": item["unit"],
                        "description": item["description"],
                        "image_url": item["image_url"],
                        "harvest_date": timezone.now().date(),
                    },
                )

                if created:
                    added += 1
                    self.stdout.write(f"Added: {product.name}")
                else:
                    skipped += 1
                    self.stdout.write(f"Already exists: {product.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Added: {added}; already existed: {skipped}. "
                "Existing products were not deleted."
            )
        )
