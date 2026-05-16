# Como se crean CLIs Python y como instalarlas en el PATH de Windows

Una CLI es un programa que se ejecuta desde una terminal con un comando de texto.
En este proyecto el comando es:

```powershell
mydron
```

## 1. Crear un proyecto Python

La estructura recomendada es:

```text
mi-cli/
  pyproject.toml
  src/
    paquete/
      __init__.py
      __main__.py
      cli.py
```

El codigo vive dentro de `src/paquete`. Esto evita importaciones accidentales
desde la carpeta de trabajo y se parece a como se instala el paquete realmente.

## 2. Crear el parser de comandos

Python trae `argparse` en la libreria estandar. Un ejemplo minimo:

```python
import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(prog="saluda")
    parser.add_argument("nombre")
    args = parser.parse_args(argv)
    print(f"Hola {args.nombre}")
    return 0
```

Cuando el usuario ejecuta:

```powershell
saluda Pablo
```

`argparse` convierte `Pablo` en `args.nombre`.

## 3. Declarar el comando en `pyproject.toml`

La clave es `[project.scripts]`.

```toml
[project.scripts]
mydron = "mydron.cli:main"
```

Esto significa:

- crea un ejecutable llamado `mydron`
- cuando se ejecute, importa `mydron.cli`
- llama a la funcion `main`

En Windows se genera normalmente:

```text
.venv\Scripts\mydron.exe
```

## 4. Crear entorno virtual

Un entorno virtual guarda dependencias aisladas para el proyecto.

En este proyecto se creo con Python 3.12:

```powershell
cd D:\MyDron\mydron-cli
C:\Users\pablo\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
```

Activarlo:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea scripts:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Despues se activa de nuevo:

```powershell
.\.venv\Scripts\Activate.ps1
```

## 5. Instalar el proyecto

Dentro del entorno virtual:

```powershell
pip install -e .
```

`-e` significa editable. Los cambios en `src/mydron` se usan sin reinstalar el
paquete cada vez.

Comprobar:

```powershell
mydron --help
```

## 6. Ejecutar sin activar el entorno

Aunque el entorno no este activado, puedes llamar directamente al ejecutable:

```powershell
D:\MyDron\mydron-cli\.venv\Scripts\mydron.exe --help
```

Esto es util para accesos directos, tareas programadas o scripts.

## 7. Poner `mydron` en el PATH de Windows

Hay dos formas practicas.

### Opcion A: anadir `.venv\Scripts` al PATH del usuario

Ruta que hay que anadir:

```text
D:\MyDron\mydron-cli\.venv\Scripts
```

Desde PowerShell:

```powershell
$old = [Environment]::GetEnvironmentVariable("Path", "User")
$new = "D:\MyDron\mydron-cli\.venv\Scripts"
[Environment]::SetEnvironmentVariable("Path", "$old;$new", "User")
```

Cierra y abre PowerShell. Despues:

```powershell
mydron --help
```

Ventaja: sencillo.

Inconveniente: el PATH queda apuntando a un entorno virtual concreto.

### Opcion B: crear una carpeta de comandos propia

Crear una carpeta:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\bin"
```

Crear un lanzador `mydron.cmd` dentro de esa carpeta con este contenido:

```bat
@echo off
"D:\MyDron\mydron-cli\.venv\Scripts\mydron.exe" %*
```

En este proyecto ya existe un lanzador preparado en:

```text
D:\MyDron\mydron-cli\bin\mydron.cmd
```

Tambien puedes anadir directamente esta carpeta al PATH:

```text
D:\MyDron\mydron-cli\bin
```

Anadir la carpeta al PATH:

```powershell
$old = [Environment]::GetEnvironmentVariable("Path", "User")
$new = "$env:USERPROFILE\bin"
[Environment]::SetEnvironmentVariable("Path", "$old;$new", "User")
```

Cierra y abre PowerShell. Despues:

```powershell
mydron --help
```

Ventaja: puedes mover el proyecto o cambiar el entorno editando solo el `.cmd`.

## 8. Diferencia entre `python -m paquete` y comando instalado

Si existe `src/mydron/__main__.py`, se puede ejecutar:

```powershell
python -m mydron
```

Pero eso requiere que el paquete este importable por el Python activo.

El comando instalado con `[project.scripts]` es mas comodo:

```powershell
mydron
```

## 9. Flujo normal de desarrollo de una CLI

1. Editar codigo en `src/paquete`.
2. Ejecutar comando:

   ```powershell
   mydron --help
   ```

3. Probar subcomandos:

   ```powershell
   mydron ports
   ```

4. Anadir tests.
5. Ejecutar tests.
6. Documentar el comando nuevo.

## 10. Reglas practicas

- Usa `argparse` para CLIs simples y robustas.
- Usa subcomandos cuando haya varias acciones: `ports`, `info`, `status`.
- Devuelve `0` si todo va bien.
- Devuelve `1` si hay error operativo.
- Escribe errores en `stderr`.
- No hagas cambios peligrosos sin confirmacion explicita.
- En herramientas de drones, crea backup antes de escribir configuracion.
