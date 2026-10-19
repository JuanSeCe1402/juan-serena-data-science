"""Principios y proyectos públicos de WUNSCE; el lore futuro permanece en docs/UNIVERSO.md."""

CHARACTERS = [{'slug': 'wus',
  'name': 'Wus',
  'title': 'El Mago',
  'verb': 'Imagina',
  'origin': 'Personaje original de WUNSCE: el deseo, la posibilidad y la imaginación '
            'aplicada.',
  'story': 'Wus viaja porque desea conocer lo que hay detrás del horizonte. Ante una puerta '
           'cerrada, imagina otra entrada. Cada encuentro amplía las herramientas con las que '
           'puede crear.',
  'business': 'Exploración, prototipos, diseño de soluciones y visión de producto. Hace '
              'visible lo que comienza como una idea, acompañado siempre por el criterio de '
              'Wis.',
  'principle': 'Primero imagina lo que puede existir.',
  'symbol': '✦'},
 {'slug': 'wis',
  'name': 'Wis',
  'title': 'El Sabio',
  'verb': 'Comprende',
  'origin': 'Personaje original de WUNSCE: la elección, el entendimiento y el criterio.',
  'story': 'Donde Wus ve diez caminos, Wis busca cuál conserva lo importante. Su fuerza está '
           'en reconocer la pregunta que todavía falta hacer.',
  'business': 'Diagnóstico, arquitectura, priorización y análisis de procesos. Distingue '
              'entre una solución brillante y una solución útil.',
  'principle': 'Antes de construir, entiende.',
  'symbol': '◉'},
 {'slug': 'nana',
  'name': 'Nana',
  'title': 'La Portadora de la Luz',
  'verb': 'Estructura',
  'origin': 'Inspirada respetuosamente en Nanahuatzin, figura de la tradición nahua/mexica '
            'asociada con humildad, sacrificio y transformación luminosa.',
  'story': 'Ante una montaña de fragmentos sin nombre, Nana no los desecha. Los ordena y '
           'compara hasta revelar un dibujo. No inventa información: permite ver la '
           'estructura que ya estaba allí.',
  'business': 'Preparación y transformación de datos: perfiles, limpieza, duplicados, '
              'faltantes, normalización, calidad y salidas listas para analizar.',
  'principle': 'Lo que parece ruido puede contener una estructura.',
  'symbol': '◈'},
 {'slug': 'tikal',
  'name': 'Tikal',
  'title': 'La Ciudad que Recuerda',
  'verb': 'Organiza',
  'origin': 'Inspirada en Tikal, la gran ciudad maya histórica. Evoca organización, '
            'coordinación y memoria de una operación compleja.',
  'story': 'Tikal es una ciudad que habla. Cada plaza representa un proceso y cada camino, '
           'una dependencia. Enseña que un edificio aislado no basta para que toda la ciudad '
           'funcione.',
  'business': 'Clientes, pedidos, inventario, tareas y estados compartidos. Hace visible la '
              'operación para que distintas actividades puedan trabajar juntas.',
  'principle': 'Una operación invisible no puede mejorarse.',
  'symbol': '▥'},
 {'slug': 'frey',
  'name': 'Frey',
  'title': 'El Custodio de la Prosperidad',
  'verb': 'Mide',
  'origin': 'Inspirado en Freyr, también llamado Frey en formas adaptadas, figura de la '
            'mitología nórdica vinculada con prosperidad, fertilidad y abundancia.',
  'story': 'En una tierra fértil que empieza a agotarse, Frey enseña a conocer el costo de '
           'cada cosecha. No rechaza el crecimiento: lo vuelve medible para que pueda '
           'sostenerse.',
  'business': 'Costos directos e indirectos, márgenes, precios, escenarios y cotizaciones. '
              'Tikal muestra lo que ocurre; Frey revela el valor que produce y a qué costo.',
  'principle': 'El ingreso no es prosperidad si el costo permanece invisible.',
  'symbol': '↗'},
 {'slug': 'darwin',
  'name': 'Darwin',
  'title': 'El Observador de la Adaptación',
  'verb': 'Aprende',
  'origin': 'Inspirado en Charles Darwin y en la idea científica de adaptación mediante '
            'variación, selección y cambio a lo largo del tiempo.',
  'story': 'Darwin invita a observar antes de inferir. Enseña que adaptarse a condiciones '
           'cambiantes exige reconocer patrones y desconfiar de una predicción que oculta su '
           'incertidumbre.',
  'business': 'Aprendizaje automático, clasificación, predicción y evaluación de modelos con '
              'métricas y límites claros. Nana prepara la información; Darwin aprende de '
              'ella.',
  'principle': 'Predecir no es adivinar: es medir patrones y reconocer incertidumbre.',
  'symbol': '✧'},
 {'slug': 'esculapio',
  'name': 'Esculapio',
  'title': 'El Guardián del Cuidado',
  'verb': 'Cuida',
  'origin': 'Inspirado en Asclepio/Esculapio, figura grecorromana asociada históricamente con '
            'la medicina y el cuidado.',
  'story': 'Esculapio no entrega una cura mágica. Enseña que cuidar también es ordenar, '
           'conservar contexto y reconocer cuándo una persona debe tomar el control.',
  'business': 'Presencia profesional, agenda, recordatorios y comunicación administrativa del '
              'consultorio. Su función es operativa; no sustituye al profesional ni al '
              'criterio clínico.',
  'principle': 'La tecnología debe dejar más espacio para cuidar.',
  'symbol': '✚'}]

CHARACTERS_BY_SLUG = {c["slug"]: c for c in CHARACTERS}
