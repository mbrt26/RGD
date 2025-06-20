# 🧪 Guía de Validación - Módulo de Proyectos
## Sesiones 3 y 4 - Funcionalidades Completas

---

## 📊 **Datos Generados para Pruebas**

### **Proyectos Creados: 12**
- **Pendientes**: 6 proyectos
- **En Ejecución**: 4 proyectos  
- **Finalizados**: 2 proyectos

### **Colaboradores: 13**
- Directores, Ingenieros, Técnicos, Coordinadores

### **Bitácoras: 120**
- **Planeadas**: 33 (22 requieren registro urgente)
- **En Proceso**: 26
- **Completadas**: 27 (con firmas digitales)
- **Canceladas**: 34

### **Prórrogas: 9**
- Estados: Solicitada, Aprobada, Rechazada, Aplicada

---

## 🔍 **Funcionalidades a Validar**

### **🟢 SESIÓN 3: Fechas, Prórrogas y Control Temporal**

#### **1. Control de Tiempo y Retrasos**
📍 **URL**: `http://127.0.0.1:8000/proyectos/proyectos/`

**Validar:**
- ✅ Columna "% Avance Planeado" vs "% Avance Real"
- ✅ **Badges rojos** cuando avance real < avance planeado (9 proyectos afectados)
- ✅ **6 proyectos con retraso temporal** visible en la lista
- ✅ Indicadores de días de retraso
- ✅ Semáforos de estado del proyecto

#### **2. Módulo de Prórrogas**
📍 **URL**: `http://127.0.0.1:8000/proyectos/prorrogas/`

**Validar:**
- ✅ Lista de 9 prórrogas con diferentes estados
- ✅ Crear nueva prórroga
- ✅ Workflow de aprobación
- ✅ Cálculo automático de días de extensión
- ✅ Impacto en presupuesto

#### **3. Cálculo Automático de Fechas**
📍 **URL**: `http://127.0.0.1:8000/proyectos/proyectos/nuevo/`

**Validar:**
- ✅ Al cambiar fecha inicio + días prometidos → fecha fin se actualiza automáticamente
- ✅ JavaScript funcionando para cálculos en tiempo real

---

### **🔵 SESIÓN 4: Presupuestos y Bitácoras Avanzadas**

#### **1. Control Presupuestario Avanzado**
📍 **URL**: `http://127.0.0.1:8000/proyectos/proyectos/`

**Validar:**
- ✅ Columna "% Ejecución Presupuesto"
- ✅ **Badges rojos** cuando ejecución > avance real (7 proyectos afectados)
- ✅ Columna "Gastado" con valores monetarios
- ✅ Columna "Control Financiero" con disponible
- ✅ Indicadores de riesgo de sobrecosto

#### **2. Bitácoras con Funcionalidades Avanzadas**
📍 **URL**: `http://127.0.0.1:8000/proyectos/bitacora/`

**Validar:**
- ✅ **22 filas rojas** (bitácoras que requieren registro urgente)
- ✅ Filas amarillas (planeadas normales)
- ✅ Filas verdes (completadas)
- ✅ Información de líder de trabajo y equipo
- ✅ Estados de validación digital

#### **3. Formulario de Bitácora Completo**
📍 **URL**: `http://127.0.0.1:8000/proyectos/bitacora/1/editar/`

**Validar:**
- ✅ **Sección "Equipo de Trabajo"** (Badge Sesión 4)
  - Campo Líder de Trabajo
  - Selección múltiple de Equipo
- ✅ **Sección "Control Temporal"** (Badge Sesión 4)
  - Fecha Planificada (date picker)
  - Fecha Ejecución Real
  - Duración en horas
- ✅ **Sección "Estado y Validación"** (Badge Sesión 4)
  - Estado de actividad
  - Estado de validación
- ✅ **Sección "Firmas Digitales"** (Solo en edición)
  - Estado de firma director
  - Estado de firma ingeniero
  - Metadata completa (IP, dispositivo, fecha)

