# Estudio de comandos CLI INAV en este dron

Fecha del estudio: 2026-05-16.

Placa conectada:

```text
INAV/SPEEDYBEEF405V4 9.0.1 Feb 13 2026 / 06:49:35 (d44f2cf6)
GCC-13.2.1 20231009
Puerto: COM5
Target: SPEEDYBEEF405V4
Board ID: SB44
```

## Fuentes usadas

- Salida real de `help`: `backups/cli-help.txt`
- Salida real de `get`: `backups/cli-get-all.txt`
- Salida real de `diff all`: `backups/cli-diff-all.txt`
- Backup completo: `backups/speedybee-v4-dump.txt`
- Documentacion oficial INAV CLI: <https://github.com/iNavFlight/inav/blob/master/docs/Cli.md>
- Documentacion oficial de variables CLI: <https://github.com/iNavFlight/inav/blob/master/docs/Settings.md>

La documentacion oficial indica que la CLI se abre enviando `#`, que `save`
guarda y reinicia la controladora, y que `dump` / `diff` son los comandos base
para backup y restauracion. Tambien avisa que no todos los comandos existen en
todas las controladoras.

## Resumen del firmware

La placa expone 48 comandos principales por `help`.

El comando `get` ha devuelto 670 variables configurables con valor actual y
rango permitido o valores enumerados.

El comando `diff all` ha devuelto una configuracion diferencial pequena frente a
los defaults del firmware. La salida incluye `save` al final porque esta pensada
para restaurarse como batch.

## Politica de seguridad en `mydron-cli`

`mydron cli` ahora bloquea por defecto comandos que pueden cambiar configuracion,
rebootear la placa, entrar en modos especiales o activar salidas.

Comandos permitidos por defecto:

```text
diff
dump
get
gpssats
help
memory
resource
sd_info
showdebug
status
tasks
version
```

Ejemplos seguros:

```powershell
mydron cli --port COM5 version
mydron cli --port COM5 status
mydron cli --port COM5 get nav
mydron cli --port COM5 diff all
```

Para comandos de escritura hay que usar:

```powershell
mydron cli --port COM5 --allow-unsafe "set nombre = valor"
```

Antes de usar `--allow-unsafe` debe existir backup reciente:

```powershell
mydron dump-cli --port COM5 --out backups\speedybee-v4-dump.txt
```

## Clasificacion por riesgo

### Nivel 0: lectura y diagnostico

Estos comandos no deberian cambiar configuracion ni estado persistente.

| Comando | Funcion | Automatizable |
| --- | --- | --- |
| `help` | Lista comandos disponibles | Si |
| `version` | Muestra firmware, target y build | Si |
| `status` | Estado general, sensores, flags de armado | Si |
| `get` | Lee variables y rangos | Si |
| `diff` | Muestra cambios respecto a defaults | Si |
| `dump` | Vuelca configuracion completa | Si |
| `resource` | Lista recursos hardware asignados | Si |
| `memory` | Uso de memoria | Si |
| `tasks` | Estadisticas de tareas | Si |
| `sd_info` | Informacion de SD | Si |
| `gpssats` | Satelites GPS visibles | Si |
| `showdebug` | Campos debug | Si, con cuidado |

### Nivel 1: lectura con subcomandos, escritura con argumentos

Estos comandos pueden ser seguros con una forma concreta, pero peligrosos con
otra. Por eso se bloquean por defecto en `mydron-cli`.

| Comando | Lectura tipica | Escritura tipica |
| --- | --- | --- |
| `feature` | `feature list` | `feature GPS`, `feature -GPS` |
| `blackbox` | `blackbox list` | `blackbox NAV_POS`, `blackbox -ACC` |
| `beeper` | `beeper list` | `beeper -RX_SET` |
| `serial` | `serial` | `serial 0 ...` |
| `osd_layout` | `osd_layout` | `osd_layout 0 ...` |
| `timer_output_mode` | `timer_output_mode` | `timer_output_mode 2 SERVOS` |
| `motor` | `motor` podria leer | `motor 0 1100` mueve salidas |

