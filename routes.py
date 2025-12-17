"""
Rutas y controladores Flask para PlanBuyCook

Define los endpoints para:
- Calendario de comidas (planificación libre)
- Gestión de platos
- Gestión de ingredientes
- Almacén
- Lista de compra
"""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Day, Meal, MealDish, Dish, Ingredient, DishIngredient, PantryStock, ShoppingList, ShoppingItem
from services import (
    PantryService, MealService, ShoppingListService, 
    CalendarService, StockError
)


main_bp = Blueprint('main', __name__)


# ==================== CALENDARIO ====================

@main_bp.route('/calendar')
def calendar():
    """Vista del calendario semanal"""
    # Obtener fecha de inicio de la semana (lunes)
    today = datetime.now().date()
    week_offset = int(request.args.get('week', 0))
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    
    # Obtener días de la semana
    days = CalendarService.get_week_days(start_of_week)
    
    # Preparar estructura de comidas
    meal_types = ['breakfast', 'lunch', 'dinner']
    meal_names = {
        'breakfast': 'Desayuno',
        'lunch': 'Almuerzo',
        'dinner': 'Cena'
    }
    
    return render_template(
        'calendar.html',
        days=days,
        meal_types=meal_types,
        meal_names=meal_names,
        week_offset=week_offset
    )


