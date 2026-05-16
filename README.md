# mydron-cli

CLI local para comunicarse con una controladora INAV por USB/MSP.

## Instalacion rapida

Desde PowerShell:

```powershell
cd D:\MyDron\mydron-cli
.\.venv\Scripts\Activate.ps1
pip install -e .
```

El comando queda disponible dentro del entorno virtual como:

```powershell
mydron --help
```

Tambien se puede ejecutar sin activar el entorno:

```powershell
D:\MyDron\mydron-cli\.venv\Scripts\mydron.exe --help
```

El proyecto incluye un lanzador Windows:

```powershell
D:\MyDron\mydron-cli\bin\mydron.cmd --help
```

Para usar `mydron` desde cualquier terminal, anade al PATH una de estas carpetas:

- `D:\MyDron\mydron-cli\.venv\Scripts`
- `D:\MyDron\mydron-cli\bin`

## Comandos

- listar puertos serie

```powershell
mydron ports
```

- leer informacion basica de INAV por MSP

```powershell
mydron info --port COM5
```

- leer estado basico por MSP

```powershell
mydron status --port COM5
```

- crear un backup completo de la configuracion por CLI textual INAV

```powershell
mydron dump-cli --port COM5 --out backups\inav-dump.txt
```

- ejecutar un comando de la CLI textual de INAV

```powershell
mydron cli --port COM5 status
```

## Seguridad

No se han implementado comandos de armado, motores ni RC. Esta herramienta esta pensada
para empezar en modo lectura y backup.

Antes de trabajar con una controladora real:

- quita las helices
- no conectes LiPo si no es necesaria
- cierra INAV Configurator antes de usar esta CLI
- haz siempre un `dump-cli` antes de cambiar configuracion

## Documentacion

- [Como funciona el proyecto](docs/COMO_FUNCIONA.md)
- [Como se crean CLIs Python y como instalarlas en el PATH de Windows](docs/CREAR_CLIS_WINDOWS.md)
- [Estudio de comandos CLI INAV en este dron](docs/INAV_CLI_COMMANDS.md)

## Skill Codex

El repo incluye la skill reutilizable en:

```text
skills\mydron-inav
```

Esa skill contiene los flujos de trabajo seguros para detectar el puerto USB,
hacer backups dentro de `D:\MyDron`, usar `mydron cli`, planificar cambios de
configuracion y diagnosticar motores/servos con barreras de seguridad.
