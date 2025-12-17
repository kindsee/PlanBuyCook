"""
Servicios de lógica de negocio para PlanBuyCook (FILOSOFÍA SIMPLIFICADA)

NUEVA FILOSOFÍA:
1. Doble contador de stock:
   - stock_actual: Lo que realmente tienes físicamente
   - stock_planificado: actual - lo planificado (puede ser negativo = hay que comprar)

2. Al asignar platos:
   - Se descuenta de stock_planificado
   - NO se toca stock_actual
   - Puede quedar negativo (indica que hay que comprar)

3. Al confirmar comida (botón ✓):
   - Se descuenta de stock_actual
   - Se ajusta stock_planificado si es necesario

4. Porciones simples:
   - "Tortilla x5" en lugar de porcentajes complejos
   - Más intuitivo y fácil de usar

Contiene servicios para:
- Gestión de stock del almacén (doble contador)
- Asignación de platos con porciones
- Confirmación de comidas ejecutadas
- Generación de listas de compra
"""
from datetime import datetime, timedelta
from sqlalchemy import and_, func
from models import db, Ingredient, PantryStock, Dish, DishIngredient, Day, Meal, MealDish, ShoppingList, ShoppingItem


class StockError(Exception):
    """Excepción personalizada para errores de stock"""
    pass


class PantryService:
    """Servicio para gestión del almacén con doble contador"""
    
    @staticmethod
    def get_stock(ingredient_id):
        """
        Obtiene los stocks de un ingrediente
        
        Returns:
            dict: {'actual': float, 'planificado': float} o None si no existe
        """
        stock = PantryStock.query.filter_by(ingredient_id=ingredient_id).first()
        if stock:
            return {
                'actual': stock.stock_actual,
                'planificado': stock.stock_planificado
            }
        return {'actual': 0.0, 'planificado': 0.0}
    
    @staticmethod
    def update_stock_actual(ingredient_id, quantity, operation='set', auto_commit=True):
        """
        Actualiza el stock ACTUAL (físico) de un ingrediente
        También actualiza stock_planificado en la misma cantidad
        
        Args:
            ingredient_id: ID del ingrediente
            quantity: Cantidad a modificar
            operation: 'set' (establecer), 'add' (añadir), 'subtract' (restar)
            auto_commit: Si True, hace commit automáticamente
        """
        stock = PantryStock.query.filter_by(ingredient_id=ingredient_id).first()
        
        if not stock:
            stock = PantryStock(ingredient_id=ingredient_id, stock_actual=0.0, stock_planificado=0.0)
            db.session.add(stock)
            if auto_commit:
                db.session.flush()
        
        old_actual = stock.stock_actual
        
        if operation == 'set':
            stock.stock_actual = quantity
            # Ajustar planificado manteniendo la diferencia
            diff = stock.stock_actual - old_actual
            stock.stock_planificado += diff
        elif operation == 'add':
            stock.stock_actual += quantity
            stock.stock_planificado += quantity
        elif operation == 'subtract':
            if stock.stock_actual < quantity:
                ingredient = Ingredient.query.get(ingredient_id)
                raise StockError(
                    f"Stock insuficiente de {ingredient.name}. "
                    f"Disponible: {stock.stock_actual} {ingredient.unit}, "
                    f"Intentas restar: {quantity} {ingredient.unit}"
                )
            stock.stock_actual -= quantity
            stock.stock_planificado -= quantity
        
        if auto_commit:
            db.session.commit()
        
        return stock
    
    @staticmethod
    def update_stock_planificado(ingredient_id, quantity, operation='subtract', auto_commit=True):
        """
        Actualiza SOLO el stock planificado (para planificación de comidas)
        PUEDE quedar negativo (indica que hay que comprar)
        
        Args:
            ingredient_id: ID del ingrediente
            quantity: Cantidad a modificar
            operation: 'add' (devolver) o 'subtract' (descontar)
            auto_commit: Si True, hace commit automáticamente
        """
        stock = PantryStock.query.filter_by(ingredient_id=ingredient_id).first()
        
        if not stock:
            stock = PantryStock(ingredient_id=ingredient_id, stock_actual=0.0, stock_planificado=0.0)
            db.session.add(stock)
            if auto_commit:
                db.session.flush()
        
        if operation == 'add':
            stock.stock_planificado += quantity
        elif operation == 'subtract':
            stock.stock_planificado -= quantity  # PUEDE quedar negativo
        
        if auto_commit:
            db.session.commit()
        
        return stock