@main_bp.route('/meal/assign', methods=['POST'])
def assign_meal():
    """Añade un plato a una comida con tres modos: porciones, batch nuevo, o batch existente"""
    from models import DishBatch
    try:
        day_id = request.form.get('day_id', type=int)
        meal_type = request.form.get('meal_type')
        assignment_type = request.form.get('assignment_type')  # dish, order, eat_out
        
        if assignment_type == 'dish':
            dish_id = request.form.get('dish_id', type=int)
            dish_mode = request.form.get('dish_mode')  # portions, batch_new, batch_existing
            
            if dish_mode == 'portions':
                # Modo 1: Porciones múltiples
                portions = request.form.get('portions', type=int, default=1)
                MealService.add_dish_to_meal(day_id, meal_type, dish_id, portions, batch_id=None)
                flash(f'✓ Plato añadido correctamente (x{portions})', 'success')
                
            elif dish_mode == 'batch_new':
                # Modo 2: Crear nuevo batch
                percentage_to_use = request.form.get('batch_percentage_new', type=float)
                
                if not percentage_to_use or percentage_to_use <= 0 or percentage_to_use > 100:
                    flash('Porcentaje inválido', 'error')
                    return redirect(url_for('main.calendar'))
                
                # Crear batch
                batch = DishBatch(
                    dish_id=dish_id,
                    percentage_remaining=100.0,
                    ingredients_deducted=False
                )
                db.session.add(batch)
                db.session.flush()
                
                # Descontar ingredientes por hacer el plato completo
                MealService.deduct_batch_ingredients(batch.id)
                
                # Restar el porcentaje usado hoy
                batch.percentage_remaining -= percentage_to_use
                
                # Añadir a la comida
                MealService.add_dish_to_meal(day_id, meal_type, dish_id, 1, 
                                            batch_id=batch.id, percentage=percentage_to_use)
                
                db.session.commit()
                remaining = 100 - percentage_to_use
                flash(f'✓ Batch creado y usando {percentage_to_use:.0f}%. Queda {remaining:.0f}% para otro día', 'success')
                
            elif dish_mode == 'batch_existing':
                # Modo 3: Usar de batch existente
                batch_id = request.form.get('batch_id', type=int)
                percentage_to_use = request.form.get('batch_percentage_existing', type=float)
                
                if not batch_id or not percentage_to_use:
                    flash('Selección de batch inválida', 'error')
                    return redirect(url_for('main.calendar'))
                
                # Validar batch
                batch = DishBatch.query.get_or_404(batch_id)
                
                if percentage_to_use > batch.percentage_remaining:
                    flash(f'Solo queda {batch.percentage_remaining:.0f}% del batch', 'error')
                    return redirect(url_for('main.calendar'))
                
                # Restar porcentaje del batch
                batch.percentage_remaining -= percentage_to_use
                
                # Añadir a la comida
                MealService.add_dish_to_meal(day_id, meal_type, dish_id, 1,
                                            batch_id=batch_id, percentage=percentage_to_use)
                
                db.session.commit()
                flash(f'✓ Usando {percentage_to_use:.0f}% del batch. Queda {batch.percentage_remaining:.0f}%', 'success')
            
            else:
                flash('Modo de preparación inválido', 'error')
                
        elif assignment_type in ['order', 'eat_out']:
            MealService.assign_special_to_meal(day_id, meal_type, assignment_type)
            flash('Comida asignada correctamente', 'success')
        else:
            flash('Selección inválida', 'error')
            
    except ValueError as e:
        db.session.rollback()
        flash(str(e), 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al asignar comida: {str(e)}', 'error')
    
    return redirect(url_for('main.calendar'))


@main_bp.route('/meal/remove_dish', methods=['POST'])
def remove_dish_from_meal():
    """Elimina un plato específico de una comida"""
    try:
        meal_dish_id = request.form.get('meal_dish_id', type=int)
        
        MealService.remove_dish_from_meal(meal_dish_id)
        flash('Plato eliminado de la comida', 'success')
    except Exception as e:
        flash(f'Error al eliminar plato: {str(e)}', 'error')
    
    return redirect(url_for('main.calendar'))


@main_bp.route('/meal/remove', methods=['POST'])
def remove_meal():
    """Elimina una comida asignada"""
    try:
        day_id = request.form.get('day_id', type=int)
        meal_type = request.form.get('meal_type')
        
        MealService.remove_meal(day_id, meal_type)
        flash('Comida eliminada correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar comida: {str(e)}', 'error')
    
    return redirect(url_for('main.calendar'))


@main_bp.route('/meal/confirm', methods=['POST'])
def confirm_meal():
    """Confirma que una comida se ejecutó realmente (botón ✓)"""
    try:
        meal_id = request.form.get('meal_id', type=int)
        
        MealService.confirm_meal(meal_id)
        flash('✓ Comida confirmada. Ingredientes descontados del stock real', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error al confirmar comida: {str(e)}', 'error')
    
    return redirect(url_for('main.calendar'))


@main_bp.route('/meal/unconfirm', methods=['POST'])
def unconfirm_meal():
    """Deshace la confirmación de una comida"""
    try:
        meal_id = request.form.get('meal_id', type=int)
        
        MealService.unconfirm_meal(meal_id)
        flash('Confirmación deshecha. Ingredientes devueltos al stock', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error al desconfirmar comida: {str(e)}', 'error')
    
    return redirect(url_for('main.calendar'))


@main_bp.route('/meal/replicate', methods=['POST'])
def replicate_meal():
    """Replica una comida completa a otro día y tipo de comida"""
    try:
        source_meal_id = request.form.get('source_meal_id', type=int)
        target_date_str = request.form.get('target_date')
        target_meal_type = request.form.get('target_meal_type')
        
        # Validar datos
        if not all([source_meal_id, target_date_str, target_meal_type]):
            flash('Faltan datos para replicar la comida', 'error')
            return redirect(url_for('main.calendar'))
        
        # Parsear fecha
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        
        # Obtener comida origen
        source_meal = Meal.query.get_or_404(source_meal_id)
        
        # Obtener o crear día destino
        target_day = CalendarService.get_or_create_day(target_date)
        
        # Obtener o crear comida destino
        target_meal = target_day.get_meal(target_meal_type)
        if not target_meal:
            target_meal = Meal(
                day_id=target_day.id,
                meal_type=target_meal_type
            )
            db.session.add(target_meal)
            db.session.flush()
        
        # Copiar todos los MealDish
        copied_count = 0
        for meal_dish in source_meal.meal_dishes:
            new_meal_dish = MealDish(
                meal_id=target_meal.id,
                dish_id=meal_dish.dish_id,
                portions=meal_dish.portions
            )
            db.session.add(new_meal_dish)
            copied_count += 1
        
        # El stock planificado ya se actualiza automáticamente al crear los MealDish
        
        db.session.commit()
        
        flash(f'✓ Comida replicada exitosamente ({copied_count} platos copiados)', 'success')
    except ValueError as e:
        db.session.rollback()
        flash(f'Error en fecha: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al replicar comida: {str(e)}', 'error')
    
    return redirect(url_for('main.calendar'))


@main_bp.route('/meal/dish/edit', methods=['POST'])
def edit_meal_dish():
    """Edita un plato asignado a una comida (cambiar plato o porciones)"""
    try:
        meal_dish_id = request.form.get('meal_dish_id', type=int)
        dish_id = request.form.get('dish_id', type=int)
        portions = request.form.get('portions', type=int)
        
        # Validar datos
        if not all([meal_dish_id, dish_id, portions]):
            flash('Faltan datos para editar el plato', 'error')
            return redirect(url_for('main.calendar'))
        
        if portions < 1:
            flash('Las porciones deben ser al menos 1', 'error')
            return redirect(url_for('main.calendar'))
        
        # Obtener MealDish
        meal_dish = MealDish.query.get_or_404(meal_dish_id)
        
        # Verificar que la comida no esté confirmada
        if meal_dish.meal.confirmed:
            flash('No se puede editar un plato de una comida ya confirmada', 'error')
            return redirect(url_for('main.calendar'))
        
        # Guardar meal_id antes de cambios
        meal_id = meal_dish.meal_id
        
        # Primero devolver el stock del plato anterior
        old_dish = meal_dish.dish
        old_portions = meal_dish.portions
        
        if not meal_dish.is_batch_mode:
            # Devolver ingredientes del plato anterior
            for di in old_dish.ingredients:
                quantity = di.quantity * old_portions
                PantryService.update_stock_planificado(
                    di.ingredient_id,
                    quantity,
                    operation='add',
                    auto_commit=False
                )
        
        # Actualizar datos
        meal_dish.dish_id = dish_id
        meal_dish.portions = portions
        meal_dish.batch_id = None  # Resetear batch al editar
        meal_dish.percentage = None
        
        # Descontar ingredientes del nuevo plato
        new_dish = Dish.query.get(dish_id)
        for di in new_dish.ingredients:
            quantity = di.quantity * portions
            PantryService.update_stock_planificado(
                di.ingredient_id,
                quantity,
                operation='subtract',
                auto_commit=False
            )
        
        db.session.commit()
        
        flash('✓ Plato actualizado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al editar plato: {str(e)}', 'error')
    
    return redirect(url_for('main.calendar'))


# ==================== PLATOS ====================

@main_bp.route('/dishes')
def dishes():
    """Lista todos los platos"""
    all_dishes = Dish.query.order_by(Dish.name).all()
    return render_template('dishes.html', dishes=all_dishes)


@main_bp.route('/dish/new', methods=['GET', 'POST'])
def new_dish():
    """Crea un nuevo plato"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description', '')
            
            dish = Dish(name=name, description=description)
            db.session.add(dish)
            db.session.flush()
            
            # Añadir ingredientes
            ingredient_ids = request.form.getlist('ingredient_ids[]')
            quantities = request.form.getlist('quantities[]')
            
            for ing_id, qty in zip(ingredient_ids, quantities):
                if ing_id and qty:
                    dish_ingredient = DishIngredient(
                        dish_id=dish.id,
                        ingredient_id=int(ing_id),
                        quantity=float(qty)
                    )
                    db.session.add(dish_ingredient)
            
            db.session.commit()
            flash(f'Plato "{name}" creado correctamente', 'success')
            return redirect(url_for('main.dishes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear plato: {str(e)}', 'error')
    
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return render_template('dish_form.html', dish=None, ingredients=ingredients)


@main_bp.route('/dish/<int:dish_id>/edit', methods=['GET', 'POST'])
def edit_dish(dish_id):
    """Edita un plato existente"""
    dish = Dish.query.get_or_404(dish_id)
    
    if request.method == 'POST':
        try:
            dish.name = request.form.get('name')
            dish.description = request.form.get('description', '')
            
            # Eliminar ingredientes previos
            DishIngredient.query.filter_by(dish_id=dish.id).delete()
            
            # Añadir nuevos ingredientes
            ingredient_ids = request.form.getlist('ingredient_ids[]')
            quantities = request.form.getlist('quantities[]')
            
            for ing_id, qty in zip(ingredient_ids, quantities):
                if ing_id and qty:
                    dish_ingredient = DishIngredient(
                        dish_id=dish.id,
                        ingredient_id=int(ing_id),
                        quantity=float(qty)
                    )
                    db.session.add(dish_ingredient)
            
            db.session.commit()
            flash(f'Plato "{dish.name}" actualizado correctamente', 'success')
            return redirect(url_for('main.dishes'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar plato: {str(e)}', 'error')
    
    ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return render_template('dish_form.html', dish=dish, ingredients=ingredients)


@main_bp.route('/dish/<int:dish_id>/delete', methods=['POST'])
def delete_dish(dish_id):
    """Elimina un plato"""
    try:
        dish = Dish.query.get_or_404(dish_id)
        name = dish.name
        db.session.delete(dish)
        db.session.commit()
        flash(f'Plato "{name}" eliminado correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar plato: {str(e)}', 'error')
    
    return redirect(url_for('main.dishes'))


# ==================== INGREDIENTES ====================

@main_bp.route('/ingredients')
def ingredients():
    """Lista todos los ingredientes"""
    all_ingredients = Ingredient.query.order_by(Ingredient.name).all()
    return render_template('ingredients.html', ingredients=all_ingredients)


@main_bp.route('/ingredient/new', methods=['GET', 'POST'])
def new_ingredient():
    """Crea un nuevo ingrediente"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            unit = request.form.get('unit')
            initial_stock = request.form.get('initial_stock', 0, type=float)
            
            ingredient = Ingredient(name=name, unit=unit)
            db.session.add(ingredient)
            db.session.flush()
            
            # Crear entrada en almacén con stock_actual
            stock = PantryStock(
                ingredient_id=ingredient.id, 
                stock_actual=initial_stock,
                stock_planificado=initial_stock
            )
            db.session.add(stock)
            
            db.session.commit()
            flash(f'Ingrediente "{name}" creado correctamente', 'success')
            return redirect(url_for('main.ingredients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear ingrediente: {str(e)}', 'error')
    
    return render_template('ingredient_form.html', ingredient=None)


@main_bp.route('/ingredient/<int:ingredient_id>/edit', methods=['GET', 'POST'])
def edit_ingredient(ingredient_id):
    """Edita un ingrediente"""
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    if request.method == 'POST':
        try:
            ingredient.name = request.form.get('name')
            ingredient.unit = request.form.get('unit')
            
            db.session.commit()
            flash(f'Ingrediente "{ingredient.name}" actualizado correctamente', 'success')
            return redirect(url_for('main.ingredients'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar ingrediente: {str(e)}', 'error')
    
    return render_template('ingredient_form.html', ingredient=ingredient)


@main_bp.route('/ingredient/<int:ingredient_id>/delete', methods=['POST'])
def delete_ingredient(ingredient_id):
    """Elimina un ingrediente"""
    try:
        ingredient = Ingredient.query.get_or_404(ingredient_id)
        name = ingredient.name
        db.session.delete(ingredient)
        db.session.commit()
        flash(f'Ingrediente "{name}" eliminado correctamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar ingrediente: {str(e)}', 'error')
    
    return redirect(url_for('main.ingredients'))


# ==================== ALMACÉN ====================

@main_bp.route('/pantry')
def pantry():
    """Vista del almacén con doble contador de stock"""
    stocks = PantryStock.query.join(Ingredient).order_by(Ingredient.name).all()
    
    # Incluir ingredientes sin stock
    all_ingredients = Ingredient.query.order_by(Ingredient.name).all()
    stock_dict = {s.ingredient_id: s for s in stocks}
    
    pantry_items = []
    for ingredient in all_ingredients:
        stock = stock_dict.get(ingredient.id)
        pantry_items.append({
            'ingredient': ingredient,
            'stock_actual': stock.stock_actual if stock else 0.0,
            'stock_planificado': stock.stock_planificado if stock else 0.0,
            'falta_comprar': abs(stock.stock_planificado) if (stock and stock.stock_planificado < 0) else 0.0,
            'last_updated': stock.last_updated if stock else None
        })
    
    return render_template('pantry.html', pantry_items=pantry_items)


@main_bp.route('/pantry/update', methods=['POST'])
def update_pantry():
    """Actualiza el stock ACTUAL de un ingrediente"""
    try:
        ingredient_id = request.form.get('ingredient_id', type=int)
        operation = request.form.get('operation', 'set')  # set, add, subtract
        quantity = request.form.get('quantity', type=float)
        
        PantryService.update_stock_actual(ingredient_id, quantity, operation)
        
        ingredient = Ingredient.query.get(ingredient_id)
        flash(f'Stock de "{ingredient.name}" actualizado correctamente', 'success')
        
    except StockError as e:
        flash(str(e), 'error')
    except Exception as e:
        flash(f'Error al actualizar stock: {str(e)}', 'error')
    
    return redirect(url_for('main.pantry'))


# ==================== LISTA DE COMPRA ====================

@main_bp.route('/shopping')
def shopping():
    """Vista de listas de compra"""
    lists = ShoppingList.query.order_by(ShoppingList.created_at.desc()).all()
    return render_template('shopping.html', shopping_lists=lists)


@main_bp.route('/shopping/generate', methods=['GET', 'POST'])
def generate_shopping():
    """Genera una nueva lista de compra desde stock planificado negativo"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '')
            
            shopping_list = ShoppingListService.generate_shopping_list_from_stock(name=name)
            
            flash(f'Lista de compra generada con {shopping_list.total_items} items', 'success')
            return redirect(url_for('main.shopping_detail', list_id=shopping_list.id))
            
        except ValueError as e:
            flash(str(e), 'info')
            return redirect(url_for('main.shopping'))
        except Exception as e:
            flash(f'Error al generar lista: {str(e)}', 'error')
    
    return render_template('shopping_generate.html')


@main_bp.route('/shopping/<int:list_id>')
def shopping_detail(list_id):
    """Detalle de una lista de compra"""
    shopping_list = ShoppingList.query.get_or_404(list_id)
    return render_template('shopping_detail.html', shopping_list=shopping_list)


@main_bp.route('/shopping/<int:list_id>/complete', methods=['POST'])
def complete_shopping(list_id):
    """Marca lista como completada y añade al almacén"""
    try:
        ShoppingListService.complete_shopping_list(list_id)
        flash(f'Lista completada. Items añadidos al almacén.', 'success')
    except Exception as e:
        flash(f'Error al completar lista: {str(e)}', 'error')
    
    return redirect(url_for('main.shopping_detail', list_id=list_id))


@main_bp.route('/shopping/<int:list_id>/item/<int:item_id>/update', methods=['POST'])
def update_shopping_item(list_id, item_id):
    """Actualiza la cantidad de un item en la lista de compra"""
    try:
        new_quantity = float(request.form.get('quantity', 0))
        if new_quantity <= 0:
            raise ValueError("La cantidad debe ser mayor que 0")
        
        item = ShoppingItem.query.get_or_404(item_id)
        item.quantity_to_buy = new_quantity
        db.session.commit()
        
        flash(f'Cantidad actualizada a {new_quantity}', 'success')
    except ValueError as e:
        flash(f'Error: {str(e)}', 'error')
    except Exception as e:
        flash(f'Error al actualizar cantidad: {str(e)}', 'error')
    
    return redirect(url_for('main.shopping_detail', list_id=list_id))


@main_bp.route('/shopping/<int:list_id>/delete', methods=['POST'])
def delete_shopping(list_id):
    """Elimina una lista de compra"""
    try:
        shopping_list = ShoppingList.query.get_or_404(list_id)
        db.session.delete(shopping_list)
        db.session.commit()
        flash('Lista de compra eliminada', 'success')
    except Exception as e:
        flash(f'Error al eliminar lista: {str(e)}', 'error')
    
    return redirect(url_for('main.shopping'))


# ==================== API ENDPOINTS ====================

@main_bp.route('/api/dishes')
def api_dishes():
    """API para obtener lista de platos con información de batches disponibles"""
    from models import DishBatch
    dishes = Dish.query.order_by(Dish.name).all()
    
    result = []
    for d in dishes:
        # Buscar batches con porcentaje disponible
        available_batches = DishBatch.query.filter(
            DishBatch.dish_id == d.id,
            DishBatch.percentage_remaining > 0
        ).all()
        
        total_available = sum(b.percentage_remaining for b in available_batches)
        
        result.append({
            'id': d.id,
            'name': d.name,
            'description': d.description,
            'has_available_batch': total_available > 0,
            'available_percentage': total_available
        })
    
    return jsonify(result)


@main_bp.route('/api/batches')
def api_batches():
    """API para obtener batches disponibles de un plato"""
    from models import DishBatch
    dish_id = request.args.get('dish_id', type=int)
    
    if not dish_id:
        return jsonify([])
    
    batches = DishBatch.query.filter(
        DishBatch.dish_id == dish_id,
        DishBatch.percentage_remaining > 0
    ).order_by(DishBatch.preparation_date.desc()).all()
    
    result = []
    for batch in batches:
        result.append({
            'id': batch.id,
            'dish_id': batch.dish_id,
            'preparation_date': batch.preparation_date.strftime('%Y-%m-%d'),
            'percentage_remaining': batch.percentage_remaining,
            'display_info': batch.display_info
        })
    
    return jsonify(result)


@main_bp.route('/api/ingredients/<int:ingredient_id>/stock')
def api_ingredient_stock(ingredient_id):
    """API para obtener stock de un ingrediente"""
    quantity = PantryService.get_stock(ingredient_id)
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    return jsonify({
        'ingredient_id': ingredient_id,
        'name': ingredient.name,
        'unit': ingredient.unit,
        'quantity': quantity
    })
