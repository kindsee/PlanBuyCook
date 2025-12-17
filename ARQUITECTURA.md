# Arquitectura del Proyecto PlanBuyCook

## 📊 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    NAVEGADOR DEL USUARIO                     │
│                    (HTML + Bootstrap)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      FLASK APP (app.py)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              ROUTES (routes.py)                        │ │
│  │  • /calendar - Gestión de calendario                   │ │
│  │  • /dishes - Gestión de platos                         │ │
│  │  • /ingredients - Gestión de ingredientes              │ │
│  │  • /pantry - Control de almacén                        │ │
│  │  • /shopping - Listas de compra                        │ │
│  └──────────────────────┬─────────────────────────────────┘ │
│                         │                                     │
│                         ▼                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │            SERVICES (services.py)                      │ │
│  │  • PantryService - Lógica de almacén                   │ │
│  │  • MealService - Lógica de comidas                     │ │
│  │  • ShoppingListService - Lógica de compras             │ │
│  │  • CalendarService - Lógica de calendario              │ │
│  └──────────────────────┬─────────────────────────────────┘ │
│                         │                                     │
│                         ▼                                     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              MODELS (models.py)                        │ │
│  │  • Ingredient - Ingredientes base                      │ │
│  │  • PantryStock - Stock del almacén                     │ │
│  │  • Dish - Platos                                       │ │
│  │  • DishIngredient - Relación plato-ingrediente         │ │
│  │  • Day - Días del calendario                           │ │
│  │  • Meal - Comidas (desayuno, almuerzo, cena)           │ │
│  │  • ShoppingList - Listas de compra                     │ │
│  │  • ShoppingItem - Items de lista                       │ │
│  └──────────────────────┬─────────────────────────────────┘ │
└─────────────────────────┼─────────────────────────────────────┘
                          │
                          ▼
            ┌─────────────────────────────┐
            │   SQLAlchemy (ORM)          │
            └──────────────┬──────────────┘
                          │
                          ▼
            ┌─────────────────────────────┐
            │   MariaDB Database          │
            │   (planbuycook)             │
            └─────────────────────────────┘
```

## 🗂️ Estructura de Archivos

```
PlanBuyCook/
│
├── 📄 app.py                    # Aplicación Flask principal
├── 📄 config.py                 # Configuración de la app
├── 📄 models.py                 # Modelos de base de datos (SQLAlchemy)
├── 📄 routes.py                 # Rutas y controladores
├── 📄 services.py               # Lógica de negocio
├── 📄 init_db.py                # Script de inicialización de BD
│
├── 📄 requirements.txt          # Dependencias Python
├── 📄 .env.example              # Plantilla de variables de entorno
├── 📄 .gitignore                # Archivos ignorados por Git
├── 📄 README.md                 # Documentación principal
├── 📄 GUIA_USO.md               # Guía detallada de uso
├── 📄 ARQUITECTURA.md           # Este archivo
├── 📄 create_database.sql       # Script SQL para crear BD
│
├── 📁 templates/                # Plantillas HTML (Jinja2)
│   ├── base.html                # Plantilla base
│   ├── index.html               # Página de inicio
│   ├── calendar.html            # Vista de calendario
│   ├── dishes.html              # Lista de platos
│   ├── dish_form.html           # Formulario de plato
│   ├── ingredients.html         # Lista de ingredientes
│   ├── ingredient_form.html     # Formulario de ingrediente
│   ├── pantry.html              # Vista del almacén
│   ├── shopping.html            # Lista de listas de compra
│   ├── shopping_detail.html     # Detalle de lista
│   └── shopping_generate.html   # Generador de lista
│
└── 📁 static/                   # Archivos estáticos
    └── 📁 css/
        └── custom.css           # Estilos personalizados
```

## 🔄 Flujo de Datos

### 1. Flujo de Planificación de Comida

```
Usuario selecciona plato para una comida
          ↓
routes.py recibe solicitud
          ↓
MealService.assign_dish_to_meal()
          ↓
Verifica stock con PantryService.check_sufficient_stock()
          ↓
¿Hay stock suficiente?
    ├─ NO → Retorna error (StockError)
    │
    └─ SÍ → Descuenta ingredientes con PantryService.update_stock()
              ↓
          Crea/actualiza Meal en BD
              ↓
          Marca ingredients_deducted = True
              ↓
          Retorna éxito
```

### 2. Flujo de Generación de Lista de Compra

```
Usuario solicita generar lista (período: X semanas)
          ↓
routes.py recibe solicitud
          ↓
ShoppingListService.generate_shopping_list()
          ↓
Calcula ingredientes necesarios (calculate_ingredients_needed)
    ├─ Obtiene días del período
    ├─ Itera sobre comidas de cada día
    ├─ Suma cantidades de ingredientes
    └─ Retorna dict {ingredient_id: quantity_needed}
          ↓
Para cada ingrediente:
    ├─ Obtiene stock disponible (PantryService.get_stock)
    ├─ Calcula: quantity_to_buy = max(0, needed - available)
    └─ Crea ShoppingItem si quantity_to_buy > 0
          ↓
Crea ShoppingList con todos los items
          ↓
Retorna lista generada
```

### 3. Flujo de Completar Lista de Compra

```
Usuario marca lista como completada
          ↓
routes.py recibe solicitud
          ↓
ShoppingListService.mark_list_completed()
          ↓
Para cada item en la lista:
    ├─ PantryService.update_stock(ingredient_id, quantity_to_buy, 'add')
    ├─ Marca item.purchased = True
    └─ Actualiza stock en PantryStock
          ↓
Marca shopping_list.completed = True
          ↓