class MealService:
    """Servicio para gestión de comidas con porciones simples"""
    
    @staticmethod
    def add_dish_to_meal(day_id, meal_type, dish_id, portions=1):
        """
        Añade un plato a una comida con número de porciones
        Descuenta del stock_planificado (puede quedar negativo)
        
        Args:
            day_id: ID del día
            meal_type: Tipo de comida (breakfast, lunch, dinner)
            dish_id: ID del plato
            portions: Número de porciones (1, 2, 3, 4, 5...)
        
        Returns:
            MealDish: Relación creada
        """
        try:
            if portions < 1:
                raise ValueError("El número de porciones debe ser al menos 1")
            
            day = Day.query.get_or_404(day_id)
            dish = Dish.query.get_or_404(dish_id)
            
            # Buscar o crear la comida
            meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
            if not meal:
                meal = Meal(day_id=day_id, meal_type=meal_type, special_type=None)
                db.session.add(meal)
                db.session.flush()
            
            # Limpiar special_type si existía
            if meal.special_type:
                meal.special_type = None
            
            # Descontar del stock PLANIFICADO (puede quedar negativo)
            for di in dish.ingredients:
                quantity_needed = di.quantity * portions
                PantryService.update_stock_planificado(
                    di.ingredient_id, 
                    quantity_needed, 
                    operation='subtract',
                    auto_commit=False
                )
            
            # Obtener el siguiente orden
            max_order = db.session.query(func.max(MealDish.order)).filter_by(meal_id=meal.id).scalar() or -1
            
            # Crear MealDish
            meal_dish = MealDish(
                meal_id=meal.id,
                dish_id=dish_id,
                portions=portions,
                order=max_order + 1
            )
            db.session.add(meal_dish)
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
        Elimina un plato de una comida y DEVUELVE al stock planificado
        
        Args:
            meal_dish_id: ID de la relación MealDish
        """
        try:
            meal_dish = MealDish.query.get_or_404(meal_dish_id)
            dish = meal_dish.dish
            portions = meal_dish.portions
            
            # Devolver al stock PLANIFICADO
            for di in dish.ingredients:
                quantity = di.quantity * portions
                PantryService.update_stock_planificado(
                    di.ingredient_id,
                    quantity,
                    operation='add',
                    auto_commit=False
                )
            
            db.session.delete(meal_dish)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al eliminar plato de comida: {str(e)}")
    
    @staticmethod
    def confirm_meal(meal_id):
        """
        Confirma que una comida se ejecutó realmente
        Descuenta del stock ACTUAL los ingredientes
        
        Args:
            meal_id: ID de la comida
        
        Returns:
            Meal: Comida confirmada
        """
        try:
            meal = Meal.query.get_or_404(meal_id)
            
            if meal.confirmed:
                raise ValueError("Esta comida ya está confirmada")
            
            if meal.is_special:
                # Comidas especiales no consumen ingredientes
                meal.confirmed = True
                meal.confirmed_at = datetime.utcnow()
                db.session.commit()
                return meal
            
            # Descontar del stock ACTUAL
            for meal_dish in meal.meal_dishes:
                dish = meal_dish.dish
                portions = meal_dish.portions
                
                for di in dish.ingredients:
                    quantity = di.quantity * portions
                    try:
                        PantryService.update_stock_actual(
                            di.ingredient_id,
                            quantity,
                            operation='subtract',
                            auto_commit=False
                        )
                    except StockError as e:
                        # Si no hay stock actual suficiente, aún así permitir confirmar
                        # (ya cocinaste, aunque no tenías stock registrado)
                        ingredient = Ingredient.query.get(di.ingredient_id)
                        print(f"⚠️  Advertencia: {e}. Se permite confirmar de todas formas.")
                        # Forzar stock actual a 0
                        stock = PantryStock.query.filter_by(ingredient_id=di.ingredient_id).first()
                        stock.stock_actual = 0
            
            # Marcar como confirmada
            meal.confirmed = True
            meal.confirmed_at = datetime.utcnow()
            
            db.session.commit()
            return meal
            
        except ValueError as e:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al confirmar comida: {str(e)}")
    
    @staticmethod
    def unconfirm_meal(meal_id):
        """
        Des-confirma una comida (deshace la confirmación)
        DEVUELVE al stock actual los ingredientes
        
        Args:
            meal_id: ID de la comida
        """
        try:
            meal = Meal.query.get_or_404(meal_id)
            
            if not meal.confirmed:
                raise ValueError("Esta comida no está confirmada")
            
            if not meal.is_special:
                # Devolver al stock ACTUAL
                for meal_dish in meal.meal_dishes:
                    dish = meal_dish.dish
                    portions = meal_dish.portions
                    
                    for di in dish.ingredients:
                        quantity = di.quantity * portions
                        PantryService.update_stock_actual(
                            di.ingredient_id,
                            quantity,
                            operation='add',
                            auto_commit=False
                        )
            
            # Desmarcar confirmación
            meal.confirmed = False
            meal.confirmed_at = None
            
            db.session.commit()
            
        except ValueError as e:
            db.session.rollback()
            raise
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al desconfirmar comida: {str(e)}")
    
    @staticmethod
    def assign_special_to_meal(day_id, meal_type, special_type):
        """
        Asigna una opción especial a una comida (pedir comida, comer fuera)
        Elimina todos los platos y DEVUELVE stock planificado
        
        Args:
            day_id: ID del día
            meal_type: Tipo de comida
            special_type: 'order' o 'eat_out'
        """
        try:
            day = Day.query.get_or_404(day_id)
            
            meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
            
            if meal:
                # Devolver stock de todos los platos
                for meal_dish in meal.meal_dishes:
                    dish = meal_dish.dish
                    portions = meal_dish.portions
                    
                    for di in dish.ingredients:
                        quantity = di.quantity * portions
                        PantryService.update_stock_planificado(
                            di.ingredient_id,
                            quantity,
                            operation='add',
                            auto_commit=False
                        )
                    
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
        """Elimina una comida y devuelve stock planificado"""
        try:
            meal = Meal.query.filter_by(day_id=day_id, meal_type=meal_type).first()
            
            if meal:
                # Devolver stock de todos los platos
                for meal_dish in meal.meal_dishes:
                    dish = meal_dish.dish
                    portions = meal_dish.portions
                    
                    for di in dish.ingredients:
                        quantity = di.quantity * portions
                        PantryService.update_stock_planificado(
                            di.ingredient_id,
                            quantity,
                            operation='add',
                            auto_commit=False
                        )
                
                db.session.delete(meal)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Error al eliminar comida: {str(e)}")


class ShoppingListService:
    """Servicio para generación de listas de compra"""
    
    @staticmethod
    def generate_shopping_list_from_stock(name=None):
        """
        Genera lista de compra basándose en ingredientes con stock_planificado NEGATIVO
        (stock negativo = hay que comprar)
        
        Args:
            name: Nombre personalizado para la lista
            
        Returns:
            ShoppingList: Lista de compra generada
        """
        # Obtener todos los stocks con planificado negativo
        negative_stocks = PantryStock.query.filter(PantryStock.stock_planificado < 0).all()
        
        if not negative_stocks:
            raise ValueError("No hay ingredientes que comprar. Stock planificado suficiente.")
        
        # Crear lista
        if name is None:
            name = f"Lista de Compra - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        shopping_list = ShoppingList(
            name=name,
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=7),
            completed=False
        )
        db.session.add(shopping_list)
        db.session.flush()
        
        # Crear items
        for stock in negative_stocks:
            quantity_to_buy = abs(stock.stock_planificado)  # Convertir negativo a positivo
            
            item = ShoppingItem(
                shopping_list_id=shopping_list.id,
                ingredient_id=stock.ingredient_id,
                quantity_needed=quantity_to_buy,  # Lo que falta
                quantity_available=stock.stock_actual,  # Lo que tienes
                quantity_to_buy=quantity_to_buy,
                purchased=False
            )
            db.session.add(item)
        
        db.session.commit()
        return shopping_list
    
    @staticmethod
    def complete_shopping_list(shopping_list_id):
        """
        Marca lista como completada y añade ingredientes al stock ACTUAL y PLANIFICADO
        
        Args:
            shopping_list_id: ID de la lista
        """
        shopping_list = ShoppingList.query.get_or_404(shopping_list_id)
        
        for item in shopping_list.items:
            if not item.purchased:
                # Añadir al stock actual Y planificado
                PantryService.update_stock_actual(
                    item.ingredient_id,
                    item.quantity_to_buy,
                    operation='add',
                    auto_commit=False
                )
                item.purchased = True
        
        shopping_list.completed = True
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
