# Cambio de Filosofía: Planificación Libre

## ¿Qué cambió?

### ANTES (filosofía antigua)
- ✗ Solo podías asignar platos si **había ingredientes en stock**
- ✗ Al asignar un plato, se **descontaban automáticamente** los ingredientes
- ✗ No podías planificar comidas futuras sin tener todo comprado

### AHORA (nueva filosofía)
- ✓ Puedes **planificar libremente** cualquier plato, haya o no ingredientes
- ✓ Los ingredientes **NO se descuentan** al planificar
- ✓ La **lista de compras** calcula automáticamente qué te falta comprar
- ✓ Flujo natural: **planificar → generar lista → comprar → cocinar**

## Flujo de trabajo ideal

### 1. Planifica tu semana
Asigna platos a cada comida sin preocuparte del stock:
```
Lunes Almuerzo → Arroz con pollo (100%)
Martes Cena → Pasta carbonara (50%)
Miércoles Almuerzo → Pasta carbonara (50%)
```

### 2. Genera la lista de compras
El sistema calcula automáticamente:
- **Ingredientes necesarios** para todas las comidas planificadas
- **Stock disponible** en tu almacén
- **Cantidad a comprar** = necesario - disponible

### 3. Compra lo que falta
Usa la lista generada para ir al supermercado.

### 4. Completa la compra
Al marcar la lista como "completada", los ingredientes se añaden al almacén.

### 5. (Futuro) Marca como consumido
Cuando cocines realmente, podrás marcar el plato como "consumido" para descontar ingredientes.

## Conceptos técnicos

### Batches Virtuales
Ahora los "batches" son **virtuales** (solo planificación):
- `ingredients_deducted = False` (por defecto)
- Se crean al asignar platos, pero no tocan el almacén
- Permiten usar porcentajes (5%, 10%, 25%, 50%, 100%)

### Cálculo de lista de compras
```python
para cada comida planificada:
    si no es "pedir comida" ni "comer fuera":
        para cada plato en la comida:
            cantidad_necesaria += ingrediente.cantidad × (porcentaje/100)

para cada ingrediente:
    cantidad_a_comprar = max(0, cantidad_necesaria - stock_disponible)
```

## Migración desde versión anterior

Si tenías datos con la filosofía antigua (ingredientes descontados):

### Opción 1: Modo seguro (recomendado)
```bash
python migrate_to_virtual_batches.py
```
- Marca batches como virtuales
- NO devuelve ingredientes al almacén
- Usa si no confías en el stock actual

### Opción 2: Devolver ingredientes
```bash
python migrate_to_virtual_batches.py --return-ingredients
```
- Marca batches como virtuales
- DEVUELVE ingredientes descontados al almacén
- Usa si el stock actual es correcto

## Ventajas del nuevo sistema

1. **Más natural**: Planificas primero, compras después (como en la vida real)
2. **Sin restricciones**: No te bloquea por falta de ingredientes
3. **Lista automática**: Sabes exactamente qué comprar
4. **Flexible**: Puedes cambiar planes sin afectar el stock
5. **Control real**: El almacén refleja lo que realmente tienes

## Archivos modificados

- `models.py`: `DishBatch.ingredients_deducted` default cambiado a `False`
- `services.py`: 
  - `add_dish_to_meal()`: Eliminada verificación y deducción de stock
  - `remove_dish_from_meal()`: Ya no devuelve ingredientes
  - `calculate_ingredients_needed()`: Documentación actualizada
- `routes.py`: Eliminado manejo de `StockError` en asignación de platos

## Nota importante

El campo `ingredients_deducted` en `DishBatch` se mantiene para:
- **Compatibilidad** con datos antiguos
- **Futuro**: Marcar platos realmente consumidos vs. solo planificados
- **Trazabilidad**: Saber qué batches descontaron ingredientes (antiguo sistema)

En la práctica actual, **todos los batches nuevos tienen `ingredients_deducted=False`**.
