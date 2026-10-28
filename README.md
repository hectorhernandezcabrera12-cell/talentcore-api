# TalentCore API

API REST para gestión de talento construida con FastAPI y SQLite.

## Desarrollo Local

Instala dependencias y ejecuta el servidor:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

Ejecuta la suite de pruebas:

```bash
pytest -v
```

## Docker

Construye y levanta el contenedor:

```bash
docker compose up --build
```

## Endpoints

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/` | Salud del servicio |
| `GET` | `/talents` | Lista de talentos |
| `POST` | `/talents` | Crea un talento |
| `GET` | `/talents/{id}` | Detalle de un talento |
| `DELETE` | `/talents/{id}` | Elimina un talento |