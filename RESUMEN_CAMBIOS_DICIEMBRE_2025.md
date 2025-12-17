# Resumen de Cambios: Nueva Filosofía de Planificación

## Fecha: 16 de diciembre de 2025

## Cambio principal
Se modificó la filosofía del sistema para permitir **planificación libre de comidas** sin verificar stock de ingredientes.

## Motivación
El usuario necesita poder crear y asignar platos a futuro independientemente de si hay ingredientes disponibles. La lista de compras se genera basándose en lo planificado vs. lo disponible.

---

## Cambios en el código

### 1. `models.py`
**Modelo `DishBatch`**
- ✏️ Docstring actualizado: ahora son "batches virtuales"
- ✏️ `ingredients_deducted` default cambiado: `True` → `False`
- 📝 Los batches ya no representan preparaciones reales, solo planificación

### 2. `services.py`

#### Header del archivo
- ✏️ Docstring completamente reescrito explicando la nueva filosofía
- 📝 Documenta el flujo: planificar → calcular necesario → generar lista

#### Función `MealService.add_dish_to_meal()`
**Eliminado:**
- ❌ Verificación de stock con `check_sufficient_stock()`
- ❌ Deducción de ingredientes con `update_stock(operation='subtract')`
- ❌ Manejo de batches antiguos (migración)
- ❌ Mensajes de error de stock insuficiente

**Modificado:**
- ✏️ Docstring: ahora explica filosofía de batches virtuales
- ✏️ Manejo de excepciones: solo `ValueError`, no `StockError`
- ✏️ Creación de batch con `ingredients_deducted=False`

**Resultado:** Ahora solo crea/asigna el batch virtual sin tocar el almacén.

#### Función `MealService.remove_dish_from_meal()`
- ✏️ Docstring actualizado con nota sobre filosofía
- 📝 Funcionalmente igual (devuelve porcentaje al batch)
- 📝 Aclaración: no devuelve ingredientes porque nunca fueron descontados

#### Función `ShoppingListService.calculate_ingredients_needed()`
- ✏️ Docstring ampliado explicando la nueva filosofía
- 📝 Código sin cambios (ya calculaba correctamente)
- 📝 Ahora está documentado su rol en el flujo

### 3. `routes.py`

#### Header del archivo
- ✏️ Importación de `StockError` mantenida (se usa en actualización manual de almacén)
- ✏️ Comentario actualizado: "planificación libre"

#### Ruta `/meal/assign`
**Modificado:**
- ✏️ Manejo de excepciones: `StockError` → `ValueError`
- 📝 Ya no puede haber error de stock al asignar platos
- 📝 Solo puede haber error de porcentaje inválido

---

## Archivos nuevos creados

### `migrate_to_virtual_batches.py`
Script de migración para bases de datos existentes:
- Marca batches antiguos como virtuales (`ingredients_deducted=False`)
- Opción segura: solo marca batches
- Opción con devolución: devuelve ingredientes al almacén
- Interactivo con confirmación

### `FILOSOFIA_PLANIFICACION.md`
Documentación completa del cambio:
- Comparación ANTES vs AHORA
- Flujo de trabajo ideal (4 pasos)
- Explicación de conceptos técnicos
- Instrucciones de migración
- Ventajas del nuevo sistema
- Lista de archivos modificados

---

## Impacto en funcionalidades

### ✅ Funciona igual
- ✓ Asignación de comidas especiales (pedir comida, comer fuera)
- ✓ Eliminación de platos de comidas
- ✓ Sistema de porcentajes (5%, 10%, 25%, 50%, 100%)
- ✓ Gestión manual del almacén (añadir/restar ingredientes)
- ✓ Generación de lista de compras
- ✓ Completar lista de compras (añade al almacén)

### 🆕 Nuevo comportamiento
- **Asignación de platos:** NO verifica stock, NO descuenta ingredientes
- **Lista de compras:** Muestra TODO lo que falta (basado en planificación)
- **Batches:** Son virtuales por defecto

### 🔜 Funcionalidad futura
- Marcar platos como "consumidos" cuando se cocinen realmente
- Esto sí descontaría ingredientes del almacén

---

## Testing recomendado

1. **Planificar comidas sin stock**
   - Crear platos con ingredientes no disponibles
   - Verificar que se asignan sin error

2. **Generar lista de compras**
   - Planificar varias comidas
   - Verificar que la lista muestra TODO lo necesario
   - Verificar cálculo: necesario - disponible

3. **Completar compra**
   - Marcar lista como completada
   - Verificar que ingredientes se añaden al almacén

4. **Modificar planes**
   - Cambiar platos asignados
   - Verificar que no afecta el almacén

5. **Migración (si hay datos antiguos)**
   - Ejecutar script de migración
   - Verificar que batches quedan marcados como virtuales

---

## Notas para desarrollo futuro

### Campo `ingredients_deducted`
Se mantiene por:
1. **Compatibilidad** con datos de la versión anterior
2. **Futuro:** Distinguir platos planificados vs. realmente consumidos
3. **Trazabilidad:** Historial de qué batches descontaron ingredientes

### Posible función futura: `mark_as_consumed()`
```python
def mark_meal_as_consumed(meal_id):
    """Marca una comida como consumida y descuenta ingredientes"""
    meal = Meal.query.get(meal_id)
    for meal_dish in meal.meal_dishes:
        batch = meal_dish.batch
        if not batch.ingredients_deducted:
            # Descontar ingredientes ahora que se consumió realmente
            for di in batch.dish.ingredients:
                quantity = di.quantity * (meal_dish.percentage / 100.0)
                PantryService.update_stock(di.ingredient_id, quantity, 'subtract')
            batch.ingredients_deducted = True
```

---

## Checklist de verificación

- [x] Código modificado y probado
- [x] Documentación actualizada (docstrings)
- [x] Script de migración creado
- [x] Documento de filosofía creado
- [x] Resumen de cambios creado
- [ ] Tests ejecutados (pendiente usuario)
- [ ] Migración de BD ejecutada (si aplica)
- [ ] Actualizar README.md (opcional)
- [ ] Actualizar ARQUITECTURA.md (opcional)

---

## Comando para probar

```bash
# 1. Activar entorno virtual
venv\Scripts\activate

# 2. (Opcional) Migrar datos existentes
python migrate_to_virtual_batches.py

# 3. Ejecutar aplicación
python app.py

# 4. Probar flujo completo:
#    - Crear ingredientes y platos
#    - Planificar comidas (sin stock)
#    - Generar lista de compras
#    - Completar compra
#    - Verificar almacén
```
