# FILOSOFÍA SIMPLIFICADA - Sistema de Doble Stock

## 🎯 Resumen Ejecutivo

Se ha reimplementado COMPLETAMENTE el sistema con una filosofía mucho más simple e intuitiva:

### Antes (Complejo ❌)
- Batches virtuales
- Porcentajes (5%, 10%, 25%, 50%, 100%)
- Stock único
- No sabías qué comprar hasta generar lista

### Ahora (Simple ✅)
- **Porciones simples**: "Tortilla x5"
- **Doble stock**: actual (real) y planificado (con comidas descontadas)
- **Stock negativo = hay que comprar**
- **Botón ✓ para confirmar** cuando cocinas realmente

---

## 📊 Doble Contador de Stock

Cada ingrediente tiene **DOS stocks**:

### 1. Stock Actual (Real)
- Lo que **realmente tienes físicamente** en tu cocina
- Solo se descuenta cuando **confirmas** que cocinaste (botón ✓)
- Se incrementa al comprar

### 2. Stock Planificado
- **Stock actual MENOS lo planificado**
- Se descuenta automáticamente al planificar comidas
- **PUEDE SER NEGATIVO** (significa que hay que comprar)

### Ejemplo Visual

```
Tienes 500g de arroz

PLANIFICAS Paella (necesita 400g):
  stock_actual: 500g (no cambia)
  stock_planificado: 500g - 400g = 100g ✓

PLANIFICAS Arroz con pollo (necesita 300g):
  stock_actual: 500g (no cambia)
  stock_planificado: 100g - 300g = -200g ⚠️ NEGATIVO!
  
💡 Stock negativo = Faltan 200g que comprar

COMPRAS 300g:
  stock_actual: 500g + 300g = 800g
  stock_planificado: -200g + 300g = 100g ✓

CONFIRMAS Paella (✓):
  stock_actual: 800g - 400g = 400g ✓
  stock_planificado: 100g (ya estaba descontado)

CONFIRMAS Arroz con pollo (✓):
  stock_actual: 400g - 300g = 100g ✓
  stock_planificado: 100g (ya estaba descontado)
```

---

## 🍽️ Porciones Simples

Ya no hay porcentajes complejos. Ahora es simple:

- **"Tortilla"** = 1 porción
- **"Tortilla x5"** = 5 porciones

Cada plato tiene ingredientes para 1 porción. Si pones x5, multiplica todo por 5.

---

## ✓ Confirmación de Comidas

### Nuevo botón en cada comida: **✓ Confirmar**

**Cuándo usar:**
- Cuando **realmente cocines** el plato
- Cuando **realmente comas** la comida planificada

**Qué hace:**
- Descuenta ingredientes del **stock actual**
- Marca la comida como "ejecutada"
- Cambia color visual (verde con ✓)

**Flujo completo:**

```
1. PLANIFICAS: "Paella" para el lunes
   → stock_planificado se descuenta
   → stock_actual NO cambia
   
2. GENERAS LISTA: Ves que necesitas comprar X ingredientes
   
3. COMPRAS: Los ingredientes
   → stock_actual aumenta
   → stock_planificado aumenta
   
4. EL LUNES COCINAS: Haces la paella
   → Presionas botón ✓
   → stock_actual se descuenta
   → Comida queda confirmada (verde)
```

---

## 🛒 Lista de Compras AUTOMÁTICA

**Ya no necesitas seleccionar fechas ni semanas.**

La lista se genera automáticamente desde los ingredientes con **stock planificado negativo**:

```
GENERAR LISTA:
  → Busca todos los ingredientes donde stock_planificado < 0
  → Crea lista con: abs(stock_planificado) de cada uno
  
Ejemplo:
  Arroz: stock_planificado = -200g → Lista: "Comprar 200g arroz"
  Huevo: stock_planificado = -5 unidades → Lista: "Comprar 5 huevos"
```

**Ventaja:** Siempre sabes EXACTAMENTE qué falta comprar mirando el stock.

---

## 🔄 Flujo Completo del Usuario

### Lunes (Planificación)
```
1. Abro el calendario
2. Añado platos a la semana:
   - Lunes: Paella x2
   - Martes: Pasta x1
   - Miércoles: Tortilla x3
   
→ stock_planificado se descuenta automáticamente
→ Veo en "Almacén" qué tiene stock negativo (rojo)
```

### Martes (Compra)
```
1. Voy a "Lista de Compra"
2. Click "Generar Lista"
3. Veo lista automática con TODO lo que falta
4. Voy al supermercado
5. Compro lo de la lista
6. Marco lista como "Completada"

→ stock_actual se incrementa
→ stock_planificado vuelve a positivo
```

### Miércoles-Viernes (Ejecución)
```
Cada día que cocino:
1. Cocino el plato planificado
2. Click botón ✓ "Confirmar"
3. La comida queda marcada en verde
4. stock_actual se descuenta

Si no cocino algo planificado:
→ No pasa nada, queda sin confirmar
→ El stock_planificado sigue descontado
→ El stock_actual NO se toca
```

---

## 🆕 Cambios Técnicos Principales

### Base de Datos

