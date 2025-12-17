# FAQ: Nueva Filosofía de Planificación

## Preguntas Frecuentes sobre el Cambio

---

## General

### ¿Qué cambió exactamente?
**Antes:** Solo podías asignar platos si tenías ingredientes en stock. Al asignar, se descontaban automáticamente.

**Ahora:** Puedes planificar libremente sin verificar stock. Los ingredientes NO se descuentan. La lista de compras te dice qué falta.

### ¿Por qué se hizo este cambio?
La filosofía anterior era contra-intuitiva. En la vida real primero **planificas** la semana y **después** vas a comprar lo que falta. No al revés.

### ¿Esto rompe mi aplicación existente?
No. Solo necesitas ejecutar el script de migración si tienes datos:
```bash
python migrate_to_virtual_batches.py
```

---

## Sobre los Batches

### ¿Qué son los "batches virtuales"?
Son registros que organizan el uso de porcentajes de platos, pero NO representan preparaciones reales con ingredientes descontados.

### ¿Qué significa `ingredients_deducted = False`?
Significa que ese batch es virtual (planificación) y NO descontó ingredientes del almacén.

### ¿Por qué mantener el campo `ingredients_deducted`?
Por 3 razones:
1. **Compatibilidad** con datos de la versión anterior
2. **Futuro:** Distinguir platos planificados vs. realmente consumidos
3. **Trazabilidad:** Saber qué batches descontaron ingredientes (versión anterior)

### ¿Los batches antiguos siguen funcionando?
Sí, pero necesitas migrarlos con el script `migrate_to_virtual_batches.py`

---

## Planificación de Comidas

### ¿Puedo asignar un plato aunque no tenga ingredientes?
**Sí.** Esa es la esencia del cambio. Planificas libremente.

### ¿Qué pasa si no tengo nada en el almacén?
Nada. Puedes planificar toda tu semana igual. La lista de compras te mostrará TODO lo que necesitas comprar.

### ¿Puedo cambiar los platos planificados fácilmente?
**Sí.** Como no afectan el stock, puedes cambiarlos cuantas veces quieras sin problemas.

### ¿Se pierden los porcentajes si cambio un plato?
No. El porcentaje se devuelve al batch para que pueda reutilizarse.

---

## Lista de Compras

### ¿Cómo sabe qué comprar si no descuenta ingredientes?
La lista calcula:
```
Para cada ingrediente:
  cantidad_a_comprar = necesario_para_todas_comidas - stock_disponible
```

### ¿Puede la lista mostrar cantidades negativas?
No. Si tienes más de lo necesario, simplemente no aparece en la lista.

### ¿Puedo generar varias listas para fechas solapadas?
Sí, pero cada una calculará independientemente. Ten en cuenta que la última que completes actualizará el stock.

### ¿La lista incluye platos marcados como "Pedir comida" o "Comer fuera"?
No. Esos tipos de comida NO consumen ingredientes, por lo que no aparecen en la lista.

---

## Almacén

### ¿Cuándo se descuentan los ingredientes ahora?
Actualmente, **NUNCA** se descuentan automáticamente. Puedes hacerlo manualmente desde "Almacén".

### ¿Cómo sé cuántos ingredientes me quedan?
Ve a la sección "Almacén" para ver tu stock actual.

### ¿Debo actualizar el almacén manualmente cuando cocino?
Por ahora **sí**, si quieres que el stock refleje la realidad. En el futuro habrá función "Marcar como consumido".

### ¿Qué pasa al completar una lista de compras?
Los ingredientes se **añaden automáticamente** al almacén con las cantidades compradas.

---

## Migración

### ¿Debo ejecutar el script de migración?
**Sí**, si usaste la versión anterior con ingredientes descontados.

**No**, si empiezas de cero con la nueva versión.

### ¿Qué hace el script de migración?
Marca todos los batches existentes como virtuales (`ingredients_deducted = False`).

Opcionalmente, puede devolver al almacén los ingredientes que fueron descontados.

### ¿Cuál opción del script debo usar?

**Opción 1 - Modo seguro (recomendado):**
```bash
python migrate_to_virtual_batches.py
```
- Solo marca batches como virtuales
- NO toca el almacén
- Usa esta si no confías en que el stock actual es correcto

**Opción 2 - Con devolución:**
```bash
python migrate_to_virtual_batches.py --return-ingredients
```
- Marca batches como virtuales
- DEVUELVE ingredientes descontados al almacén
- Usa esta si confías en que el stock actual es correcto

### ¿Puedo revertir la migración?
No fácilmente. Haz **backup de tu base de datos** antes de ejecutar el script.

### ¿Qué pasa si no migro?
Los batches antiguos con `ingredients_deducted = True` seguirán funcionando, pero pueden causar confusión. Es mejor migrarlos.

---

