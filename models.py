"""
Modelos de base de datos para PlanBuyCook

Define las entidades principales:
- Day: Días del calendario
- Meal: Comidas (desayuno, almuerzo, cena)
- Dish: Platos disponibles
- Ingredient: Ingredientes base
- DishIngredient: Relación entre platos e ingredientes con cantidades
- PantryStock: Stock actual del almacén
- ShoppingList: Lista de compra generada
- ShoppingItem: Items individuales de la lista de compra
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

db = SQLAlchemy()


class Ingredient(db.Model):
    """
    Ingrediente base con unidad de medida
    """
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit = db.Column(db.String(20), nullable=False)  # g, kg, ml, l, unidades, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    pantry_stock = db.relationship('PantryStock', backref='ingredient', uselist=False, cascade='all, delete-orphan')
    dish_ingredients = db.relationship('DishIngredient', backref='ingredient', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Ingredient {self.name} ({self.unit})>'


class PantryStock(db.Model):
    """
    Stock de ingredientes con doble contador:
    - stock_actual: Lo que realmente tienes físicamente
    - stock_planificado: actual - lo planificado (puede ser negativo = hay que comprar)
    """
    __tablename__ = 'pantry_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False, unique=True)
    stock_actual = db.Column(db.Float, nullable=False, default=0.0)  # Stock real físico
    stock_planificado = db.Column(db.Float, nullable=False, default=0.0)  # Descontando planificación
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mantenemos quantity para compatibilidad (deprecated)
    @property
    def quantity(self):
        """Compatibilidad: retorna stock_actual"""
        return self.stock_actual
    
    def __repr__(self):
        return f'<PantryStock {self.ingredient.name}: actual={self.stock_actual}, planificado={self.stock_planificado} {self.ingredient.unit}>'


class Dish(db.Model):
    """
    Plato con nombre, descripción e ingredientes asociados
    """
    __tablename__ = 'dishes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    ingredients = db.relationship('DishIngredient', backref='dish', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Dish {self.name}>'
    
    def get_total_ingredients(self):
        """Retorna diccionario con ingredientes y cantidades necesarias"""
        return {
            di.ingredient_id: {
                'ingredient': di.ingredient,
                'quantity': di.quantity
            }
            for di in self.ingredients
        }


class DishIngredient(db.Model):
    """
    Relación entre plato e ingrediente con cantidad específica
    """
    __tablename__ = 'dish_ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)  # Cantidad en la unidad del ingrediente
    
    __table_args__ = (
        db.UniqueConstraint('dish_id', 'ingredient_id', name='unique_dish_ingredient'),
        CheckConstraint('quantity > 0', name='check_dish_quantity_positive'),
    )
    
    def __repr__(self):
        return f'<DishIngredient {self.dish.name}: {self.quantity} {self.ingredient.unit} of {self.ingredient.name}>'


class Day(db.Model):
    """
    Día del calendario con sus comidas
    """
    __tablename__ = 'days'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    meals = db.relationship('Meal', backref='day', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Day {self.date}>'
    
    def get_meal(self, meal_type):
        """Obtiene la comida específica del día"""
        return next((m for m in self.meals if m.meal_type == meal_type), None)


class DishBatch(db.Model):
    """
    Batch de un plato preparado que se usará en múltiples días
    
    Ejemplo: Preparas 1 paella grande el lunes, usas 50% ese día,
    30% el martes, 20% el miércoles.
    
    percentage_remaining: Cuánto queda disponible del batch (0-100%)
    """
    __tablename__ = 'dish_batches'
    
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    preparation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    percentage_remaining = db.Column(db.Float, nullable=False, default=100.0)
    ingredients_deducted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    dish = db.relationship('Dish', backref='batches')
    meal_dishes = db.relationship('MealDish', backref='batch', cascade='all, delete-orphan')
    
    __table_args__ = (
        CheckConstraint('percentage_remaining >= 0 AND percentage_remaining <= 100', 
                       name='check_percentage_valid'),
    )
    
    @property
    def is_available(self):
        """True si todavía queda algo del batch"""
        return self.percentage_remaining > 0
    
    @property
    def display_info(self):
        """Información para mostrar en UI"""
        date_str = self.preparation_date.strftime('%d/%m/%Y')
        return f'{self.dish.name} - {date_str} ({self.percentage_remaining:.0f}% disponible)'
    
    def __repr__(self):
        return f'<DishBatch {self.dish.name} {self.percentage_remaining}% restante>'


class Meal(db.Model):
    """
    Comida específica: desayuno, almuerzo o cena
    
    Puede ser:
    - Uno o varios platos (relación a través de MealDish)
    - "Pedir comida" (special_type = 'order')
    - "Comer fuera" (special_type = 'eat_out')
    
    NUEVA FILOSOFÍA: confirmed indica si la comida se ejecutó realmente
    """
    __tablename__ = 'meals'
    
    MEAL_TYPES = ['breakfast', 'lunch', 'dinner']
    SPECIAL_TYPES = ['order', 'eat_out']  # Pedir comida, Comer fuera
    
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey('days.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner
    special_type = db.Column(db.String(20), nullable=True)  # order, eat_out
    confirmed = db.Column(db.Boolean, default=False, nullable=False)  # ¿Se ejecutó realmente?
    confirmed_at = db.Column(db.DateTime, nullable=True)  # Fecha de confirmación
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    meal_dishes = db.relationship('MealDish', backref='meal', cascade='all, delete-orphan', 
                                  order_by='MealDish.order')
    
    __table_args__ = (
        db.UniqueConstraint('day_id', 'meal_type', name='unique_day_meal'),
    )
    
    def __repr__(self):
        dishes_count = len(self.meal_dishes)
        if dishes_count > 0:
            return f'<Meal {self.meal_type} on {self.day.date}: {dishes_count} platos>'
        elif self.special_type:
            return f'<Meal {self.meal_type} on {self.day.date}: {self.special_type}>'
        return f'<Meal {self.meal_type} on {self.day.date}: not assigned>'
    
    @property
    def is_special(self):
        """Retorna True si es comida especial (no consume ingredientes)"""
        return self.special_type in self.SPECIAL_TYPES
    
    @property
    def display_name(self):
        """Nombre legible para mostrar en interfaz"""
        if len(self.meal_dishes) > 0:
            dish_names = ', '.join([f"{md.dish.name} ({md.percentage}%)" 
                                   for md in self.meal_dishes])
            return dish_names
        elif self.special_type == 'order':
            return 'Pedir comida'
        elif self.special_type == 'eat_out':
            return 'Comer fuera'
        return 'Sin asignar'


class MealDish(db.Model):
    """
    Relación N:M entre Meal y Dish
    
    DOBLE FUNCIONALIDAD:
    1. Porciones múltiples: portions=5, batch_id=None -> Hacer 5 veces el plato
    2. Uso de batch: portions=1, batch_id=X, percentage=50 -> Usar 50% de un batch existente
    
    Regla: Si batch_id es NULL, usa portions. Si batch_id existe, usa percentage.
    """
    __tablename__ = 'meal_dishes'
    
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    
    # Modo 1: Porciones múltiples (sin batch)
    portions = db.Column(db.Integer, nullable=False, default=1)  # Número de porciones
    
    # Modo 2: Uso de batch (con porcentaje)
    batch_id = db.Column(db.Integer, db.ForeignKey('dish_batches.id'), nullable=True)
    percentage = db.Column(db.Float, nullable=True)  # Porcentaje del batch usado
    
    order = db.Column(db.Integer, nullable=False, default=0)  # Orden de presentación
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    dish = db.relationship('Dish', backref='meal_dishes')
    
    __table_args__ = (
        CheckConstraint('portions > 0', name='check_portions_positive'),
        CheckConstraint('percentage IS NULL OR (percentage > 0 AND percentage <= 100)', 
                       name='check_percentage_valid_range'),
    )
    
    @property
    def is_batch_mode(self):
        """True si usa batch con porcentaje"""
        return self.batch_id is not None
    
    @property
    def display_name(self):
        """Nombre para mostrar en UI"""
        if self.is_batch_mode:
            return f'{self.dish.name} ({self.percentage:.0f}% de batch)'
        elif self.portions == 1:
            return self.dish.name
        else:
            return f'{self.dish.name} x{self.portions}'
    
    def __repr__(self):
        if self.is_batch_mode:
            return f'<MealDish {self.dish.name} {self.percentage}% batch>'
        return f'<MealDish {self.dish.name} x{self.portions}>'


class ShoppingList(db.Model):
    """
    Lista de compra generada para un período
    """
    __tablename__ = 'shopping_lists'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    
    # Relaciones
    items = db.relationship('ShoppingItem', backref='shopping_list', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ShoppingList {self.name}>'
    
    @property
    def total_items(self):
        """Total de items en la lista"""
        return len(self.items)


class ShoppingItem(db.Model):
    """
    Item individual en una lista de compra
    """
    __tablename__ = 'shopping_items'
    
    id = db.Column(db.Integer, primary_key=True)
    shopping_list_id = db.Column(db.Integer, db.ForeignKey('shopping_lists.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    quantity_needed = db.Column(db.Float, nullable=False)
    quantity_available = db.Column(db.Float, nullable=False, default=0.0)
    quantity_to_buy = db.Column(db.Float, nullable=False)
    purchased = db.Column(db.Boolean, default=False)
    
    # Relación
    ingredient = db.relationship('Ingredient')
    
    __table_args__ = (
        CheckConstraint('quantity_needed > 0', name='check_quantity_needed_positive'),
        CheckConstraint('quantity_to_buy >= 0', name='check_quantity_to_buy_positive'),
    )
    
    def __repr__(self):
        return f'<ShoppingItem {self.ingredient.name}: {self.quantity_to_buy} {self.ingredient.unit}>'
