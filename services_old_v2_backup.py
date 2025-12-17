"""
Servicios de lógica de negocio para PlanBuyCook (NUEVA FILOSOFÍA)

FILOSOFÍA DE PLANIFICACIÓN:
- Los platos se PLANIFICAN libremente sin verificar stock (batches virtuales)
- Los ingredientes NO se descuentan al asignar platos
- La lista de compra calcula: ingredientes_necesarios - stock_disponible
- (Futuro) Los ingredientes se marcarán como consumidos cuando se cocine realmente

Contiene funciones para:
- Gestión de stock del almacén
- Cálculo de ingredientes necesarios
- Generación de listas de compra
- Gestión de batches virtuales de platos con porcentajes
"""

from datetime import datetime, timedelta
from sqlalchemy import and_, func
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
    def update_stock(ingredient_id, quantity, operation='set', auto_commit=True):
        """
        Actualiza el stock de un ingrediente
        
        Args:
            ingredient_id: ID del ingrediente
            quantity: Cantidad a modificar
            operation: 'set' (establecer), 'add' (añadir), 'subtract' (restar)
            auto_commit: Si True, hace commit automáticamente. Si False, el llamador debe hacer commit
        """
        stock = PantryStock.query.filter_by(ingredient_id=ingredient_id).first()
        
        if not stock:
            # Crear entrada si no existe
            stock = PantryStock(ingredient_id=ingredient_id, quantity=0.0)
            db.session.add(stock)
            if auto_commit:
                db.session.flush()
        
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
        
        if auto_commit:
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
                    'available': available,
                    'needed': quantity_needed,
                    'missing': quantity_needed - available
                })
        
        return (len(insufficient) == 0, insufficient)


