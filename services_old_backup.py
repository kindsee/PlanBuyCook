"""
Servicios de lógica de negocio para PlanBuyCook

Contiene funciones para:
- Gestión de stock del almacén
- Cálculo de ingredientes necesarios
- Generación de listas de compra
- Descuento automático de ingredientes
- Gestión de batches de platos con porcentajes
"""
from datetime import datetime, timedelta
from sqlalchemy import and_
from models import db, Ingredient, PantryStock, Dish, DishIngredient, Day, Meal, MealDish, DishBatch, ShoppingList, ShoppingItem


class StockError(Exception):
    """Excepción personalizada para errores de stock"""
    pass


class PantryService:
    """Servicio para gestión del almacén"""
    
    @staticmethod
    def get_stock(ingredient_id):
        """Obtiene el stock actual de un ingrediente"""
        stock = PantryStock.query.filter_by(ingredient_id=ingredient_id).first()
        return stock.quantity if stock else 0.0
    
    @staticmethod
    def update_stock(ingredient_id, quantity, operation='set'):
        """
        Actualiza el stock de un ingrediente
        
        Args:
            ingredient_id: ID del ingrediente
            quantity: Cantidad a modificar
            operation: 'set' (establecer), 'add' (añadir), 'subtract' (restar)
        """
        stock = PantryStock.query.filter_by(ingredient_id=ingredient_id).first()
        
        if not stock:
            # Crear entrada si no existe
            stock = PantryStock(ingredient_id=ingredient_id, quantity=0.0)
            db.session.add(stock)
        
        if operation == 'set':
            stock.quantity = quantity
        elif operation == 'add':
            stock.quantity += quantity
        elif operation == 'subtract':
            new_quantity = stock.quantity - quantity
            if new_quantity < 0:
                ingredient = Ingredient.query.get(ingredient_id)
                raise StockError(
                    f"Stock insuficiente de {ingredient.name}. "
                    f"Disponible: {stock.quantity} {ingredient.unit}, "
                    f"Necesario: {quantity} {ingredient.unit}"
                )
            stock.quantity = new_quantity
        
        db.session.commit()
        return stock
    
    @staticmethod
    def check_sufficient_stock(ingredient_quantities):
        """
        Verifica si hay stock suficiente para una lista de ingredientes
        
        Args:
            ingredient_quantities: dict {ingredient_id: quantity_needed}
            
        Returns:
            tuple (bool, list): (tiene_stock_suficiente, lista_de_faltantes)
        """
        insufficient = []
        
        for ingredient_id, quantity_needed in ingredient_quantities.items():
            available = PantryService.get_stock(ingredient_id)
            if available < quantity_needed:
                ingredient = Ingredient.query.get(ingredient_id)
                insufficient.append({
                    'ingredient': ingredient,
                    'needed': quantity_needed,
                    'available': available,
                    'missing': quantity_needed - available
                })
        
        return len(insufficient) == 0, insufficient


class MealService:
    """Servicio para gestión de comidas"""
    
    @staticmethod
    def assign_dish_to_meal(day_id, meal_type, dish_id):
        """
        Asigna un plato a una comida y descuenta ingredientes
        
        Args:
            day_id: ID del día
            meal_type: Tipo de comida (breakfast, lunch, dinner)
            dish_id: ID del plato
        """
        day = Day.query.get_or_404(day_id)
        dish = Dish.query.get_or_404(dish_id)
        
        # Verificar stock suficiente
        ingredient_quantities = {
            di.ingredient_id: di.quantity 
            for di in dish.ingredients
        }
        
        has_stock, insufficient = PantryService.check_sufficient_stock(ingredient_quantities)
        
        if not has_stock:
            error_msg = "Stock insuficiente:\n"
            for item in insufficient:
                error_msg += (
                    f"- {item['ingredient'].name}: "
                    f"faltan {item['missing']} {item['ingredient'].unit}\n"
                )
            raise StockError(error_msg)
        
        # Buscar o crear la comida
        meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
        
        if meal:
            # Si ya existe, devolver ingredientes previos si tenía un plato
            if meal.dish_id and meal.ingredients_deducted:
                MealService._return_ingredients(meal.dish_id)
            
            meal.dish_id = dish_id
            meal.special_type = None
        else:
            meal = Meal(
                day_id=day_id,
                meal_type=meal_type,
                dish_id=dish_id,
                special_type=None
            )
            db.session.add(meal)
        
        # Descontar ingredientes
        for ingredient_id, quantity in ingredient_quantities.items():
            PantryService.update_stock(ingredient_id, quantity, operation='subtract')
        
        meal.ingredients_deducted = True
        db.session.commit()
        
        return meal
    
    @staticmethod
    def assign_special_to_meal(day_id, meal_type, special_type):
        """
        Asigna una opción especial a una comida (pedir comida, comer fuera)
        
        Args:
            day_id: ID del día
            meal_type: Tipo de comida
            special_type: 'order' o 'eat_out'
        """
        day = Day.query.get_or_404(day_id)
        
        # Buscar o crear la comida
        meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
        
        if meal:
            # Si tenía un plato, devolver ingredientes
            if meal.dish_id and meal.ingredients_deducted:
                MealService._return_ingredients(meal.dish_id)
            
            meal.dish_id = None
            meal.special_type = special_type
            meal.ingredients_deducted = False
        else:
            meal = Meal(
                day_id=day_id,
                meal_type=meal_type,
                dish_id=None,
                special_type=special_type,
                ingredients_deducted=False
            )
            db.session.add(meal)
        
        db.session.commit()
        return meal
    
    @staticmethod
    def remove_meal(day_id, meal_type):
        """Elimina una comida y devuelve ingredientes al almacén"""
        meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
        
        if meal:
            if meal.dish_id and meal.ingredients_deducted:
                MealService._return_ingredients(meal.dish_id)
            
            db.session.delete(meal)
            db.session.commit()
    
    @staticmethod
    def _return_ingredients(dish_id):
        """Devuelve ingredientes al almacén cuando se elimina un plato"""
        dish = Dish.query.get(dish_id)
        if dish:
            for di in dish.ingredients:
                PantryService.update_stock(
                    di.ingredient_id,
                    di.quantity,
                    operation='add'
                )


