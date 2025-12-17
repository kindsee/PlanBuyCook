# RESUMEN DE CAMBIOS - Sistema de Porcentajes de Platos

## ✅ Implementación Completada

Se ha implementado exitosamente el sistema de **múltiples platos por comida** con **porcentajes de uso** (100%, 50%, 25%, 10%, 5%).

---

## 🎯 Características Implementadas

### 1. **Sistema de Batches (Preparaciones)**
- Cada vez que se prepara un plato al 100% por primera vez, se crea un `DishBatch`
- Los ingredientes se **descuentan del almacén solo una vez** al crear el batch
- El batch rastrea el `percentage_remaining` (porcentaje restante disponible)
- Los batches pueden reutilizarse en múltiples comidas hasta agotar el 100%

### 2. **Múltiples Platos por Comida**
- Ahora puedes añadir varios platos a una misma comida (desayuno, almuerzo, cena)
- Cada plato se añade con un porcentaje específico: 5%, 10%, 25%, 50%, 100%
- Los platos se muestran en una lista con su porcentaje correspondiente

### 3. **Lógica de Descuento de Ingredientes**

**Escenario 1 - Primer uso (100%):**
```
Día 1 - Almuerzo: Paella 100%
→ Se crea DishBatch con 100% disponible
→ Se descuentan TODOS los ingredientes del almacén
→ Batch queda con 0% disponible
```

**Escenario 2 - Uso con batch existente:**
```
Día 1 - Almuerzo: Paella 100%
→ Crea batch, descuenta ingredientes
→ Batch: 100% → 0%

Día 2 - Almuerzo: Paella 50%
→ Busca batch existente con suficiente porcentaje
→ NO ENCUENTRA batch con 50% disponible
→ Crea NUEVO batch, descuenta ingredientes otra vez
→ Batch nuevo: 100% → 50%

Día 3 - Cena: Paella 50%
→ Encuentra batch con 50% disponible
→ USA el batch existente SIN descontar ingredientes
→ Batch: 50% → 0%
```

**Escenario 3 - Uso eficiente de porcentajes:**
```
Día 1 - Almuerzo: Paella 50%
→ Crea batch, descuenta ingredientes
→ Batch: 100% → 50% disponible

Día 2 - Cena: Paella 25%
→ USA batch existente (tiene 50% disponible)
→ NO descuenta ingredientes
→ Batch: 50% → 25% disponible

Día 3 - Desayuno: Paella 25%
→ USA batch existente (tiene 25% disponible)
→ NO descuenta ingredientes
→ Batch: 25% → 0%
```

---

## 📋 Cambios en la Base de Datos

### Nuevas Tablas

**`dish_batches`**
```sql
id                      INT PRIMARY KEY
dish_id                 INT (FK → dishes.id)
preparation_date        DATETIME
percentage_remaining    FLOAT (0-100)
ingredients_deducted    BOOLEAN
created_at             DATETIME
```

**`meal_dishes`** (relación N:M entre Meal y Dish)
```sql
id           INT PRIMARY KEY
meal_id      INT (FK → meals.id)
dish_id      INT (FK → dishes.id)
batch_id     INT (FK → dish_batches.id)
percentage   INT (5, 10, 25, 50, 100)
order        INT
created_at   DATETIME
```

### Cambios en Tabla `meals`
- **Eliminadas columnas:** `dish_id`, `ingredients_deducted`
- Ahora solo tiene: `id`, `day_id`, `meal_type`, `special_type`, `created_at`
- La relación con platos se hace a través de `meal_dishes`

---

## 🔧 Nuevos Endpoints API

### POST `/meal/assign`
Añade un plato a una comida con porcentaje
```
Parámetros:
- day_id: ID del día
- meal_type: breakfast/lunch/dinner
- assignment_type: dish/order/eat_out
- dish_id: ID del plato
- percentage: 5, 10, 25, 50, 100
```

### POST `/meal/remove_dish`
Elimina un plato específico de una comida
```
Parámetros:
- meal_dish_id: ID de la relación MealDish
```

### GET `/api/dishes`
Retorna platos con información de batches disponibles
```json
{
  "id": 1,
  "name": "Paella",
  "description": "...",
  "has_available_batch": true,
  "available_percentage": 50.0
}
```

---

## 🎨 Interfaz de Usuario

### Vista de Calendario
- Muestra **lista de platos** asignados a cada comida con su porcentaje
- Cada plato tiene botón [X] para eliminarlo individualmente
- Botón **"Añadir plato"** para agregar más platos a la comida
- Los platos especiales (Pedir comida, Comer fuera) se mantienen igual

### Modal de Asignación
- Selector de tipo: Plato / Pedir comida / Comer fuera
- Selector de plato con indicador de porcentaje disponible
- Selector de porcentaje: 100%, 50%, 25%, 10%, 5%
- **Información en tiempo real:**
  - Si el plato ya tiene batch disponible → muestra "X% disponibles sin coste"
  - Si el plato no tiene batch → indica que se descontarán ingredientes

---

## 📝 Servicios Actualizados

### `MealService.add_dish_to_meal(day_id, meal_type, dish_id, percentage)`
- Busca batch existente con porcentaje suficiente
- Si no existe, crea nuevo batch y descuenta ingredientes
- Resta el porcentaje usado del batch
- Crea relación `MealDish`

### `MealService.remove_dish_from_meal(meal_dish_id)`
- Elimina la relación `MealDish`
- **Devuelve el porcentaje al batch** para que pueda reutilizarse

### `ShoppingListService.calculate_ingredients_needed()`
- Ahora calcula ingredientes considerando porcentajes
- Formula: `quantity = dish_ingredient_quantity * (percentage / 100)`

