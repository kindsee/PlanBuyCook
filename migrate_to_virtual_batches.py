"""
Script de migración: Cambio a filosofía de batches virtuales

Actualiza la base de datos existente para reflejar la nueva filosofía:
- Los batches existentes se marcan como virtuales (ingredients_deducted=False)
- Opcionalmente, devuelve ingredientes al almacén si fueron descontados previamente

ADVERTENCIA: Este script modifica datos. Haz backup antes de ejecutar.

Uso:
    python migrate_to_virtual_batches.py [--return-ingredients]
    
Opciones:
    --return-ingredients: Devuelve al almacén los ingredientes que fueron descontados
"""
import sys
from datetime import datetime
from app import app
from models import db, DishBatch, PantryStock
from services import PantryService

def migrate_batches_to_virtual(return_ingredients=False):
    """
    Migra los batches existentes a la nueva filosofía virtual
    
    Args:
        return_ingredients: Si True, devuelve ingredientes al almacén
    """
    with app.app_context():
        # Obtener batches que tienen ingredients_deducted=True
        batches = DishBatch.query.filter_by(ingredients_deducted=True).all()
        
        print(f"\n{'='*60}")
        print(f"MIGRACIÓN A BATCHES VIRTUALES")
        print(f"{'='*60}")
        print(f"\nBatches encontrados con ingredientes descontados: {len(batches)}")
        
        if not batches:
            print("\n✓ No hay batches que migrar. Todo listo.")
            return
        
        total_devueltos = 0
        
        for batch in batches:
            dish = batch.dish
            print(f"\n• Batch ID {batch.id}: {dish.name}")
            print(f"  Fecha preparación: {batch.preparation_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"  Porcentaje restante: {batch.percentage_remaining}%")
            
            if return_ingredients:
                # Devolver ingredientes al almacén (100% del plato)
                print(f"  → Devolviendo ingredientes al almacén:")
                for di in dish.ingredients:
                    try:
                        PantryService.update_stock(
                            di.ingredient_id,
                            di.quantity,
                            operation='add',
                            auto_commit=False
                        )
                        print(f"    + {di.ingredient.name}: {di.quantity} {di.ingredient.unit}")
                        total_devueltos += 1
                    except Exception as e:
                        print(f"    ✗ Error con {di.ingredient.name}: {str(e)}")
            else:
                print(f"  → Ingredientes NO se devolverán (modo seguro)")
            
            # Marcar como virtual (sin ingredientes descontados)
            batch.ingredients_deducted = False
        
        # Confirmar cambios
        try:
            db.session.commit()
            print(f"\n{'='*60}")
            print(f"✓ MIGRACIÓN COMPLETADA")
            print(f"{'='*60}")
            print(f"• Batches migrados: {len(batches)}")
            if return_ingredients:
                print(f"• Ingredientes devueltos: {total_devueltos}")
            else:
                print(f"• Ingredientes devueltos: 0 (modo seguro)")
            print(f"\nTodos los batches ahora son virtuales.")
            print(f"Los platos se pueden planificar libremente sin verificar stock.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n✗ ERROR al confirmar cambios: {str(e)}")
            sys.exit(1)


def main():
    """Punto de entrada del script"""
    return_ingredients = '--return-ingredients' in sys.argv
    
    print("\n" + "="*60)
    print("MIGRACIÓN: Cambio a Filosofía de Batches Virtuales")
    print("="*60)
    
    if return_ingredients:
        print("\n⚠️  MODO: Devolución de ingredientes ACTIVADA")
        print("   Los ingredientes descontados se devolverán al almacén")
        response = input("\n¿Continuar? (escribe 'SI' para confirmar): ")
        if response.upper() != 'SI':
            print("\n✗ Migración cancelada")
            sys.exit(0)
    else:
        print("\n✓ MODO SEGURO: Solo marcará batches como virtuales")
        print("   Los ingredientes NO se devolverán al almacén")
        print("   (Usa --return-ingredients para devolverlos)")
    
    migrate_batches_to_virtual(return_ingredients)


if __name__ == '__main__':
    main()
