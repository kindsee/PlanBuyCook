# PlanBuyCook 🍽️

Aplicación web para la gestión de comidas diarias en casa con control de inventario y lista de compras automática.

## Características

- 📅 **Calendario de comidas**: Planifica desayuno, almuerzo y cena para cada día
- 🍲 **Gestión de platos**: Crea platos con sus ingredientes y cantidades
- 🏪 **Almacén virtual**: Control de stock de ingredientes
- 🛒 **Lista de compra automática**: Calcula qué comprar según la planificación
- ⚠️ **Control de stock**: Previene planificar comidas sin ingredientes suficientes

## Stack Tecnológico

- **Backend**: Python 3.10+ con Flask
- **Base de datos**: MariaDB con SQLAlchemy
- **Frontend**: HTML5 + Bootstrap 5
- **ORM**: SQLAlchemy

## Instalación

### 1. Requisitos previos
- Python 3.10 o superior
- MariaDB 10.5 o superior

### 2. Clonar el repositorio
```bash
git clone <repository-url>
cd PlanBuyCook
```

### 3. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar base de datos
```sql
CREATE DATABASE planbuycook CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales de base de datos
```

### 7. Inicializar base de datos
```bash
python init_db.py
```

### 8. Ejecutar la aplicación
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## Estructura del Proyecto

```
PlanBuyCook/
├── app.py                 # Aplicación Flask principal
├── config.py              # Configuración
├── models.py              # Modelos de base de datos
├── routes.py              # Rutas y controladores
├── services.py            # Lógica de negocio
├── init_db.py             # Script de inicialización
├── requirements.txt       # Dependencias Python
├── templates/             # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── calendar.html
│   ├── dishes.html
│   ├── ingredients.html
│   ├── pantry.html
│   └── shopping_list.html
└── static/                # Archivos estáticos
    └── css/
        └── custom.css
```

## Modelos de Datos

- **Day**: Representa un día con sus comidas
- **Meal**: Comida específica (desayuno, almuerzo, cena)
- **Dish**: Plato con nombre y descripción
- **Ingredient**: Ingrediente con unidad de medida
- **DishIngredient**: Relación plato-ingrediente con cantidad
- **PantryStock**: Stock actual de cada ingrediente
- **ShoppingList**: Lista de compra generada
- **ShoppingItem**: Item individual en la lista de compra

## Uso

### Gestión de Ingredientes
1. Accede a "Ingredientes"
2. Añade ingredientes con su unidad de medida
3. Define el stock inicial en "Almacén"

### Creación de Platos
1. Accede a "Platos"
2. Crea un nuevo plato
3. Añade ingredientes con sus cantidades

### Planificación de Comidas
1. Accede al "Calendario"
2. Selecciona un día y comida
3. Asigna un plato, "Pedir comida" o "Comer fuera"
4. El sistema descuenta automáticamente ingredientes del almacén

### Generar Lista de Compra
1. Accede a "Lista de Compra"
2. Indica el número de semanas a planificar
3. El sistema calcula ingredientes necesarios vs disponibles
4. Genera la lista de compra con cantidades exactas

## Licencia

MIT License