### Nivel 2: cambios de configuracion

Estos comandos modifican configuracion en RAM. Normalmente no son persistentes
hasta `save`, pero pueden afectar el estado actual.

| Comando | Area |
| --- | --- |
| `set` | Variables generales |
| `aux` | Modos asignados a canales |
| `adjrange` | Ajustes en vuelo |
| `color` | Colores OSD/LED |
| `mode_color` | Colores por modo |
| `led` | Tira LED |
| `ledpinpwm` | PWM en pin LED |
| `map` | Orden de canales RC |
| `rxrange` | Rango de canales RC |
| `mmix` | Mezclador de motores |
| `smix` | Mezclador de servos |
| `servo` | Configuracion de servos |
| `safehome` | Safehomes |
| `geozone` | Geozonas |
| `fwapproach` | Aproximacion fixed wing |
| `logic` | Condiciones logicas |
| `gvar` | Variables globales |
| `pid` | Controladores PID configurables |
| `osd_custom_elements` | Elementos OSD personalizados |
| `temp_sensor` | Sensores de temperatura |
| `wp` | Waypoints |

### Nivel 3: perfiles y contexto de configuracion

Estos comandos cambian el perfil activo. Eso altera a que seccion afectan los
siguientes `get`, `set`, `dump` o `diff`.

| Comando | Riesgo |
| --- | --- |
| `control_profile` | Cambia perfil de control/PID |
| `mixer_profile` | Cambia perfil de mixer |
| `battery_profile` | Cambia perfil de bateria |

Para backups completos conviene usar `dump all` o recorrer perfiles de forma
explicita.

### Nivel 4: persistencia, reboot, modos especiales y passthrough

Estos comandos requieren confirmacion explicita y un motivo claro.

| Comando | Efecto |
| --- | --- |
| `save` | Guarda configuracion y reinicia la FC |
| `defaults` | Resetea defaults y reinicia |
| `dfu` | Entra en modo DFU en el reboot |
| `msc` | Cambia a USB Mass Storage |
| `gpspassthrough` | Redirige GPS al puerto serie |
| `serialpassthrough` | Redirige un puerto serie |
| `bind_rx` | Inicia binding de receptor |
| `play_sound` | Activa sonido |
| `cli_delay` | Cambia delay de CLI |
| `batch` | Agrupa comandos; usado en backups/restores |

### Nivel 5: salidas fisicas

Estos comandos no deben automatizarse sin una capa especifica de seguridad.

| Comando | Riesgo |
| --- | --- |
| `motor` | Puede activar motores o ESC |
| `servo` | Puede mover servos |
| `ledpinpwm` | Puede activar salida PWM en pin LED |
| `timer_output_mode` | Puede cambiar asignacion de salidas |
| `resource` con cambios futuros | Puede romper asignaciones de hardware |

Regla operativa: helices fuera antes de cualquier prueba que toque salidas.

## Comandos encontrados en esta placa