#### **4. Sistema de Firmas Digitales**
📍 **URL**: Bitácoras completadas con validación

**Validar:**
- ✅ 120 bitácoras tienen firmas digitales
- ✅ Información de IP y dispositivo registrada
- ✅ Workflow de validación por director e ingeniero
- ✅ Estados: pendiente → validada_director → validada_completa

---

## 🎯 **Casos de Prueba Específicos**

### **Caso 1: Proyecto con Problemas de Avance**
```
Buscar proyectos con badge rojo en "% Avance Real"
→ Verificar que avance real < avance planeado
→ Confirmar alerta visual funcionando
```

### **Caso 2: Proyecto con Sobreejecución Presupuestaria**
```
Buscar proyectos con badge rojo en "% Ejecución Presupuesto"  
→ Verificar que ejecución > avance real
→ Confirmar indicador de sobreejecución
```

### **Caso 3: Bitácora Urgente**
```
Ir a lista de bitácoras
→ Identificar 22 filas rojas
→ Verificar que son bitácoras "planeadas" atrasadas
→ Confirmar badges de urgencia
```

### **Caso 4: Formulario Completo de Bitácora**
```
Editar cualquier bitácora
→ Verificar 6 secciones organizadas
→ Confirmar campos de Sesión 4 presentes
→ Validar información de firmas digitales
```

### **Caso 5: Crear Nueva Prórroga**
```
Seleccionar proyecto en ejecución
→ Crear nueva prórroga
→ Verificar cálculo automático de días
→ Probar workflow de aprobación
```

---

## 🚨 **Alertas a Validar**

### **Alertas Rojas (Críticas)**
- ✅ **9 proyectos** con avance real < planeado
- ✅ **7 proyectos** con sobreejecución presupuestaria  
- ✅ **22 bitácoras** requieren registro urgente
- ✅ **6 proyectos** con retraso temporal

### **Indicadores Visuales**
- ✅ Badges rojos pulsantes para alertas
- ✅ Semáforos de estado de proyecto
- ✅ Color-coding en filas de bitácoras
- ✅ Iconos FontAwesome diferenciados

---

## 📋 **Checklist de Validación**

### **Lista de Proyectos**
- [ ] Columnas reorganizadas (13 columnas)
- [ ] Badges rojos funcionando
- [ ] Información presupuestaria visible
- [ ] Alertas de retraso mostradas
- [ ] Responsive design funcional

### **Formulario de Proyectos**
- [ ] Cálculo automático de fechas
- [ ] Campos presupuestarios
- [ ] Validaciones funcionando

### **Lista de Bitácoras**  
- [ ] Color-coding por estado
- [ ] Información de equipos
- [ ] Estados de validación
- [ ] Alertas de urgencia

### **Formulario de Bitácoras**
- [ ] 6 secciones organizadas
- [ ] Campos de Sesión 4 presentes
- [ ] Información de firmas
- [ ] Validaciones funcionando

### **Módulo de Prórrogas**
- [ ] CRUD completo
- [ ] Workflow de aprobación
- [ ] Cálculos automáticos
- [ ] Impacto en proyecto

---

## 🎉 **Resultado Esperado**

Al completar esta validación, habrás verificado que:

✅ **Sesión 3** - Control temporal y prórrogas completamente funcional
✅ **Sesión 4** - Control presupuestario y bitácoras avanzadas operativo
✅ **120 bitácoras** con todas las funcionalidades implementadas
✅ **Alertas visuales** funcionando correctamente
✅ **Formularios** completamente actualizados
✅ **Sistema robusto** listo para producción

---

### 📞 **Soporte**
Si encuentras algún problema durante la validación, verifica:
1. Servidor Django ejecutándose
2. Migraciones aplicadas
3. Template tags cargados
4. Datos de prueba generados correctamente