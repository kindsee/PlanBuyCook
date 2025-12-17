# GitHub Copilot Instructions for PlanBuyCook

## Project Overview
PlanBuyCook is a Flask-based web application for managing daily meal planning, ingredient inventory, and automated shopping list generation for home use.

## Tech Stack
- **Backend**: Python 3.10+, Flask 3.0, SQLAlchemy 2.0
- **Database**: MariaDB with PyMySQL driver
- **Frontend**: HTML5, Bootstrap 5, Jinja2 templates, Vanilla JavaScript
- **Architecture**: MVC with service layer

## Project Structure
```
app.py          → Flask app initialization and main entry point
config.py       → Configuration using environment variables
models.py       → SQLAlchemy models (8 tables with relationships)
routes.py       → Flask blueprints and route handlers
services.py     → Business logic layer (4 service classes)
templates/      → Jinja2 HTML templates with Bootstrap
static/css/     → Custom CSS styles
```

## Key Architectural Patterns

### Service Layer Pattern
All business logic is isolated in service classes (`services.py`):
- `PantryService` - Inventory management
- `MealService` - Meal assignment and ingredient deduction
- `ShoppingListService` - Shopping list generation
- `CalendarService` - Calendar day management

**Example**: When assigning a meal, use `MealService.assign_dish_to_meal()` rather than direct model manipulation.

### Model Relationships
Critical model connections:
- `Ingredient` ←1:1→ `PantryStock` (stock tracking)
- `Ingredient` ←1:N→ `DishIngredient` ←N:1→ `Dish` (recipe ingredients)
- `Day` ←1:N→ `Meal` →N:1→ `Dish` (meal planning)
- `ShoppingList` ←1:N→ `ShoppingItem` →N:1→ `Ingredient` (shopping)

### Database Constraints
- `PantryStock.quantity >= 0` - Prevent negative inventory
- `Meal` - Mutually exclusive: either `dish_id` OR `special_type`, not both
- `DishIngredient` - Unique constraint on (dish_id, ingredient_id)

## Important Business Rules

### 1. Automatic Ingredient Deduction
When a dish is assigned to a meal:
1. Check stock sufficiency with `PantryService.check_sufficient_stock()`
2. If insufficient, raise `StockError` with details
3. If sufficient, subtract ingredients with `PantryService.update_stock(operation='subtract')`
4. Set `Meal.ingredients_deducted = True`

### 2. Special Meal Types
- `special_type='order'` (Pedir comida) - Does NOT consume ingredients
- `special_type='eat_out'` (Comer fuera) - Does NOT consume ingredients
- Only `Meal` with `dish_id` consumes ingredients

### 3. Meal Reassignment
When changing a meal's dish:
- Return previous dish's ingredients to pantry with `_return_ingredients()`
- Then deduct new dish's ingredients
- Handle atomically within a transaction

### 4. Shopping List Calculation
Formula for each ingredient:
```python
quantity_to_buy = max(0, quantity_needed - quantity_available)
```
Only create `ShoppingItem` if `quantity_to_buy > 0`

## Code Style Conventions

### Python
- **Docstrings**: Google style for all classes and public methods
- **Type hints**: Preferred but not enforced
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Imports**: Group by stdlib, third-party, local with blank lines between
- **Error handling**: Use `StockError` for inventory issues, handle in routes with flash messages

### Flask Routes
- Use blueprints (`main_bp` in routes.py)
- Return redirects with `flash()` messages for POST operations
- Return templates with context for GET operations
- API endpoints prefix with `/api/` and return JSON

### Templates
- Extend `base.html` which includes Bootstrap 5 and custom navbar
- Use Bootstrap utility classes rather than custom CSS when possible
- Icons from Bootstrap Icons (`<i class="bi bi-icon-name"></i>`)
- Forms: Use POST method with CSRF token (Flask-WTF if added)
- JavaScript: Place in `{% block extra_js %}` at bottom

