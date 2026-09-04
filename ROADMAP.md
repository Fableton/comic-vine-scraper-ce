# Roadmap

## Pendientes conocidos

- [ ] **Regresar al comic anterior desde la ventana de búsqueda de serie**:
  agregar la opción de volver al comic anterior (navegación hacia atrás)
  también desde la ventana de búsqueda de serie (`searchform.py`). Esta
  funcionalidad ya existe en la ventana de detalle de serie (`seriesform.py`);
  falta replicarla en la de búsqueda.

- [ ] **Ignorar Publishers desde las opciones**: agregar a la configuración
  del scraper (`configform.py` / `configuration.py`) la capacidad de marcar
  Publishers para ignorar, de forma que sea más fácil excluir editoriales de
  las que se sabe que no se tienen comics. Incluye:
  - Guardar en caché una lista de Publishers (para poblar el selector de
    cuáles ignorar) — no depender de pedirla de nuevo a la API cada vez.
  - En la lista de series (donde aparece el Publisher de cada resultado),
    filtrar/ocultar automáticamente las series cuyo Publisher esté en la
    lista de ignorados.
  - Agregar un menú contextual (clic derecho) sobre una serie/resultado en
    esa lista con la opción **"Ignorar Publisher"**, que agregue ese
    Publisher a la configuración de ignorados directamente desde ahí (sin
    tener que ir a las opciones manualmente).