---

## 🗃️ Migración de Datos

Se ejecutó script `migrate_db.py` que:
1. ✅ Creó tablas `dish_batches` y `meal_dishes`
2. ✅ Migró 2 comidas existentes al nuevo modelo
3. ✅ Eliminó columnas obsoletas de `meals`

Los datos antiguos se conservaron correctamente.

---

## 🚀 Cómo Usar

### 1. Añadir Plato a Comida
1. Ir al **Calendario**
2. Clic en **"Asignar"** o **"Añadir plato"** en una comida
3. Seleccionar **"Plato"**
4. Elegir el plato
5. Seleccionar porcentaje (100%, 50%, 25%, 10%, 5%)
6. Clic en **"Añadir"**

### 2. Ver Batches Disponibles
- Al seleccionar un plato en el modal, verás si tiene porcentaje disponible
- Ejemplo: "Este plato ya fue preparado. Quedan 50% disponibles sin coste de ingredientes"

### 3. Eliminar Plato de Comida
- En el calendario, cada plato tiene un botón [X]
- Al eliminar, el porcentaje se devuelve al batch para reutilizarlo

### 4. Múltiples Platos en una Comida
- Puedes añadir tantos platos como quieras a una misma comida
- Ejemplo: Desayuno → Café 10% + Tostadas 50% + Fruta 25%

---

## 💡 Recomendaciones de Uso

### Para Optimizar Ingredientes:
1. **Prepara platos grandes (100%)** cuando tengas ingredientes
2. **Usa porciones pequeñas (25%, 10%)** en días siguientes
3. Los ingredientes solo se descuentan una vez

### Ejemplo Práctico:
```
Domingo: Cocinas Paella 100% (descuenta ingredientes)
Lunes: Usas Paella 50% en almuerzo (sin coste)
Martes: Usas Paella 50% en cena (sin coste)
→ Con una preparación cubres 3 comidas
```

---

## 🔍 Mantenimiento

### Limpieza de Batches
El sistema incluye método `MealService.cleanup_empty_batches()` que elimina batches completamente usados (0%) de hace más de 7 días.

Puedes ejecutarlo periódicamente para mantener la base de datos limpia.

---

## 📌 Archivos Modificados

### Modelos
- `models.py` - Añadidos `DishBatch` y `MealDish`, modificado `Meal`

### Servicios
- `services.py` - Reescrito `MealService` con sistema de batches
- `services_old_backup.py` - Backup del servicio anterior

### Rutas
- `routes.py` - Actualizados endpoints y API

### Templates
- `templates/calendar.html` - Nueva interfaz con múltiples platos y porcentajes
- `templates/calendar_old.html` - Backup del template anterior

### Migración
- `migrate_db.py` - Script de migración (ya ejecutado)

---

## ✅ Estado del Sistema

**Base de datos:** ✅ Migrada correctamente
**Aplicación:** ✅ Ejecutándose en http://localhost:5001
**Funcionalidad:** ✅ Múltiples platos con porcentajes operativa
**Interfaz:** ✅ Modal con selector de porcentajes y información de batches

---

## 🎉 ¡Sistema Listo para Usar!

Accede a **http://localhost:5001** para probar:
- Calendario de comidas
- Añadir múltiples platos con porcentajes
- Ver batches disponibles
- Optimizar uso de ingredientes

---

## 🔄 ACTUALIZACIÓN: Nueva Filosofía de Planificación (Diciembre 2025)

### ⚠️ CAMBIO IMPORTANTE
Se modificó fundamentalmente la forma en que funcionan los batches y el descuento de ingredientes.

### Filosofía ANTERIOR (Octubre-Noviembre 2025)
- ❌ Solo podías asignar platos si había ingredientes en stock
- ❌ Los ingredientes se descontaban automáticamente al asignar
- ❌ Los batches representaban preparaciones reales

### Filosofía NUEVA (Diciembre 2025)
- ✅ Planificas libremente sin verificar stock
- ✅ Los ingredientes NO se descuentan al planificar
- ✅ Los batches son **virtuales** (solo organización)
- ✅ La lista de compras calcula qué falta

### ¿Por qué el cambio?
La filosofía anterior requería tener ingredientes ANTES de planificar. Esto era contra-intuitivo porque en la vida real primero planificas la semana y LUEGO vas a comprar lo que falta.

### Impacto en Batches
Ahora los batches son **virtuales**:
- `ingredients_deducted = False` por defecto
- Sirven solo para organizar porcentajes
- NO representan preparaciones reales con ingredientes descontados

### Documentación Actualizada
Lee los nuevos documentos:
- `FILOSOFIA_PLANIFICACION.md` - Explicación completa del cambio
- `GUIA_NUEVA_FILOSOFIA.md` - Guía de uso con ejemplos
- `RESUMEN_CAMBIOS_DICIEMBRE_2025.md` - Cambios técnicos detallados
- `migrate_to_virtual_batches.py` - Script para migrar datos antiguos

### Migración Necesaria
Si usaste el sistema con la filosofía anterior, ejecuta:
```bash
python migrate_to_virtual_batches.py
```

---

## 📚 Documentación Completa

- **CAMBIOS_PORCENTAJES.md** ← Este archivo (sistema de porcentajes)
- **FILOSOFIA_PLANIFICACION.md** → Nueva filosofía de planificación
- **GUIA_NUEVA_FILOSOFIA.md** → Guía de uso con ejemplos
- **RESUMEN_CAMBIOS_DICIEMBRE_2025.md** → Cambios técnicos detallados
- **ARQUITECTURA.md** → Arquitectura general del sistema
- **GUIA_USO.md** → Guía de uso general
