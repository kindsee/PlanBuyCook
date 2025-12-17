"""
Script de migración para añadir soporte de batches a MealDish

Añade las columnas:
- batch_id (FK a dish_batches)
- percentage (porcentaje del batch usado)

Permite dos modos:
1. Porciones múltiples: portions=5, batch_id=NULL
2. Uso de batch: portions=1, batch_id=X, percentage=50
"""
from app import create_app
from models import db

def migrate():
    app = create_app()
    
    with app.app_context():
        print("🔧 Añadiendo soporte de batches a meal_dishes...")
        
        # Añadir columnas si no existen
        with db.engine.connect() as conn:
            # Verificar si ya existen
            result = conn.execute(db.text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'meal_dishes' 
                AND COLUMN_NAME = 'batch_id'
            """))
            
            exists = result.fetchone()[0] > 0
            
            if not exists:
                print("   Añadiendo columna batch_id...")
                conn.execute(db.text("""
                    ALTER TABLE meal_dishes 
                    ADD COLUMN batch_id INT NULL,
                    ADD CONSTRAINT fk_meal_dishes_batch 
                        FOREIGN KEY (batch_id) REFERENCES dish_batches(id)
                        ON DELETE CASCADE
                """))
                conn.commit()
                
                print("   Añadiendo columna percentage...")
                conn.execute(db.text("""
                    ALTER TABLE meal_dishes 
                    ADD COLUMN percentage FLOAT NULL
                """))
                conn.commit()
                
                print("   Añadiendo constraint de percentage...")
                conn.execute(db.text("""
                    ALTER TABLE meal_dishes 
                    ADD CONSTRAINT check_percentage_valid_range 
                    CHECK (percentage IS NULL OR (percentage > 0 AND percentage <= 100))
                """))
                conn.commit()
                
                print("✅ Columnas añadidas correctamente")
            else:
                print("ℹ️  Las columnas ya existen, no se requiere migración")
        
        print("\n✅ Migración completada")
        print("\nAhora tienes dos modos de uso:")
        print("1. Porciones múltiples: Tortilla x5 (descuenta 5 veces)")
        print("2. Batch con porcentaje: Paella 50% (usa mitad de un batch)")

if __name__ == '__main__':
    migrate()