## Funcionalidad Futura

### ¿Habrá función "Marcar como consumido"?
Sí, está planificada. Permitirá:
- Marcar cuando realmente cocines un plato planificado
- Descontar ingredientes en ese momento
- Distinguir platos planificados vs. realmente consumidos

### ¿Cómo funcionaría "Marcar como consumido"?
```
1. Tienes "Paella" planificada para el lunes
2. El lunes cocinas realmente
3. Marcas como "consumido"
4. Se descuentan ingredientes del almacén
5. El batch se marca como ingredients_deducted = True
```

### ¿Cuándo estará disponible?
No hay fecha definida. El sistema actual funciona bien sin ella (con gestión manual del almacén).

---

## Casos de Uso Específicos

### Caso: Compro gradualmente durante la semana
**Solución:** 
- Genera la lista completa al inicio
- Añade manualmente al almacén lo que vayas comprando
- Regenera la lista y verás que ya no pide lo que compraste

### Caso: Cambio de opinión a mitad de semana
**Solución:**
- Elimina el plato planificado
- Añade el nuevo plato
- Regenera la lista de compras con los cambios

### Caso: Cocino algo no planificado
**Solución:**
- Ve a "Almacén"
- Resta manualmente los ingredientes usados

### Caso: Me sobran ingredientes de una comida anterior
**Solución:**
- Están en tu almacén
- La próxima lista los considerará como "disponibles"
- No te pedirá comprarlos de nuevo

### Caso: Quiero saber si tengo suficiente para mis planes
**Solución:**
- Genera la lista de compras
- Si está vacía → tienes todo lo necesario
- Si tiene items → necesitas comprar eso

---

## Errores Comunes

### Error: "No se pudo importar StockError"
**Causa:** Archivo routes.py desactualizado.
**Solución:** StockError todavía se usa para actualización manual de almacén. Verifica que esté importado en routes.py.

### Error: "Field 'ingredients_deducted' doesn't have a default value"
**Causa:** Base de datos no migrada.
**Solución:** Ejecuta `python migrate_to_virtual_batches.py`

### La lista de compras está vacía pero no tengo ingredientes
**Causa:** No hay comidas planificadas en el período seleccionado.
**Solución:** Verifica que hayas planificado comidas en las fechas de la lista.

### Los porcentajes no cuadran al eliminar platos
**Causa:** Bug o batches corruptos.
**Solución:** 
1. Verifica la tabla `dish_batches`
2. Ejecuta `MealService.cleanup_empty_batches()`
3. Si persiste, reporta el bug

---

## Comparación Técnica

### Antes: Al asignar plato
```python
# Verificaba stock
has_stock, insufficient = check_sufficient_stock(ingredients)
if not has_stock:
    raise StockError("Faltan ingredientes")

# Descontaba ingredientes
for ingredient in ingredients:
    update_stock(ingredient, quantity, 'subtract')

# Creaba batch con ingredients_deducted=True
batch = DishBatch(..., ingredients_deducted=True)
```

### Ahora: Al asignar plato
```python
# NO verifica stock
# NO descuenta ingredientes

# Crea batch virtual
batch = DishBatch(..., ingredients_deducted=False)

# Listo
```

### Lista de compras (sin cambios)
```python
# Calcula necesario
needed = calculate_ingredients_needed(start_date, end_date)

# Compara con disponible
for ingredient, quantity_needed in needed.items():
    available = get_stock(ingredient)
    to_buy = max(0, quantity_needed - available)
```

---

## Soporte

### ¿Dónde encuentro más documentación?
- `FILOSOFIA_PLANIFICACION.md` - Explicación completa
- `GUIA_NUEVA_FILOSOFIA.md` - Ejemplos de uso
- `RESUMEN_CAMBIOS_DICIEMBRE_2025.md` - Cambios técnicos

### ¿Cómo reporto un bug?
Crea un issue en el repositorio con:
1. Descripción del problema
2. Pasos para reproducir
3. Comportamiento esperado vs. actual
4. Logs o mensajes de error

### ¿Puedo contribuir?
Sí, los pull requests son bienvenidos. Asegúrate de:
1. Seguir el estilo de código existente
2. Documentar los cambios
3. Probar antes de enviar

---

## Resumen Rápido

✅ **Sí puedes:**
- Planificar sin tener ingredientes
- Cambiar planes sin afectar stock
- Generar múltiples listas
- Gestionar almacén manualmente

❌ **No puedes (todavía):**
- Marcar comidas como "consumidas" automáticamente
- Ver historial de consumo de ingredientes
- Alertas de stock bajo

🔜 **Futuro:**
- Función "Marcar como consumido"
- Reportes de consumo
- Sugerencias de platos según stock

---

**¿Más preguntas?** Consulta los documentos de ayuda o revisa el código en `services.py` y `models.py`.