class MealService:
    """Servicio para asignación de platos a comidas con sistema de batches"""
    
    @staticmethod
    def add_dish_to_meal(day_id, meal_type, dish_id, percentage=100):
        """
        Añade un plato a una comida con porcentaje específico.
        Busca o crea un batch virtual del plato (NO descuenta ingredientes).
        
        NUEVA FILOSOFÍA: La planificación se hace sin verificar stock.
        Los ingredientes se calculan al generar la lista de compra.
        
        Args:
            day_id: ID del día
            meal_type: Tipo de comida (breakfast, lunch, dinner)
            dish_id: ID del plato
            percentage: Porcentaje del plato a usar (5, 10, 25, 50, 100)
        
        Returns:
            MealDish: Relación creada
        """
        try:
            if percentage not in MealDish.VALID_PERCENTAGES:
                raise ValueError(f"Porcentaje inválido. Debe ser uno de: {MealDish.VALID_PERCENTAGES}")
            
            day = Day.query.get_or_404(day_id)
            dish = Dish.query.get_or_404(dish_id)
            
            # Buscar o crear la comida
            meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
            if not meal:
                meal = Meal(day_id=day_id, meal_type=meal_type, special_type=None)
                db.session.add(meal)
                db.session.flush()  # Para obtener el ID
            
            # Limpiar special_type si existía
            if meal.special_type:
                meal.special_type = None
            
            # Buscar un batch virtual existente con porcentaje disponible suficiente
            batch = DishBatch.query.filter(
                DishBatch.dish_id == dish_id,
                DishBatch.percentage_remaining >= percentage
            ).order_by(DishBatch.preparation_date).first()
            
            if not batch:
                # Crear nuevo batch virtual (sin descontar ingredientes)
                batch = DishBatch(
                    dish_id=dish_id,
                    preparation_date=datetime.utcnow(),
                    percentage_remaining=100.0,
                    ingredients_deducted=False  # Los ingredientes NO se descuentan al planificar
                )
                db.session.add(batch)
                db.session.flush()
            
            # Restar porcentaje del batch virtual
            batch.percentage_remaining -= percentage
            
            # Obtener el siguiente orden
            max_order = db.session.query(func.max(MealDish.order)).filter_by(meal_id=meal.id).scalar() or -1
            
            # Crear MealDish
            meal_dish = MealDish(
                meal_id=meal.id,
                dish_id=dish_id,
                batch_id=batch.id,
                percentage=percentage,
                order=max_order + 1
            )
            db.session.add(meal_dish)
            
            # Commit único de toda la transacción
            db.session.commit()
            
            return meal_dish
            
        except ValueError as e:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al añadir plato a comida: {str(e)}")
    
    @staticmethod
    def remove_dish_from_meal(meal_dish_id):
        """
        Elimina un plato de una comida y devuelve el porcentaje al batch.
        
        NUEVA FILOSOFÍA: No se devuelven ingredientes al almacén porque
        nunca fueron descontados (los batches son virtuales).
        
        Args:
            meal_dish_id: ID de la relación MealDish
        """
        try:
            meal_dish = MealDish.query.get_or_404(meal_dish_id)
            
            # Obtener el batch
            batch = DishBatch.query.get(meal_dish.batch_id)
            
            if batch:
                # Devolver porcentaje al batch virtual, sin exceder 100%
                new_percentage = batch.percentage_remaining + meal_dish.percentage
                batch.percentage_remaining = min(new_percentage, 100.0)
            
            db.session.delete(meal_dish)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al eliminar plato de comida: {str(e)}")
    
    @staticmethod
    def assign_special_to_meal(day_id, meal_type, special_type):
        """
        Asigna una opción especial a una comida (pedir comida, comer fuera)
        Elimina todos los platos asignados a la comida y devuelve porcentajes a batches
        
        Args:
            day_id: ID del día
            meal_type: Tipo de comida
            special_type: 'order' o 'eat_out'
        """
        try:
            day = Day.query.get_or_404(day_id)
            
            # Buscar o crear la comida
            meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
            
            if meal:
                # Devolver porcentajes de todos los platos al batch
                for meal_dish in meal.meal_dishes:
                    batch = DishBatch.query.get(meal_dish.batch_id)
                    if batch:
                        # Devolver porcentaje sin exceder 100%
                        new_percentage = batch.percentage_remaining + meal_dish.percentage
                        batch.percentage_remaining = min(new_percentage, 100.0)
                    db.session.delete(meal_dish)
                
                meal.special_type = special_type
            else:
                meal = Meal(
                    day_id=day_id,
                    meal_type=meal_type,
                    special_type=special_type
                )
                db.session.add(meal)
            
            db.session.commit()
            return meal
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al asignar comida especial: {str(e)}")
    
    @staticmethod
    def remove_meal(day_id, meal_type):
        """Elimina una comida y devuelve porcentajes de platos a batches"""
        try:
            meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
            
            if meal:
                # Devolver porcentajes al batch
                for meal_dish in meal.meal_dishes:
                    batch = DishBatch.query.get(meal_dish.batch_id)
                    if batch:
                        # Devolver porcentaje sin exceder 100%
                        new_percentage = batch.percentage_remaining + meal_dish.percentage
                        batch.percentage_remaining = min(new_percentage, 100.0)
                
                db.session.delete(meal)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al eliminar comida: {str(e)}")
    
    @staticmethod
    def cleanup_empty_batches():
        """
        Elimina batches completamente usados (0% restante) de hace más de 7 días
        Limpieza de mantenimiento
        """
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        DishBatch.query.filter(
            DishBatch.percentage_remaining == 0,
            DishBatch.preparation_date < cutoff_date
        ).delete()
        db.session.commit()