class ShoppingListService:
    """Servicio para generación de listas de compra"""
    
    @staticmethod
    def calculate_ingredients_needed(start_date, end_date):
        """
        Calcula ingredientes totales necesarios para un período
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            dict: {ingredient_id: quantity_needed}
        """
        # Obtener todas las comidas del período que tienen plato asignado
        days = Day.query.filter(
            and_(Day.date >= start_date, Day.date <= end_date)
        ).all()
        
        ingredients_needed = {}
        
        for day in days:
            for meal in day.meals:
                # Solo contar comidas con plato (no las especiales)
                if meal.dish_id:
                    dish = meal.dish
                    for di in dish.ingredients:
                        if di.ingredient_id in ingredients_needed:
                            ingredients_needed[di.ingredient_id] += di.quantity
                        else:
                            ingredients_needed[di.ingredient_id] = di.quantity
        
        return ingredients_needed
    
    @staticmethod
    def generate_shopping_list(start_date, weeks=1, name=None):
        """
        Genera una lista de compra para un período
        
        Args:
            start_date: Fecha de inicio
            weeks: Número de semanas a planificar
            name: Nombre personalizado para la lista
            
        Returns:
            ShoppingList: Lista de compra generada
        """
        end_date = start_date + timedelta(weeks=weeks)
        
        if not name:
            name = f"Compra {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        # Calcular ingredientes necesarios
        ingredients_needed = ShoppingListService.calculate_ingredients_needed(
            start_date, end_date
        )
        
        # Crear lista de compra
        shopping_list = ShoppingList(
            name=name,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(shopping_list)
        db.session.flush()  # Para obtener el ID
        
        # Crear items
        for ingredient_id, quantity_needed in ingredients_needed.items():
            quantity_available = PantryService.get_stock(ingredient_id)
            quantity_to_buy = max(0, quantity_needed - quantity_available)
            
            if quantity_to_buy > 0:  # Solo añadir si hay que comprar
                item = ShoppingItem(
                    shopping_list_id=shopping_list.id,
                    ingredient_id=ingredient_id,
                    quantity_needed=quantity_needed,
                    quantity_available=quantity_available,
                    quantity_to_buy=quantity_to_buy
                )
                db.session.add(item)
        
        db.session.commit()
        return shopping_list
    
    @staticmethod
    def mark_list_completed(shopping_list_id):
        """
        Marca una lista como completada y añade items al almacén
        
        Args:
            shopping_list_id: ID de la lista de compra
        """
        shopping_list = ShoppingList.query.get_or_404(shopping_list_id)
        
        # Añadir items comprados al almacén
        for item in shopping_list.items:
            if not item.purchased:
                PantryService.update_stock(
                    item.ingredient_id,
                    item.quantity_to_buy,
                    operation='add'
                )
                item.purchased = True
        
        shopping_list.completed = True
        db.session.commit()
        
        return shopping_list


class CalendarService:
    """Servicio para gestión del calendario"""
    
    @staticmethod
    def get_or_create_day(date):
        """Obtiene o crea un día en el calendario"""
        day = Day.query.filter_by(date=date).first()
        if not day:
            day = Day(date=date)
            db.session.add(day)
            db.session.commit()
        return day
    
    @staticmethod
    def get_week_days(start_date):
        """Obtiene o crea los días de una semana"""
        days = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day = CalendarService.get_or_create_day(current_date)
            days.append(day)
        return days
