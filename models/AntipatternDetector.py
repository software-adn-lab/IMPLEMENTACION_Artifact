import re

AntiPatrones = {
    # El poner la r hace que Python no intente interpretar los caracteres de escape.
    # Esto es util para regex, porque los toma literalmente y no como caracteres especiales.
    "BLOB": [
        r"(LCH|LCS)",
        r"(CC|CM)",
        r"DC"
    ],
    "SwissArmyKnife": [
        r"MI"
    ],
    "FunctionalDecomposition": [
        r"FP",
        r"COM",
        r"PN"
        ,r"NP"
        ,r"NI"
    ],
    "SpaghettiCode": [
        r"LM",
        r"MNP",
        r"CGV",
        r"NI",
        r"NP"
    ]
}


def DetectAntipattern(relatedSmellsMoha):
    resultados = {}
    detallePorSmell = {}

    for antipatron in AntiPatrones:
        detallePorSmell[antipatron] = []
        totalCondiciones = len(AntiPatrones[antipatron])
        cumplidas = []
        smellsEncontrados = 0
        
        for regla in AntiPatrones[antipatron]:
            reglaEncontrada = False
            # Busca si la expresion regular aparece en la lista de olores relacionados.
            
            for smell in relatedSmellsMoha:
                if re.fullmatch(regla, smell['moha_smell']):
                    detallePorSmell[antipatron].append({
                        'moha_smell': smell['moha_smell'],
                        'sonar_rule': smell.get('sonar_rule', 'N/A'),
                        'metric_name': smell.get('metric_name'),
                        'source': smell.get('source', 'sonar'),
                        'line': smell.get('line'),
                        'severity': smell.get('severity', 'MAJOR'),
                        'component': smell.get('component'),
                        'archivo_clase': _extraer_archivo_clase(smell.get('component')),
                        'issue_key': smell.get('issue_key'),
                        'project': smell.get('project'),
                        'textRange': smell.get('textRange')
                    })
                    reglaEncontrada = True
                    smellsEncontrados += 1


            if reglaEncontrada:

                cumplidas.append(regla)
                        
            
        
        # Determinar confianza del antipatron.
        if len(cumplidas) == totalCondiciones:
            detectado = 'The antipattern is detected because all conditions are met (Moha Smells).'
        elif len(cumplidas) >= totalCondiciones / 2:
            detectado = 'The antipattern is likely present because at least half of the conditions are met (Moha Smells).'
        else:
            detectado = 'The antipattern is not detected because fewer than half of the conditions are met (Moha Smells).'

        resumen_archivos = _evaluar_antipatron_por_archivo(
            detallePorSmell[antipatron],
            AntiPatrones[antipatron]
        )
        archivos_con_antipatron = [
            x['archivo_clase'] for x in resumen_archivos if x['antipatron_detectado']
        ]
        
        # Guardar resultados independientes por antipatron.
        resultados[antipatron] = {
            'condiciones_totales': totalCondiciones,
            'condiciones_cumplidas': len(cumplidas),
            'detalle_condiciones_cumplidas': cumplidas,
            'total_ocurrencias': smellsEncontrados,
            'detectado': detectado,
            'detalle_smells': detallePorSmell[antipatron],
            'resumen_archivos': resumen_archivos,
            'archivos_con_antipatron': archivos_con_antipatron
        }
        
        # print(f"Resultados para {antipatron}:")
        # print(f"Se cumplieron {cumplidas} de {totalCondiciones} condiciones.")
        # print(f"Se encontraron {smellsEncontrados} olores de codigo en total.")
        # print("-" * 20)


    return resultados

def _extraer_archivo_clase(component):
    if not component:
        return "N/A"

    # Soporta rutas con / o \\ y devuelve el nombre del archivo.
    partes = re.split(r"[\\/]", str(component))
    return partes[-1] if partes and partes[-1] else str(component)


def _evaluar_antipatron_por_archivo(detalle_smells, reglas):
    if not detalle_smells:
        return []

    detalles_por_archivo = {}
    for smell in detalle_smells:
        archivo = smell.get("archivo_clase", "N/A")
        detalles_por_archivo.setdefault(archivo, []).append(smell)

    resultado_archivos = []
    total_reglas = len(reglas)

    for archivo, smells_archivo in detalles_por_archivo.items():
        reglas_cumplidas = []

        for regla in reglas:
            if any(re.fullmatch(regla, s.get("moha_smell", "")) for s in smells_archivo):
                reglas_cumplidas.append(regla)

        resultado_archivos.append({
            "archivo_clase": archivo,
            "condiciones_totales": total_reglas,
            "condiciones_cumplidas": len(reglas_cumplidas),
            "detalle_condiciones_cumplidas": reglas_cumplidas,
            "antipatron_detectado": len(reglas_cumplidas) == total_reglas
        })

    resultado_archivos.sort(
        key=lambda x: (x["condiciones_cumplidas"], x["archivo_clase"]),
        reverse=True
    )
    return resultado_archivos
