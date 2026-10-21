{
  id: 'a8',
  title: '¿Su institución construye islas de IA o un ecosistema de inteligencia?',
  subtitle: 'Autoevaluación ejecutiva · 16 preguntas · 8 minutos',
  desc: '16 preguntas para juntas y comités ejecutivos de bancos, cooperativas y aseguradoras. Descubra si sus capacidades de IA comparten datos, objetivos y gobierno, o si operan como proyectos aislados.',
  icon: '<svg width="32" height="32" viewBox="0 0 32 32" fill="none" style="pointer-events:none"><circle cx="16" cy="8" r="3" stroke="#00C0DC" stroke-width="1.5" fill="none"/><circle cx="8" cy="22" r="3" stroke="#00C0DC" stroke-width="1.5" fill="none"/><circle cx="24" cy="22" r="3" stroke="#00C0DC" stroke-width="1.5" fill="none"/><path d="M14 10.5L10 19.5M18 10.5L22 19.5M11 22h10" stroke="#00C0DC" stroke-width="1.5" stroke-linecap="round"/></svg>',
  type: 'yesno',
  groups: [
    {
      label: 'Visibilidad — Inventario y responsabilidad',
      questions: [
        '¿Existe un inventario único de todos los modelos, reglas y agentes de IA en uso, incluido el uso informal de herramientas por los empleados?',
        '¿Cada sistema de IA tiene un dueño de negocio responsable de sus resultados, además de un responsable técnico?'
      ]
    },
    {
      label: 'Integración — Flujos y trazabilidad',
      questions: [
        '¿Al menos un proceso de negocio (crédito, fraude, cobranza o siniestros) combina IA predictiva, reglas, generativa y agentes en un mismo flujo?',
        '¿Puede reconstruir de punta a punta cualquier decisión automatizada, incluidos todos los sistemas que intervinieron?'
      ]
    },
    {
      label: 'Datos — Calidad y acceso compartido',
      questions: [
        '¿Los modelos y agentes usan datos compartidos con dueño, calidad medida y linaje, en lugar de copias por proyecto?',
        '¿Puede incorporar datos externos (Open Finance, burós, datos alternativos) sin construir una integración a la medida cada vez?'
      ]
    },
    {
      label: 'Identidad y seguridad — Permisos de agentes',
      questions: [
        '¿Cada agente de IA tiene identidad propia, permisos mínimos y credenciales que se rotan?',
        '¿Su equipo de seguridad puede responder hoy qué sistemas y datos puede alcanzar cada agente?'
      ]
    },
    {
      label: 'Autonomía y supervisión — Gobierno operativo',
      questions: [
        '¿Están aprobados por escrito los niveles de autonomía de cada agente, con umbrales de monto e impacto que obligan a escalar a una persona?',
        '¿Existe un rol formal de supervisión de agentes con autoridad para detener su operación?'
      ]
    },
    {
      label: 'Valor — Medición financiera',
      questions: [
        '¿Finanzas mide el impacto de la IA en resultados (EBIT, costo por decisión, pérdida evitada) contra una línea base previa?',
        '¿Cada nuevo caso de IA cuesta menos que el anterior porque reutiliza plataforma, datos y controles?'
      ]
    },
    {
      label: 'Gobierno — Política y marcos regulatorios',
      questions: [
        '¿La junta o el consejo aprobó una política de IA y recibe reportes de riesgo de IA con la misma periodicidad que otros riesgos?',
        '¿Aplica un marco reconocido (NIST AI RMF o ISO/IEC 42001) aunque el regulador local aún no lo exija?'
      ]
    },
    {
      label: 'Arquitectura — Orquestación y apertura',
      questions: [
        '¿Existe una capa común de orquestación o un estándar de integración que todo nuevo caso de IA debe usar?',
        '¿Podría exponer servicios de forma segura a los agentes de IA de sus clientes corporativos o socios?'
      ]
    }
  ],
  bands: [
    {
      min: 0,
      max: 6,
      label: 'Capacidades aisladas',
      desc: 'Proyectos independientes: cada caso nuevo cuesta más que el anterior y nadie ve la cadena completa de decisiones. Próximo paso: inventario, política de junta y línea base en seis meses.'
    },
    {
      min: 7,
      max: 12,
      label: 'Ecosistema emergente',
      desc: 'Piezas conectadas sin gobierno transversal; los riesgos entre sistemas no tienen dueño. Próximo paso: identidad para cada agente y un flujo de extremo a extremo con valor medido por Finanzas.'
    },
    {
      min: 13,
      max: 16,
      label: 'Ecosistema de inteligencia',
      desc: 'Capacidades conectadas y gobernadas, listas para escalar sistemas multiagente y abrir un canal seguro a los agentes de sus clientes. Próximo paso: graduar la autonomía por flujo.'
    }
  ]
}
