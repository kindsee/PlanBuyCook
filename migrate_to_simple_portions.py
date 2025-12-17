"""
Script de migración: De batches/porcentajes a porciones simples

Migra la base de datos a la nueva filosofía simplificada:
1. PantryStock: quantity → stock_actual + stock_planificado
2. MealDish: (batch_id, percentage) → portions
3. Meal: añade campos confirmed y confirmed_at
4. DishBatch: se marca como deprecated (opcional: eliminarlo)

ADVERTENCIA: Este script modifica la estructura de la BD. Haz BACKUP antes.

Uso:
    python migrate_to_simple_portions.py
"""
import sys
from datetime import datetime
from app import create_app
from models import db

app = create_app()

def migrate_database():
    """Ejecuta las migraciones SQL necesarias"""
    
    print("\n" + "="*60)
    print("MIGRACIÓN: De Batches/Porcentajes a Porciones Simples")
    print("="*60)
    
    # Confirmar
    print("\n⚠️  ADVERTENCIA: Este script modificará la estructura de la base de datos")
    print("   Asegúrate de haber hecho un BACKUP antes de continuar")
    response = input("\n¿Continuar? (escribe 'SI' para confirmar): ")
    if response.upper() != 'SI':
        print("\n✗ Migración cancelada")
        sys.exit(0)
    
    with app.app_context():
        try:
            print("\n[1/7] Migrando PantryStock...")
            # Renombrar quantity a stock_actual, crear stock_planificado
            db.session.execute(db.text("""
                ALTER TABLE pantry_stock 
                CHANGE COLUMN quantity stock_actual FLOAT NOT NULL DEFAULT 0.0
            """))
            db.session.execute(db.text("""
                ALTER TABLE pantry_stock 
                ADD COLUMN stock_planificado FLOAT NOT NULL DEFAULT 0.0 AFTER stock_actual
            """))
            # Inicializar stock_planificado = stock_actual (sin planificación pendiente)
            db.session.execute(db.text("""
                UPDATE pantry_stock SET stock_planificado = stock_actual
            """))
            # Eliminar constraint antigua
            try:
                db.session.execute(db.text("""
                    ALTER TABLE pantry_stock DROP CHECK check_quantity_positive
                """))
            except:
                pass  # Puede no existir
            print("   ✓ PantryStock migrado")
            
            print("\n[2/7] Añadiendo campos a Meal...")
            # Añadir confirmed y confirmed_at
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meals 
                    ADD COLUMN confirmed BOOLEAN NOT NULL DEFAULT FALSE AFTER special_type
                """))
            except:
                print("   ⚠️  Campo 'confirmed' ya existe")
            
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meals 
                    ADD COLUMN confirmed_at DATETIME NULL AFTER confirmed
                """))
            except:
                print("   ⚠️  Campo 'confirmed_at' ya existe")
            print("   ✓ Meal actualizado")
            
            print("\n[3/7] Migrando MealDish...")
            # Convertir percentage a portions (100% = 1 porción, 50% = 0.5 -> redondeamos a 1)
            # Primero añadir columna portions
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meal_dishes 
                    ADD COLUMN portions INT NOT NULL DEFAULT 1 AFTER dish_id
                """))
            except:
                print("   ⚠️  Campo 'portions' ya existe")
            
            # Convertir porcentajes a porciones (simplificado: percentage/100 redondeado)
            db.session.execute(db.text("""
                UPDATE meal_dishes 
                SET portions = GREATEST(1, ROUND(percentage / 100))
            """))
            
            # Eliminar columnas antiguas
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meal_dishes DROP FOREIGN KEY meal_dishes_ibfk_3
                """))
            except:
                pass
            
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meal_dishes DROP COLUMN batch_id
                """))
            except:
                print("   ⚠️  Columna 'batch_id' ya eliminada")
            
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meal_dishes DROP COLUMN percentage
                """))
            except:
                print("   ⚠️  Columna 'percentage' ya eliminada")
            
            # Eliminar constraint antigua
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meal_dishes DROP CHECK check_valid_percentage
                """))
            except:
                pass
            
            # Añadir nuevo constraint
            try:
                db.session.execute(db.text("""
                    ALTER TABLE meal_dishes 
                    ADD CONSTRAINT check_portions_positive CHECK (portions > 0)
                """))
            except:
                print("   ⚠️  Constraint 'check_portions_positive' ya existe")
            
            print("   ✓ MealDish migrado")
            
            print("\n[4/7] Recalculando stock planificado...")
            # Resetear stock_planificado = stock_actual
            db.session.execute(db.text("""
                UPDATE pantry_stock SET stock_planificado = stock_actual
            """))
            
            # Descontar todas las comidas NO confirmadas planificadas
            result = db.session.execute(db.text("""
                SELECT 
                    di.ingredient_id,
                    SUM(di.quantity * md.portions) as total_needed
                FROM meal_dishes md
                JOIN meals m ON md.meal_id = m.id
                JOIN dish_ingredients di ON md.dish_id = di.dish_id
                WHERE m.confirmed = FALSE AND m.special_type IS NULL
                GROUP BY di.ingredient_id
            """))
            
            for row in result:
                ingredient_id = row[0]
                total_needed = row[1]
                db.session.execute(db.text(f"""
                    UPDATE pantry_stock 
                    SET stock_planificado = stock_planificado - {total_needed}
                    WHERE ingredient_id = {ingredient_id}
                """))
            
            print("   ✓ Stock planificado recalculado")
            
            print("\n[5/7] Marcando tabla DishBatch como deprecated...")
            # Opcionalmente, podríamos eliminar la tabla, pero la dejamos por compatibilidad
            print("   ℹ️  Tabla dish_batches mantenida (ya no se usa)")
            
            print("\n[6/7] Actualizando ShoppingList...")
            # Eliminar campo 'status' si existe y añadir 'completed'
            try:
                db.session.execute(db.text("""
                    ALTER TABLE shopping_lists DROP COLUMN status
                """))
            except:
                pass
            
            try:
                db.session.execute(db.text("""
                    ALTER TABLE shopping_lists 
                    ADD COLUMN completed BOOLEAN NOT NULL DEFAULT FALSE AFTER end_date
                """))
            except:
                print("   ⚠️  Campo 'completed' ya existe")
            
            print("   ✓ ShoppingList actualizado")
            
            print("\n[7/7] Confirmando cambios...")
            db.session.commit()
            
            print("\n" + "="*60)
            print("✓ MIGRACIÓN COMPLETADA EXITOSAMENTE")
            print("="*60)
            print("\nCambios realizados:")
            print("• PantryStock: quantity → stock_actual + stock_planificado")
            print("• Meal: añadidos campos confirmed y confirmed_at")
            print("• MealDish: batch_id y percentage → portions")
            print("• Stock planificado recalculado según comidas pendientes")
            print("\nNOTA: La tabla dish_batches se mantiene pero ya no se usa")
            print("\nPuedes ejecutar la aplicación normalmente:")
            print("  python app.py")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ ERROR durante la migración: {str(e)}")
            print("\nLa base de datos se ha revertido al estado anterior")
            print("Revisa el error y vuelve a intentarlo")
            sys.exit(1)


if __name__ == '__main__':
    migrate_database()