**PantryStock:**
- ❌ `quantity` (eliminado)
- ✅ `stock_actual` (nuevo)
- ✅ `stock_planificado` (nuevo)

**Meal:**
- ✅ `confirmed` (nuevo)
- ✅ `confirmed_at` (nuevo)

**MealDish:**
- ❌ `batch_id` (eliminado)
- ❌ `percentage` (eliminado)
- ✅ `portions` (nuevo)

**DishBatch:**
- ⚠️ Tabla mantenida pero ya NO se usa (deprecated)

### Servicios (services.py)

**PantryService:**
- `update_stock_actual()` - Actualiza stock real
- `update_stock_planificado()` - Actualiza stock planificado
- `get_stock()` - Retorna ambos stocks

**MealService:**
- `add_dish_to_meal(day, meal, dish, portions)` - Usa porciones, descuenta planificado
- `confirm_meal(meal_id)` - **NUEVO**: Confirma comida, descuenta actual
- `unconfirm_meal(meal_id)` - **NUEVO**: Deshace confirmación

**ShoppingListService:**
- `generate_shopping_list_from_stock()` - **NUEVO**: Genera lista desde stock negativo

### Rutas (routes.py)

**Nuevas:**
- `POST /meal/confirm` - Confirma comida (botón ✓)
- `POST /meal/unconfirm` - Deshace confirmación

**Modificadas:**
- `/meal/assign` - Usa `portions` en lugar de `percentage`
- `/pantry` - Muestra ambos stocks
- `/shopping/generate` - Genera desde stock negativo

---

## 🔧 Migración desde Versión Anterior

### Paso 1: Backup
```bash
# IMPORTANTE: Haz backup de tu base de datos
mysqldump -u root -p planbuycook > backup_antes_migracion.sql
```

### Paso 2: Ejecutar Migración
```bash
python migrate_to_simple_portions.py
```

El script hará:
1. `quantity` → `stock_actual`
2. Crear `stock_planificado`
3. Añadir `confirmed` y `confirmed_at` a `meals`
4. `(batch_id, percentage)` → `portions` en `meal_dishes`
5. Recalcular stock planificado

### Paso 3: Verificar
```bash
python app.py
# Verifica que todo funciona correctamente
```

---

## 📋 Ventajas del Nuevo Sistema

### ✅ Más Simple
- No más batches complejos
- No más porcentajes (5, 10, 25, 50, 100)
- Porciones intuitivas: x1, x2, x3, x4, x5

### ✅ Más Visual
- Stock negativo en ROJO = hay que comprar
- Comidas confirmadas en VERDE con ✓
- Dos columnas: "Real" y "Planificado"

### ✅ Más Flexible
- Planifica sin límite
- Stock puede quedar negativo (solo es información)
- Confirma cuando realmente cocinas

### ✅ Más Realista
- Refleja cómo realmente funciona una cocina
- Separación entre "plan" y "ejecución"
- Lista de compras automática

---

## 🎨 Interfaz de Usuario

### Vista Almacén
```
Ingrediente | Stock Real | Planificado | Falta Comprar
---------------------------------------------------------
Arroz       | 500g       | -200g       | 200g ⚠️
Pollo       | 1kg        | 800g        | -
Huevo       | 10 un      | 10 un       | -
Tomate      | 0g         | -300g       | 300g ⚠️
```

### Vista Calendario
```
Lunes - Almuerzo
┌─────────────────────────┐
│ Paella x2              │ ✓ Confirmar
│ [Eliminar]             │
└─────────────────────────┘

Lunes - Cena (✓ Confirmada)
┌─────────────────────────┐
│ Tortilla x1  ✓         │ ⟲ Deshacer
└─────────────────────────┘
```

### Formulario Añadir Plato
```
Plato: [Seleccionar ▼]
Porciones: [____] (1, 2, 3, 4, 5...)
[Añadir]
```

---

## ⚡ Quick Start

### Para Usuarios Nuevos
```bash
1. python app.py
2. Crea ingredientes
3. Crea platos
4. Planifica semana
5. Genera lista automática
6. Compra y completa lista
7. Confirma comidas cuando cocines
```

### Para Usuarios con Datos Antiguos
```bash
1. Backup de BD
2. python migrate_to_simple_portions.py
3. python app.py
4. Verifica que todo migró bien
```

---

## 📞 Soporte

**Archivos importantes:**
- `FILOSOFIA_SIMPLIFICADA.md` ← Este archivo
- `migrate_to_simple_portions.py` ← Script de migración
- `services.py` ← Lógica de negocio
- `models.py` ← Modelos de BD
- `routes.py` ← Rutas de la web

**En caso de problemas:**
1. Revisa los logs de la aplicación
2. Verifica que la migración se completó
3. Comprueba que los templates están actualizados
4. Restaura el backup si es necesario

---

## 🔮 Próximos Pasos

Los templates (HTML) aún necesitan actualizarse para:
1. Mostrar porciones "x5" en lugar de porcentajes
2. Añadir botón ✓ "Confirmar" en cada comida
3. Mostrar doble stock en vista almacén
4. Código de colores (rojo=negativo, verde=confirmado)

**Prioridad:** Actualizar templates es el siguiente paso crítico.

---

¡Disfruta del nuevo sistema simplificado! 🎉
