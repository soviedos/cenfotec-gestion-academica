# Shared Kernel

Código transversal reutilizado por todos los módulos de la plataforma.

## Contenido

| Carpeta                        | Responsabilidad                                                                       |
| ------------------------------ | ------------------------------------------------------------------------------------- |
| `core/`                        | Settings, cache (Redis), logging                                                      |
| `domain/entities/`             | `Base`, `UUIDMixin`, `TimestampMixin`                                                 |
| `domain/exceptions.py`         | Excepciones base: `DomainError`, `NotFoundError`, `DuplicateError`, `ValidationError` |
| `domain/schemas/`              | `BaseSchema`, `TimestampSchema`, `PaginatedItems`, `HealthResponse`, `ErrorResponse`  |
| `infrastructure/database/`     | Engine async, session factory (`get_db`)                                              |
| `infrastructure/repositories/` | `BaseRepository` genérico (CRUD)                                                      |
| `infrastructure/storage/`      | `FileStorage` protocol, `MinioFileStorage`                                            |
| `infrastructure/tasks/`        | Instancia de Celery                                                                   |

## Regla de dependencia

`shared/` **nunca** importa de `app/modules/*`.
Los módulos importan de `shared/` para heredar bases y reutilizar infraestructura.
Las excepciones específicas de cada módulo (e.g. `ModalidadRequeridaError`, `GeminiError`)
viven en `app/modules/<módulo>/domain/exceptions.py` y extienden las bases de `shared`.