Retorna lista actualizada
```

## 🗄️ Modelo de Base de Datos

### Relaciones entre Tablas

```
Ingredient (1) ────┬─── (1) PantryStock
                   │
                   └─── (N) DishIngredient ─── (1) Dish
                                                     │
                                                     └─── (N) Meal ─── (1) Day

ShoppingList (1) ─── (N) ShoppingItem ─── (1) Ingredient
```

### Descripción de Modelos

#### Ingredient
- **Propósito**: Define ingredientes base
- **Campos clave**: `name`, `unit`
- **Relaciones**: PantryStock (1:1), DishIngredient (1:N)

#### PantryStock
- **Propósito**: Stock actual de cada ingrediente
- **Campos clave**: `ingredient_id`, `quantity`
- **Restricciones**: quantity >= 0

#### Dish
- **Propósito**: Platos/recetas disponibles
- **Campos clave**: `name`, `description`
- **Relaciones**: DishIngredient (1:N), Meal (1:N)

#### DishIngredient
- **Propósito**: Relación plato-ingrediente con cantidad
- **Campos clave**: `dish_id`, `ingredient_id`, `quantity`
- **Restricciones**: Unique(dish_id, ingredient_id), quantity > 0

#### Day
- **Propósito**: Día del calendario
- **Campos clave**: `date` (unique)
- **Relaciones**: Meal (1:N)

#### Meal
- **Propósito**: Comida específica de un día
- **Campos clave**: `meal_type` (breakfast/lunch/dinner), `dish_id`, `special_type`
- **Lógica**: dish_id Y special_type son mutuamente excluyentes
- **Flag**: `ingredients_deducted` para control de descuento

#### ShoppingList
- **Propósito**: Lista de compra generada
- **Campos clave**: `name`, `start_date`, `end_date`, `completed`
- **Relaciones**: ShoppingItem (1:N)

#### ShoppingItem
- **Propósito**: Item individual en lista de compra
- **Campos clave**: `ingredient_id`, `quantity_needed`, `quantity_available`, `quantity_to_buy`

## 🔐 Servicios y Responsabilidades

### PantryService
**Responsabilidad**: Gestión del almacén virtual

**Métodos principales**:
- `get_stock(ingredient_id)` - Obtener stock actual
- `update_stock(ingredient_id, quantity, operation)` - Actualizar stock
  - operation: 'set', 'add', 'subtract'
- `check_sufficient_stock(ingredient_quantities)` - Verificar disponibilidad

### MealService
**Responsabilidad**: Gestión de comidas y calendario

**Métodos principales**:
- `assign_dish_to_meal(day_id, meal_type, dish_id)` - Asignar plato
- `assign_special_to_meal(day_id, meal_type, special_type)` - Asignar especial
- `remove_meal(day_id, meal_type)` - Eliminar comida
- `_return_ingredients(dish_id)` - Devolver ingredientes al almacén

### ShoppingListService
**Responsabilidad**: Generación y gestión de listas de compra

**Métodos principales**:
- `calculate_ingredients_needed(start_date, end_date)` - Calcular necesidades
- `generate_shopping_list(start_date, weeks, name)` - Generar lista
- `mark_list_completed(shopping_list_id)` - Completar lista

### CalendarService
**Responsabilidad**: Gestión del calendario

**Métodos principales**:
- `get_or_create_day(date)` - Obtener o crear día
- `get_week_days(start_date)` - Obtener semana completa

## 🎨 Stack Tecnológico

### Backend
- **Framework**: Flask 3.0.0
- **ORM**: SQLAlchemy 2.0.23
- **Database Driver**: PyMySQL 1.1.0
- **Environment**: python-dotenv 1.0.0

### Frontend
- **Templates**: Jinja2 (incluido en Flask)
- **CSS Framework**: Bootstrap 5.3.0
- **Icons**: Bootstrap Icons 1.10.0
- **JavaScript**: Vanilla JS (sin frameworks adicionales)

### Base de Datos
- **Motor**: MariaDB 10.5+
- **Charset**: utf8mb4
- **Collation**: utf8mb4_unicode_ci

## 🔒 Seguridad y Buenas Prácticas

### Implementadas
- ✅ Variables de entorno para credenciales
- ✅ SQLAlchemy ORM (previene SQL injection)
- ✅ Validaciones de stock antes de operaciones
- ✅ Constraints de base de datos (CHECK, UNIQUE)
- ✅ Manejo de errores con excepciones personalizadas
- ✅ Flash messages para feedback al usuario

### Recomendaciones para Producción
- 🔐 Cambiar SECRET_KEY a valor fuerte y único
- 🔐 Usar HTTPS
- 🔐 Implementar autenticación de usuarios
- 🔐 Añadir rate limiting
- 🔐 Configurar backups automáticos de BD
- 🔐 Usar gunicorn o uwsgi en lugar de servidor de desarrollo
- 🔐 Configurar logs de auditoría

## 🚀 Despliegue

### Desarrollo Local
```bash
python app.py
# Acceder a http://localhost:5000
```

### Producción (ejemplo con gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Variables de Entorno Requeridas
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `FLASK_SECRET_KEY`
- `FLASK_ENV` (development/production)

## 📈 Posibles Extensiones Futuras

1. **Autenticación**: Sistema multi-usuario con familias
2. **API REST**: Endpoints JSON para aplicación móvil
3. **Recetas**: Añadir instrucciones paso a paso
4. **Etiquetas**: Categorizar platos (vegetariano, sin gluten, etc.)
5. **Estadísticas**: Gráficos de consumo y gastos
6. **Exportación**: PDF de listas de compra
7. **Notificaciones**: Alertas de stock bajo
8. **Historial**: Registro de comidas consumidas
9. **Presupuesto**: Control de costos de ingredientes
10. **Integración**: Conexión con supermercados online

---

**Documentación actualizada**: Diciembre 2024
