-- =========================GSCELLY==============================================
-- AWS Athena SQL Queries para el Data Lake de Canvas LMS
-- Tabla particionada: canvas_courses_parquet
-- ==============================================================================

-- 1. Distribución de cursos por estado (Visión general de la plataforma)
-- Nos permite ver el volumen de cursos activos frente a los no publicados o borrados.
SELECT 
    estado,
    COUNT(course_id) AS total_cursos
FROM 
    canvas_courses_parquet
GROUP BY 
    estado
ORDER BY 
    total_cursos DESC;

-- 2. Auditoría de Integración ERP (Cursos sin SIS ID)
-- Vital para asegurar que todos los cursos de la subcuenta principal (ej. 1) 
-- estén sincronizados correctamente con el sistema académico (Banner, etc.).
SELECT 
    course_id,
    course_name,
    course_code,
    created_at
FROM 
    canvas_courses_parquet
WHERE 
    sis_course_id IS NULL 
    AND subaccount_id = 1
    AND estado = 'available'
ORDER BY 
    created_at DESC;

-- 3. Análisis de Adopción (Cursos creados recientemente por Subcuenta)
-- Cruza la jerarquía de la institución para ver qué facultades están creando más cursos.
SELECT 
    subaccount_id,
    COUNT(course_id) AS nuevos_cursos_este_mes
FROM 
    canvas_courses_parquet
WHERE 
    created_at >= date_trunc('month', current_date)
GROUP BY 
    subaccount_id
ORDER BY 
    nuevos_cursos_este_mes DESC;

-- 4. Validación del Pipeline ETL
-- Confirma la frescura de los datos revisando cuándo fue la última transformación de Glue.
SELECT 
    MAX(etl_processed_at) AS ultima_actualizacion_lakehouse,
    COUNT(DISTINCT course_id) AS total_cursos_procesados
FROM 
    canvas_courses_parquet;