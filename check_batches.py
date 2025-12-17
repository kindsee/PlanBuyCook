from app import app, db
from models import DishBatch, Dish

with app.app_context():
    batches = DishBatch.query.all()
    print(f'\n=== BATCHES EN BASE DE DATOS ({len(batches)} total) ===\n')
    for b in batches:
        print(f'ID: {b.id}')
        print(f'  Dish: {b.dish.name}')
        print(f'  Remaining: {b.percentage_remaining}%')
        print(f'  Ingredients Deducted: {b.ingredients_deducted}')
        print()