class ShoppingListService:
    """Servicio para generación de listas de compra"""
    
    @staticmethod
    def calculate_ingredients_needed(start_date, end_date):
        """
        Calcula ingredientes totales necesarios para un período.
        Considera todos los platos planificados a través de MealDish.
        
        NUEVA FILOSOFÍA: Calcula lo necesario para preparar todas las comidas planificadas,
        independientemente del stock actual. La lista de compra mostrará qué falta comprar.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            dict: {ingredient_id: quantity_needed}
        """
        # Obtener todas las comidas del período
        days = Day.query.filter(
            and_(Day.date >= start_date, Day.date <= end_date)
        ).all()
        
        ingredients_needed = {}
        
        for day in days:
            for meal in day.meals:
                # Solo contar comidas que NO sean especiales (order, eat_out)
                if not meal.is_special:
                    for meal_dish in meal.meal_dishes:
                        dish = meal_dish.dish
                        percentage_factor = meal_dish.percentage / 100.0
                        
                        # Sumar ingredientes necesarios según el porcentaje usado
                        for di in dish.ingredients:
                            quantity = di.quantity * percentage_factor
                            if di.ingredient_id in ingredients_needed:
                                ingredients_needed[di.ingredient_id] += quantity
                            else:
                                ingredients_needed[di.ingredient_id] = quantity
        
        return ingredients_needed
    
    @staticmethod
    def generate_shopping_list(start_date, weeks=1, name=None):
        """
        Genera una lista de compra para el período especificado
        
        Args:
            start_date: Fecha de inicio
            weeks: Número de semanas a planificar
            name: Nombre personalizado para la lista
            
        Returns:
            ShoppingList: Lista de compra generada
        """
        end_date = start_date + timedelta(weeks=weeks)
        
        # Calcular ingredientes necesarios
        ingredients_needed = ShoppingListService.calculate_ingredients_needed(start_date, end_date)
        
        # Crear lista de compra
        if name is None:
            name = f"Lista {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
        
        shopping_list = ShoppingList(
            name=name,
            start_date=start_date,
            end_date=end_date,
            status='pending'
        )
        db.session.add(shopping_list)
        db.session.flush()  # Para obtener el ID
        
        # Crear items de la lista
        for ingredient_id, quantity_needed in ingredients_needed.items():
            quantity_available = PantryService.get_stock(ingredient_id)
            quantity_to_buy = max(0, quantity_needed - quantity_available)
            
            # Solo añadir si hay que comprar
            if quantity_to_buy > 0:
                item = ShoppingItem(
                    shopping_list_id=shopping_list.id,
                    ingredient_id=ingredient_id,
                    quantity_needed=quantity_needed,
                    quantity_available=quantity_available,
                    quantity_to_buy=quantity_to_buy,
                    purchased=False
                )
                db.session.add(item)
        
        db.session.commit()
        return shopping_list
    
    @staticmethod
    def complete_shopping_list(shopping_list_id):
        """
        Marca una lista como completada y añade los ingredientes al almacén
        
        Args:
            shopping_list_id: ID de la lista de compra
        """
        shopping_list = ShoppingList.query.get_or_404(shopping_list_id)
        
        for item in shopping_list.items:
            if not item.purchased:
                # Añadir al almacén
                PantryService.update_stock(
                    item.ingredient_id,
                    item.quantity_to_buy,
                    operation='add'
                )
                item.purchased = True
        
        shopping_list.status = 'completed'
        shopping_list.completed_at = datetime.utcnow()
        db.session.commit()


class CalendarService:
    """Servicio para gestión del calendario"""
    
    @staticmethod
    def get_or_create_day(date):
        """Obtiene o crea un día en el calendario"""
        day = Day.query.filter_by(date=date).first()
        if not day:
            day = Day(date=date)
            db.session.add(day)
            
            # Crear las 3 comidas vacías
            for meal_type in Meal.MEAL_TYPES:
                meal = Meal(day=day, meal_type=meal_type)
                db.session.add(meal)
            
            db.session.commit()
        return day
    
    @staticmethod
    def get_week_days(start_date):
        """Obtiene o crea 7 días consecutivos desde start_date"""
        days = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            day = CalendarService.get_or_create_day(current_date)
            days.append(day)
        return days
