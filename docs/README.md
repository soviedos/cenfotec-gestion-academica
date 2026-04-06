# Documentación — Evaluaciones Docentes

> Índice centralizado de toda la documentación técnica del proyecto.

---

## Documentos Disponibles

| Documento                                        | Descripción                                                             | Audiencia                          |
| ------------------------------------------------ | ----------------------------------------------------------------------- | ---------------------------------- |
| [architecture.md](architecture.md)               | Arquitectura del sistema, diagrama de componentes y decisiones técnicas | Desarrolladores, Arquitectos       |
| [data-model.md](data-model.md)                   | Modelo de datos: esquema ER, tablas, columnas, índices, migraciones     | Desarrolladores Backend, DBA       |
| [processing-pipeline.md](processing-pipeline.md) | Flujo de procesamiento: upload → parseo → clasificación → persistencia  | Desarrolladores Backend            |
| [gemini-integration.md](gemini-integration.md)   | Integración con Gemini API: RAG, prompts, auditoría, manejo de errores  | Desarrolladores Backend            |
| [testing-strategy.md](testing-strategy.md)       | Estrategia de testing: pirámide, fixtures, herramientas, convenciones   | Todo el equipo de desarrollo       |
| [local-development.md](local-development.md)     | Guía de desarrollo local: setup, comandos, troubleshooting              | Nuevos desarrolladores             |
| [deployment.md](deployment.md)                   | Guía de despliegue on-premise con Docker Compose + Nginx                | DevOps, Administradores            |
| [api-contracts.md](api-contracts.md)             | Especificación de endpoints de la API REST (request/response)           | Desarrolladores Frontend y Backend |
| [adr/](adr/)                                     | Registros de decisiones arquitectónicas (ADR)                           | Todo el equipo                     |

---

## Architecture Decision Records (ADR)

Los ADR documentan el **porqué** de cada decisión técnica significativa. Seguimos el formato [MADR](https://adr.github.io/madr/).

| ADR                                                | Título                                        | Estado   |
| -------------------------------------------------- | --------------------------------------------- | -------- |
| [001](adr/001-monorepo.md)                         | Usar monorepo para frontend + backend         | Aceptada |
| [002](adr/002-nextjs-frontend.md)                  | Next.js como framework frontend               | Aceptada |
| [003](adr/003-fastapi-backend.md)                  | FastAPI como framework backend                | Aceptada |
| [004](adr/004-postgresql-fuente-verdad.md)         | PostgreSQL como fuente de verdad              | Aceptada |
| [005](adr/005-parser-deterministico-pdf.md)        | Parser determinístico para extracción de PDFs | Aceptada |
| [006](adr/006-gemini-solo-analisis-cualitativo.md) | Gemini API solo para análisis cualitativo     | Aceptada |

Para crear un nuevo ADR, copiar la plantilla y usar el siguiente número consecutivo:

```bash
cp docs/adr/001-monorepo.md docs/adr/NNN-titulo-descriptivo.md
```

---

## Convenciones de Documentación

- Escribir en **español** (código y variables en inglés)
- Usar Markdown estándar compatible con GitHub
- Incluir diagramas en formato ASCII o Mermaid cuando sea posible
- Actualizar este índice al agregar nuevos documentos
- Los documentos deben incluir fecha de última actualización

---

## Pendientes de Documentación

- [x] ~~Modelo de datos y diagrama ER~~ → [data-model.md](data-model.md)
- [x] ~~Guía de integración con Gemini API~~ → [gemini-integration.md](gemini-integration.md)
- [ ] Guía de onboarding para nuevos desarrolladores
- [ ] Runbook de operaciones y troubleshooting
