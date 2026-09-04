# Changelog

Resumen funcional de los cambios de este fork (comic-vine-scraper-ce),
a partir de donde diverge de
[cbanack/comic-vine-scraper](https://github.com/cbanack/comic-vine-scraper)
v1.0.102.

## [1.1.0-ce] - Unreleased

- Se agregó un botón "Previous Comic" en la ventana de selección de serie,
  igual al que ya existía en la de selección de issue, para poder
  regresar y re-hacer el comic anterior si se eligió la serie equivocada.
- Se corrigió que el diálogo de error genérico no se mostrara cuando
  ocurría un error inesperado (no relacionado a la base de datos) durante
  el scraping o al abrir la configuración -- antes fallaba en silencio,
  sin avisar al usuario.
- Se corrigió que el botón "Configurar..." del plugin no hiciera nada:
  ComicRack estaba cargando por error una copia sin construir del script
  (desde el submódulo fuente); ahora solo carga la copia empaquetada real.
- Se agregó un `ROADMAP.md` para llevar seguimiento de los pendientes
  conocidos de este fork.

## [1.0.102-ce2] - 2026-09-01

- Se restauraron personalizaciones visuales (layouts responsive con
  TableLayoutPanel) en varias ventanas que se habían perdido al crear
  el submódulo.
- Se agregó un botón "Search" junto al campo de número de issue a
  previsualizar, y se mejoró el espaciado entre los filtros y las tablas
  en las ventanas de selección de serie/issue.
- Se automatizó la generación de releases (GitHub Actions) al crear un
  tag, sin depender de tener Ant/ipy.exe instalados localmente.

## [1.0.102-ce1] - 2026-09-01

- Se agregó búsqueda y filtros (por Serie/Año/Issues/Publisher) con
  ordenamiento multi-columna en la tabla de selección de series, y
  filtros equivalentes (con columnas Año/Mes) en la de selección de
  issues.
- Se ajustaron los elementos estáticos de los formularios de selección
  de serie e issue para que el layout sea responsive y se adapte a
  resoluciones mayores (antes tenían tamaño y posición fijos).
- Se agregó un campo editable para forzar el número de issue a buscar,
  un combobox con historial de las últimas 20 búsquedas, cache en disco
  (24h) para la lista de issues de una serie, y un botón "Previous
  Comic" en la ventana de selección de issue.
- Se corrigió Ctrl+Backspace en los nuevos campos de filtro/combobox.
- Se documentaron los cambios de este fork en el README, y se agregó un
  script de build en PowerShell que no depende de Ant/ipy.exe.
