# Como funciona mydron-cli

`mydron-cli` es una aplicacion de linea de comandos para comunicarse con una
controladora de vuelo INAV por USB. En Windows, la placa aparece como un puerto
serie, normalmente `COM3`, `COM4`, `COM5`, etc.

## Objetivo

El objetivo inicial es trabajar con seguridad:

- detectar el puerto serie
- consultar informacion basica de la placa
- leer estado basico
- entrar en la CLI textual de INAV
- crear backups con `dump`

No hay comandos de armado, motores ni envio de canales RC.

## Estructura del proyecto

```text
mydron-cli/
  pyproject.toml
  README.md
  docs/
    COMO_FUNCIONA.md
    CREAR_CLIS_WINDOWS.md
  src/
    mydron/
      __init__.py
      __main__.py
      cli.py
      inav.py
      msp.py
      serial_port.py
  tests/
    test_msp.py
```

## Modulos principales

### `cli.py`

Define los comandos que ve el usuario:

- `mydron ports`
- `mydron info --port COM5`
- `mydron status --port COM5`
- `mydron dump-cli --port COM5 --out backups\dump.txt`
- `mydron cli --port COM5 status`
- `mydron quick-health --port COM5 --board speedybee-f405-v4`

Usa `argparse`, que es la libreria estandar de Python para construir CLIs.

### `serial_port.py`

Contiene la parte de puerto serie:

- lista los puertos disponibles con `serial.tools.list_ports`
- abre el puerto con `serial.Serial`
- configura baudrate, timeout y write timeout

La dependencia que permite esto es `pyserial`.

### `msp.py`

Implementa la parte de MultiWii Serial Protocol, el protocolo que usa INAV para
comunicacion de configurador y telemetria basica.

Incluye:

- construccion de peticiones MSP v1
- construccion de peticiones MSP v2
- CRC8 DVB-S2 para MSP v2
- lectura de tramas MSP v1 y MSP v2
- parseo de respuestas basicas:
  - `MSP_API_VERSION`
  - `MSP_FC_VERSION`
  - `MSP_STATUS`
  - cadenas ASCII como variante, board y build

### `inav.py`

Es la capa de alto nivel para hablar con INAV.

Hace tres cosas:

- abre/cierra la conexion serie
- envia comandos MSP y espera respuesta
- entra en la CLI textual de INAV para ejecutar comandos como `dump` o `status`

## Flujo de `mydron info`

1. El usuario ejecuta:

   ```powershell
   mydron info --port COM5
   ```

2. `cli.py` crea un `InavClient`.
3. `InavClient` abre `COM5` a `115200`.
4. Se envian varias peticiones MSP:

   - `MSP_API_VERSION`
   - `MSP_FC_VARIANT`
   - `MSP_FC_VERSION`
   - `MSP_BOARD_INFO`
   - `MSP_BUILD_INFO`

5. Se parsean las respuestas.
6. Se imprime la informacion en pantalla.

## Flujo de `dump-cli`

1. El usuario ejecuta:

   ```powershell
   mydron dump-cli --port COM5 --out backups\inav-dump.txt
   ```

2. La herramienta abre el puerto serie.
3. Envia `#` para entrar en la CLI textual de INAV.
4. Envia `dump`.
5. Lee la salida hasta volver a detectar el prompt de INAV.
6. Guarda la salida en el fichero indicado.
7. Envia `exit` para salir de la CLI textual.

Este flujo es importante porque `dump` es la forma mas clara de guardar una
copia completa de la configuracion antes de cambiar nada.

## Uso recomendado con la SpeedyBee F405 V4

1. Quita las helices.
2. Conecta la placa por USB.
3. Cierra INAV Configurator si esta abierto.
4. Lista puertos:

   ```powershell
   mydron ports
   ```

5. Prueba informacion:

   ```powershell
   mydron info --port COM5
   ```

6. Crea backup:

   ```powershell
   mydron dump-cli --port COM5 --out backups\speedybee-v4-dump.txt
   ```

## Problemas comunes

### `Access is denied`

Otro programa tiene abierto el puerto. Cierra INAV Configurator, Betaflight
Configurator, Mission Planner u otra terminal serie.

### No aparece ningun puerto

Puede faltar el driver USB, el cable puede ser solo de carga, o Windows no ha
terminado de enumerar el dispositivo.

### `No MSP response`

Posibles causas:

- puerto equivocado
- baudrate equivocado
- la placa esta en modo DFU
- otro programa esta usando el puerto
- INAV no ha terminado de arrancar

Prueba:

```powershell
mydron info --port COM5 --baud 115200
mydron info --port COM5 --baud 57600
```

### `dump-cli` no termina

El comando `dump` puede tardar. Usa mas timeout:

```powershell
mydron dump-cli --port COM5 --out backups\dump.txt --timeout 60
```

## Siguiente evolucion

Los siguientes pasos razonables son:

- detectar automaticamente el puerto INAV probando MSP en cada COM
- crear `backup` con nombre automatico y fecha
- implementar `diff` entre dumps
- permitir cambios controlados con confirmacion explicita
- bloquear por defecto comandos peligrosos como `motor`, `feature`, `set` y `save`
  hasta que exista un modo seguro con backup previo

## Seguridad en comandos CLI textuales

El subcomando `mydron cli` no reenvia cualquier comando a ciegas. Por defecto
solo permite comandos de lectura y diagnostico como `status`, `version`, `get`,
`diff` y `dump`.

Para comandos que puedan cambiar configuracion o estado hay que usar
`--allow-unsafe`:

```powershell
mydron cli --port COM5 --allow-unsafe "set nombre = valor"
```

La referencia de riesgos esta en `docs/INAV_CLI_COMMANDS.md`.

## Health check especifico de placa

El comando `quick-health` usa un perfil de placa versionado en:

```text
boards\speedybee-f405-v4\health-profile.json
```

Para la SpeedyBee F405 V4 comprueba:

```text
+-------------+--------------------------------+
| Check       | Esperado                       |
+-------------+--------------------------------+
| Board ID    | SB44                           |
| Target      | SPEEDYBEEF405V4                |
| GYRO        | OK, ICM42605                   |
| ACC         | OK, ICM42605                   |
| BARO        | OK, SPL06                      |
| I2C errors  | 0                              |
| OSD         | MAX7456                        |
| SD          | Warning si Startup failed      |
+-------------+--------------------------------+
```

Uso:

```powershell
mydron quick-health --port COM5 --board speedybee-f405-v4
```

El informe operativo se escribe en:

```text
D:\MyDron\boards\speedybee-f405-v4\reports
```