| Comando | Descripcion de `help` | Riesgo |
| --- | --- | --- |
| `adjrange` | Configure adjustment ranges | Nivel 2 |
| `aux` | Configure modes | Nivel 2 |
| `batch` | Start or end a batch of commands | Nivel 4 |
| `beeper` | Turn on/off beeper | Nivel 1 |
| `bind_rx` | Initiate binding for RX SPI or SRXL2 | Nivel 4 |
| `color` | Configure colors | Nivel 2 |
| `mode_color` | Configure mode and special colors | Nivel 2 |
| `cli_delay` | CLI Delay | Nivel 4 |
| `defaults` | Reset to defaults and reboot | Nivel 4 |
| `dfu` | DFU mode on reboot | Nivel 4 |
| `diff` | List configuration changes from default | Nivel 0 |
| `dump` | Dump configuration | Nivel 0 |
| `exit` | Exit CLI | Nivel 0 |
| `feature` | Configure features | Nivel 1 |
| `blackbox` | Configure blackbox fields | Nivel 1 |
| `fwapproach` | Fixed Wing Approach Settings | Nivel 2 |
| `get` | Get variable value | Nivel 0 |
| `geozone` | Get or set geo zones | Nivel 2 |
| `gpspassthrough` | Passthrough GPS to serial | Nivel 4 |
| `gpssats` | Show GPS satellites | Nivel 0 |
| `help` | Show help | Nivel 0 |
| `led` | Configure LEDs | Nivel 2 |
| `ledpinpwm` | Start/stop PWM on LED pin | Nivel 5 |
| `map` | Configure RC channel order | Nivel 2 |
| `memory` | View memory usage | Nivel 0 |
| `mmix` | Custom motor mixer | Nivel 2 |
| `motor` | Get/set motor | Nivel 5 |
| `msc` | Switch into MSC mode | Nivel 4 |
| `play_sound` | Play sound | Nivel 4 |
| `control_profile` | Change control profile | Nivel 3 |
| `mixer_profile` | Change mixer profile | Nivel 3 |
| `battery_profile` | Change battery profile | Nivel 3 |
| `resource` | View currently used resources | Nivel 0 |
| `rxrange` | Configure RX channel ranges | Nivel 2 |
| `safehome` | Safe home list | Nivel 2 |
| `save` | Save and reboot | Nivel 4 |
| `serial` | Configure serial ports | Nivel 1 |
| `serialpassthrough` | Passthrough serial data to port | Nivel 4 |
| `servo` | Configure servos | Nivel 5 |
| `logic` | Configure logic conditions | Nivel 2 |
| `gvar` | Configure global variables | Nivel 2 |
| `pid` | Configurable PID controllers | Nivel 2 |
| `osd_custom_elements` | Configurable OSD custom elements | Nivel 2 |
| `set` | Change setting | Nivel 2 |
| `smix` | Servo mixer | Nivel 2 |
| `sd_info` | SD card info | Nivel 0 |
| `showdebug` | Show debug fields | Nivel 0 |
| `status` | Show status | Nivel 0 |
| `tasks` | Show task stats | Nivel 0 |
| `temp_sensor` | Temperature sensor settings | Nivel 2 |
| `version` | Show version | Nivel 0 |
| `wp` | Waypoint list | Nivel 2 |
| `osd_layout` | Get or set OSD layout | Nivel 1 |
| `timer_output_mode` | Get or set timer output mode | Nivel 1 |

## Variables configurables

`get` devuelve variables con esta forma:

```text
gyro_main_lpf_hz = 90
Allowed range: 0 - 500

gyro_filter_mode = STATIC
Allowed values: OFF, STATIC, DYNAMIC, ADAPTIVE
```

Esto permite que una futura version de `mydron-cli` valide cambios antes de
enviarlos:

1. Leer `get nombre`.
2. Parsear valor actual y rango permitido.
3. Comparar contra el valor nuevo.
4. Crear backup.
5. Enviar `set nombre = valor`.
6. Leer de nuevo `get nombre`.
7. Pedir confirmacion antes de `save`.

## Comandos que conviene automatizar primero

1. `backup`: ejecutar `dump all` o `dump` con nombre automatico y fecha.
2. `diff`: ejecutar `diff all` y guardar copia.
3. `get`: buscar variables por patron.
4. `doctor`: ejecutar `version`, `status`, `tasks`, `memory`, `sd_info`.
5. `settings export`: convertir `get` a JSON local.
6. `safe-set`: cambiar una variable con validacion, backup previo y confirmacion.

## Reglas para cambios futuros

- Nunca ejecutar `save` automaticamente despues de `set`.
- Nunca permitir `motor` sin modo especial, helices fuera y confirmacion.
- Nunca permitir `defaults`, `dfu`, `msc`, `serialpassthrough` o `gpspassthrough`
  sin doble confirmacion.
- Para restaurar configuracion, preferir `diff` frente a `dump` cuando se cambia
  de version de firmware.
- Despues de restaurar, repetir `diff` y comparar.
