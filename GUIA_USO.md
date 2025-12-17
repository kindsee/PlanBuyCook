# Guía de Uso - PlanBuyCook

## 📋 Índice
1. [Instalación y Configuración](#instalación-y-configuración)
2. [Primeros Pasos](#primeros-pasos)
3. [Flujo de Trabajo Recomendado](#flujo-de-trabajo-recomendado)
4. [Funcionalidades Detalladas](#funcionalidades-detalladas)
5. [Preguntas Frecuentes](#preguntas-frecuentes)
6. [Solución de Problemas](#solución-de-problemas)

---

## 🚀 Instalación y Configuración

### 1. Requisitos del Sistema
- Python 3.10 o superior
- MariaDB 10.5 o superior
- 100 MB de espacio en disco

### 2. Instalación Paso a Paso

#### En Windows:
```powershell
# 1. Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear base de datos en MariaDB
mysql -u root -p < create_database.sql

# 4. Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales

# 5. Inicializar base de datos
python init_db.py

# 6. Ejecutar aplicación
python app.py
```

#### En Linux/Mac:
```bash
# 1. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Crear base de datos en MariaDB
mysql -u root -p < create_database.sql

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 5. Inicializar base de datos
python init_db.py

# 6. Ejecutar aplicación
python app.py
```

### 3. Configuración del Archivo .env
```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=planbuycook
DB_USER=tu_usuario
DB_PASSWORD=tu_contraseña

FLASK_SECRET_KEY=clave_secreta_segura
FLASK_ENV=development
```

---

## 🎯 Primeros Pasos

### Orden Recomendado de Configuración

#### 1. Crear Ingredientes Base
- Accede a "Ingredientes" → "Nuevo Ingrediente"
- Añade tus ingredientes más usados
- Define la unidad de medida correcta
- Establece un stock inicial si lo deseas

**Ejemplo:**
- Nombre: Arroz
- Unidad: g (gramos)
- Stock inicial: 1000

#### 2. Configurar el Almacén
- Accede a "Almacén"
- Revisa el stock de cada ingrediente
- Ajusta cantidades según tu despensa real
- Usa las opciones:
  - **Establecer**: Define cantidad exacta
  - **Añadir**: Suma al stock actual
  - **Restar**: Resta del stock actual

#### 3. Crear Platos
- Accede a "Platos" → "Nuevo Plato"
- Ingresa nombre y descripción
- Añade ingredientes con sus cantidades
- Ejemplo de plato "Arroz con Pollo":
  - 200 g de Arroz
  - 300 g de Pollo
  - 1 unidad de Cebolla
  - 2 unidades de Ajo

#### 4. Planificar Comidas
- Accede al "Calendario"
- Selecciona un día y comida
- Elige entre:
  - **Plato**: Asigna un plato (descuenta ingredientes)
  - **Pedir comida**: Marcador especial (no descuenta)
  - **Comer fuera**: Marcador especial (no descuenta)

---

## 🔄 Flujo de Trabajo Recomendado

### Flujo Semanal

1. **Domingo por la tarde:**
   - Planifica comidas para la semana siguiente
   - Genera lista de compra para 1 semana
   - Revisa qué ingredientes necesitas

2. **Lunes (compra):**
   - Imprime o lleva tu lista de compra
   - Compra los ingredientes
   - Marca la lista como "Completada" (añade al almacén automáticamente)

3. **Durante la semana:**
   - Consulta el calendario diario
   - El sistema descuenta ingredientes automáticamente
   - Ajusta si hay cambios de planes

4. **Viernes:**
   - Revisa stock restante en el almacén
   - Ajusta planificación del fin de semana si es necesario

### Flujo Mensual

1. **Principio de mes:**
   - Planifica comidas principales del mes
   - Genera lista de compra para 4 semanas
   - Identifica ingredientes de compra grande

2. **Semanalmente:**
   - Genera listas complementarias
   - Ajusta según productos frescos

---

## 📖 Funcionalidades Detalladas

### Calendario

#### Navegación
- **Semana Anterior/Siguiente**: Navega entre semanas
- **Semana Actual**: Vuelve a la semana en curso

#### Asignar Comidas
1. Click en "Asignar" en cualquier comida
2. Selecciona tipo:
   - **Plato**: El sistema verifica stock disponible
   - **Pedir comida**: No consume ingredientes
   - **Comer fuera**: No consume ingredientes
3. Si hay stock suficiente, se descuentan ingredientes automáticamente

#### Cambiar/Eliminar Comidas
- **Cambiar**: Los ingredientes del plato anterior se devuelven al almacén
- **Eliminar**: Los ingredientes se devuelven al almacén

### Gestión de Platos

#### Crear Plato
```
1. Ingresa nombre y descripción
2. Añade ingredientes uno por uno
3. Define cantidad para cada ingrediente
4. La unidad se muestra automáticamente
5. Puedes añadir múltiples ingredientes
6. Guarda el plato
```

#### Editar Plato
- Modifica nombre o descripción
- Añade/elimina ingredientes
- Ajusta cantidades
- **Nota**: Los cambios no afectan comidas ya planificadas

### Almacén Virtual

#### Operaciones de Stock

**Establecer Cantidad:**
```python
# Ejemplo: Tienes 1000g de arroz
Stock actual: 500g
Operación: Establecer 1000
Resultado: 1000g
```

**Añadir Cantidad:**
```python
# Ejemplo: Compras 500g más
Stock actual: 1000g
Operación: Añadir 500
Resultado: 1500g
```

**Restar Cantidad:**
```python
# Ejemplo: Usaste manualmente 200g
Stock actual: 1500g
Operación: Restar 200
Resultado: 1300g
```

#### Indicadores de Stock
- 🔴 **Rojo**: Stock agotado (0)
- 🟡 **Amarillo**: Stock bajo (< 100 unidades)
- 🟢 **Verde**: Stock suficiente (≥ 100 unidades)

### Lista de Compra

#### Cómo Funciona
1. Analizas comidas planificadas en período seleccionado
2. Calcula ingredientes totales necesarios
3. Compara con stock disponible
4. Genera lista con faltantes

#### Ejemplo de Cálculo
```
Período: 1 semana (7 días)
Comidas planificadas: 15 (algunas son "pedir/fuera")
Platos con ingredientes: 10

Ejemplo Arroz:
- Necesario total: 2000g (10 platos × 200g)
- Disponible en almacén: 1000g
- A comprar: 1000g ✓
```

#### Completar Lista
- Click en "Marcar como Completada"
- Confirma la acción
- Los ingredientes se añaden automáticamente al almacén
- La lista queda marcada como completada

---

## ❓ Preguntas Frecuentes

### P: ¿Qué pasa si intento planificar una comida sin stock suficiente?
**R**: El sistema mostrará un error indicando qué ingredientes faltan y cuánto. No se asignará la comida hasta que haya stock suficiente.

### P: ¿Puedo cambiar una comida ya planificada?
**R**: Sí. Los ingredientes del plato anterior se devuelven automáticamente al almacén.

### P: ¿"Pedir comida" consume ingredientes?
**R**: No. Ni "Pedir comida" ni "Comer fuera" afectan el stock del almacén.

### P: ¿Puedo generar múltiples listas de compra?
**R**: Sí. Puedes generar tantas listas como necesites para diferentes períodos.

### P: ¿Qué pasa si elimino un ingrediente usado en platos?
**R**: Se eliminarán también las relaciones en los platos. Hazlo con cuidado.

### P: ¿Puedo usar diferentes unidades de medida?
**R**: Sí. Al crear ingredientes, selecciona la unidad apropiada (g, kg, ml, l, unidades, etc.).

### P: ¿Cómo manejo productos por piezas vs peso?
**R**: Usa "unidades" para productos contables (huevos, manzanas) y "g/kg" para productos pesables (harina, arroz).

---

## 🔧 Solución de Problemas

### Error: "No se puede conectar a la base de datos"
**Solución:**
1. Verifica que MariaDB esté ejecutándose
2. Confirma credenciales en archivo `.env`
3. Verifica que la base de datos `planbuycook` existe

```bash
# Verificar servicio MariaDB
# Windows:
net start MySQL

# Linux:
sudo systemctl status mariadb
```

### Error: "Stock insuficiente"
**Solución:**
1. Ve al "Almacén"
2. Añade más stock del ingrediente faltante
3. Intenta asignar la comida nuevamente

### Error: "No hay platos disponibles"
**Solución:**
1. Primero crea ingredientes
2. Luego crea platos con esos ingredientes
3. Ahora podrás asignarlos en el calendario

### La lista de compra está vacía
**Posibles causas:**
1. No hay comidas planificadas en el período
2. El stock actual cubre todas las necesidades
3. Solo hay comidas "Pedir" o "Comer fuera"

**Solución:**
1. Planifica más comidas con platos
2. Verifica el período seleccionado
3. Genera lista para período más largo

### Los ingredientes no se descuentan
**Causa:** El campo `ingredients_deducted` está en True

**Solución:**
```python
# Reiniciar base de datos
python init_db.py
```

---

## 📞 Soporte

Para problemas técnicos o sugerencias, revisa:
1. Este documento de guía
2. El archivo README.md
3. Los comentarios en el código fuente
4. La documentación de Flask: https://flask.palletsprojects.com/

---

## 📝 Notas Importantes

1. **Backup Regular**: Exporta tu base de datos regularmente
2. **Stock Real**: Mantén el almacén actualizado con tu despensa real
3. **Planificación**: Planifica con al menos 3-4 días de antelación
4. **Listas Antiguas**: Puedes eliminar listas completadas antiguas

---

## 🎉 Consejos de Uso

- Usa "Pedir comida" y "Comer fuera" para tener un calendario completo
- Crea platos variantes (ej: "Arroz con Pollo Light" con menos aceite)
- Agrupa compras semanales para ahorrar tiempo
- Revisa el stock antes de generar listas de compra
- Imprime las listas para llevar al supermercado

---

**¡Disfruta planificando tus comidas con PlanBuyCook! 🍽️**