### Database Operations
- Always use service layer methods, not direct model manipulation
- Use `db.session.flush()` when you need ID before commit
- Wrap related operations in try/except with `db.session.rollback()`
- Use `get_or_404()` for single record retrieval in routes

## Common Development Tasks

### Adding a New Route
1. Define in `routes.py` under appropriate section comment
2. Use service layer for business logic
3. Add template in `templates/`
4. Update navbar in `base.html` if needed

### Adding a New Model
1. Define in `models.py` with proper relationships
2. Add to `db.create_all()` (automatic)
3. Create migration if using Flask-Migrate (not currently set up)
4. Update `init_db.py` if sample data needed

### Adding Business Logic
1. Add method to appropriate service class in `services.py`
2. Use `@staticmethod` for stateless operations
3. Raise `StockError` for inventory violations
4. Document parameters and return values

### Modifying Templates
- Maintain consistent Bootstrap structure
- Use flash message categories: 'success', 'error', 'warning', 'info'
- Modals use Bootstrap 5 syntax (data-bs-* attributes)
- Keep JavaScript minimal, use vanilla JS

## Testing Approach

### Manual Testing Flow
1. Initialize DB: `python init_db.py` (loads sample data)
2. Run app: `python app.py`
3. Test sequence:
   - Create ingredients → Create dishes → Plan meals → Generate shopping list

### Key Test Cases
- Assign meal with insufficient stock → Should show error
- Reassign meal → Previous ingredients should return to stock
- Complete shopping list → Items should add to pantry
- Delete dish used in future meals → Should cascade properly

## Database Initialization
```bash
# Fresh start with sample data
python init_db.py

# Fresh start without sample data
python init_db.py --no-sample
```

Sample data includes:
- 21 common ingredients with initial stock
- 5 sample dishes (Arroz con Pollo, Pasta Carbonara, etc.)
- 3 days of sample meal planning

## Environment Configuration
Required `.env` variables:
```
DB_HOST=localhost
DB_PORT=3306
DB_NAME=planbuycook
DB_USER=root
DB_PASSWORD=your_password
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development
```

## Common Pitfalls to Avoid

1. **Direct Model Updates**: Always use service layer to maintain business logic integrity
2. **Forgetting Stock Checks**: Verify stock before any operation that consumes ingredients
3. **Ignoring ingredients_deducted Flag**: Check this before deducting to avoid double-deduction
4. **Template Variable Errors**: Use `{{ var if var else '' }}` to handle None values
5. **Date Handling**: Use `datetime.date` for dates, not `datetime` objects, in Day model

## Useful Development Commands
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
# Access at http://localhost:5000

# Reset database
python init_db.py
```

## Spanish Language Notes
The application is fully in Spanish:
- Template text uses Spanish labels
- Flash messages are in Spanish
- Database content (sample data) is in Spanish
- Comments and docstrings are in Spanish

When generating code, maintain Spanish for user-facing text and English for code/technical documentation.

## Extension Points

### Adding User Authentication
- Create `User` model
- Add `user_id` foreign key to relevant models (Day, ShoppingList)
- Use Flask-Login for session management
- Update routes to filter by current user

### Adding Recipe Instructions
- Add `instructions` field to Dish model (Text)
- Create template to display step-by-step
- Consider separate `RecipeStep` model for ordered steps

### API Endpoints
Current API routes (minimal):
- `GET /api/dishes` - List all dishes
- `GET /api/ingredients/<id>/stock` - Get ingredient stock

To extend, create API blueprint with JSON responses.

## Performance Considerations
- Large shopping list calculations iterate through all planned meals
- Consider caching frequently accessed stock values
- Add database indexes on foreign keys (automatically done by SQLAlchemy)
- For production, use connection pooling in SQLAlchemy

---

When generating code, respect these patterns and always prefer service layer methods over direct model manipulation. Maintain the existing architecture and Spanish language for user-facing elements.
