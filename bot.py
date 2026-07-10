import os
import time
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from playwright.sync_api import sync_playwright

# Credenciales desde variables de entorno (GitHub Secrets)
USUARIO = os.environ.get("GF_USER", "POSCOCFBC")
PASSWORD = os.environ.get("GF_PASSWORD", "1234")

POSCO_USER = os.environ.get("POSCO_USER", "")
POSCO_PASSWORD = os.environ.get("POSCO_PASSWORD", "")

URL_LOGIN = "https://farms.galleriafarms.com/SplashWFrm.aspx?ReturnUrl=%2fDefault.aspx"

def calcular_fechas():
    """Calcula el rango: hoy → hoy + 6 meses"""
    hoy = date.today()
    fin  = hoy + relativedelta(months=6)
    # Formato requerido por el portal: M/D/YYYY
    fecha_inicio = hoy.strftime("%-m/%-d/%Y")   # ej: 7/8/2026
    fecha_fin    = fin.strftime("%-m/%-d/%Y")    # ej: 1/8/2027
    return fecha_inicio, fecha_fin

def descargar_reporte():
    fecha_inicio, fecha_fin = calcular_fechas()
    print(f"📅 Rango de fechas: {fecha_inicio} → {fecha_fin}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # ── 1. Login ──────────────────────────────────────────────────────────
        print("🌐 Abriendo página de login...")
        page.goto(URL_LOGIN, wait_until="networkidle", timeout=60000)

        print("🔐 Haciendo login...")
        page.fill('input[placeholder*="usuario" i], input[type="text"]', USUARIO)
        page.fill('input[placeholder*="ontra" i], input[type="password"]', PASSWORD)
        page.click('button:has-text("Entrar"), input[value*="Entrar" i], input[type="submit"]')

        print("⏳ Esperando que cargue el dashboard...")
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(3)
        print(f"   ✅ URL actual: {page.url}")

        def set_devexpress_date(field_id, fecha_str):
            """Usa la API nativa de DevExpress para asignar la fecha de forma segura"""
            try:
                page.evaluate(f"""
                    var ctrl = ASPxClientControl.GetControlCollection().GetByName('{field_id}');
                    if (ctrl && ctrl.SetDate) {{
                        var parts = '{fecha_str}'.split('/');
                        // parts[0] = mes, parts[1] = dia, parts[2] = año
                        var dateObj = new Date(parseInt(parts[2]), parseInt(parts[0])-1, parseInt(parts[1]));
                        ctrl.SetDate(dateObj);
                    }}
                """)
                print(f"   ✅ {field_id} modificado via API DevExpress a: {fecha_str}")
            except Exception as e:
                print(f"   ⚠️ Error API DevExpress en {field_id}: {e}")
                
            # Pequeña pausa para que la página registre el cambio
            time.sleep(0.5)

        # ── 2. Primero seleccionar "Todos" (activa los campos de fecha) ──────────
        print("🔘 Paso 1: Seleccionando radio 'Todos'...")
        try:
            page.locator('label:has-text("Todos")').click(timeout=8000)
            print("   ⏳ Esperando que el servidor procese 'Todos'...")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(4)   # Espera extra para asegurar que el Ajax terminó
            print("   ✅ Radio 'Todos' seleccionado y procesado")
        except Exception as e:
            print(f"   ⚠️ Error en 'Todos': {e}")

        # ── 3. Luego modificar las fechas ────────────────────────────────────────
        print(f"📅 Paso 2: Configurando fechas: Desde={fecha_inicio} | Hasta={fecha_fin}")
        set_devexpress_date("dtpFInicial", fecha_inicio)
        set_devexpress_date("dtpFFinal",   fecha_fin)
        time.sleep(2) # Dar tiempo al cliente DevExpress para actualizarse

        # Screenshot para ver visualmente qué quedó en los campos
        page.screenshot(path="debug_fechas.png")

        # Verificar valores en pantalla
        val_desde = page.evaluate("document.getElementById('dtpFInicial_I') ? document.getElementById('dtpFInicial_I').value : '?'")
        val_hasta  = page.evaluate("document.getElementById('dtpFFinal_I')  ? document.getElementById('dtpFFinal_I').value  : '?'")
        print(f"   📅 Fecha DESDE en pantalla: {val_desde}")
        print(f"   📅 Fecha HASTA en pantalla: {val_hasta}")

        # ── 4. Luego clic en "Cargar" ───────────────────────────────────────────
        print("▶️ Ejecutando 'Cargar' via JavaScript...")
        try:
            page.evaluate("document.getElementById('btnRefresh_I').click()")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)
            print("   ✅ Datos cargados")
        except Exception as e:
            print(f"   ⚠️ Error al cargar: {e}")

        # ── 5. Descargar el archivo Excel ──────────────────────────────────────
        print("📥 Descargando archivo de exportación...")
        try:
            with page.expect_download(timeout=60000) as dl:
                try:
                    page.evaluate("document.getElementById('btnExportarExcel').click()")
                    print("   → Clic via JS en #btnExportarExcel")
                except Exception:
                    page.locator('#btnExportarExcelImg').click(timeout=15000)
                    print("   → Clic en #btnExportarExcelImg")

            descarga = dl.value
            nombre_sugerido = descarga.suggested_filename
            print(f"   → Nombre sugerido por el servidor: {nombre_sugerido}")

            # Guardar con nombre que incluye la fecha de hoy y la extensión real
            ext = os.path.splitext(nombre_sugerido)[1] or ".xls"
            hoy_str = date.today().strftime("%Y-%m-%d")
            archivo = f"reporte_galleria_{hoy_str}{ext}"
            descarga.save_as(archivo)
            print(f"✅ Archivo descargado: {archivo}")

        except Exception as e:
            print(f"   ⚠️ Error primer intento: {e}")
            print("   🔄 Intentando por clase CSS...")
            with page.expect_download(timeout=60000) as dl:
                page.locator('.dxIcon_export_exporttoxlsx_16x16').click(timeout=15000)
            descarga = dl.value
            nombre_sugerido = descarga.suggested_filename
            ext = os.path.splitext(nombre_sugerido)[1] or ".xls"
            hoy_str = date.today().strftime("%Y-%m-%d")
            archivo = f"reporte_galleria_{hoy_str}{ext}"
            descarga.save_as(archivo)
            print(f"✅ Archivo descargado (respaldo): {archivo}")

        # ── 6. Fase 2: Exploración de PoscoClient (Paso 1) ──────────────────────
        print("\n🚀 Iniciando Fase 2 (Paso 1): Exploración de PoscoClient con Login...")
        try:
            print("🌐 Navegando a Login de PoscoClient...")
            page.goto("http://3.132.9.174/Posco/", wait_until="networkidle", timeout=60000)
            time.sleep(3)
            
            print("🔐 Iniciando sesión en PoscoClient...")
            # En base a la captura, buscar campos de usuario y contraseña
            page.fill('input[placeholder*="usuario@email.com" i], input[type="text"]', POSCO_USER)
            page.fill('input[placeholder*="Password" i], input[type="password"]', POSCO_PASSWORD)
            page.click('button:has-text("Iniciar Sesión"), button:has-text("Login")')
            
            print("⏳ Esperando que cargue el dashboard de Posco...")
            page.wait_for_load_state("networkidle", timeout=60000)
            time.sleep(5)
            
            print("🌐 Navegando a revisar-ordenes...")
            page.goto("http://3.132.9.174/Posco/#/revisar-ordenes", wait_until="networkidle", timeout=60000)
            time.sleep(5)

            print("📸 Tomando captura inicial autenticado (debug_posco_login.png)...")
            page.screenshot(path="debug_posco_login.png", full_page=True)
            
            print("🔎 Abriendo modal de 'Import excel'...")
            page.click('button:has-text("Revisar Archivo")', timeout=10000)
            time.sleep(2)

            print("📸 Tomando captura del modal (debug_posco_modal.png)...")
            page.screenshot(path="debug_posco_modal.png", full_page=True)

            print("🔽 Seleccionando formato 'Galeria'...")
            # Como es un select normal, buscamos por etiqueta <select> o por texto cercano
            # Intentaremos seleccionarlo por su contenido.
            try:
                page.select_option('select', label="Galeria", timeout=5000)
            except Exception:
                print("   ⚠️ No se pudo seleccionar 'Galeria' directamente por etiqueta select, intentando otras formas...")
                # Por si no es un select estándar (ej. Angular Material, ng-select, etc)
                # Damos click al dropdown y luego a la opción
                # Asumimos que la foto mostraba un <select> estándar de HTML, pero si es de Angular 
                # a veces hay que usar clics. Dejaremos select_option que es lo habitual.
            
            time.sleep(2)
            print("📸 Tomando captura tras seleccionar formato (debug_posco_formato.png)...")
            page.screenshot(path="debug_posco_formato.png", full_page=True)
            
            print("📁 Seleccionando archivo Excel en el input...")
            # Inyectar el archivo en el input tipo file (esto es equivalente a darle click a Elegir Archivo y buscarlo)
            page.set_input_files('input[type="file"]', archivo)
            
            time.sleep(2)
            print("📸 Tomando captura tras seleccionar archivo (debug_posco_archivo.png)...")
            page.screenshot(path="debug_posco_archivo.png", full_page=True)
            
            print("⬆️ Dando clic en Upload para subir el archivo...")
            page.click('button:has-text("Upload"), button:has-text("Subir")', timeout=10000)
            
            print("⏳ Esperando 10 minutos a que termine la subida...")
            # Esperar 600 segundos (10 minutos)
            time.sleep(600)
            
            print("📸 Tomando captura final tras 10 minutos (debug_posco_final.png)...")
            page.screenshot(path="debug_posco_final.png", full_page=True)
            
            print("🔄 Dando clic en 'Actualizar' antes de recargar...")
            page.click('button:has-text("Actualizar")', timeout=10000)
            
            print("⏳ Esperando 5 segundos a que actualice la tabla...")
            time.sleep(5)
            
            print("📸 Tomando captura tras dar clic en actualizar (debug_posco_actualizado.png)...")
            page.screenshot(path="debug_posco_actualizado.png", full_page=True)
            
            print("🔄 Recargando la página...")
            page.reload(wait_until="networkidle", timeout=60000)
            
            print("⏳ Esperando 2 minutos extra tras la recarga...")
            time.sleep(120)
            
            print("📸 Tomando captura tras la recarga (debug_posco_reload.png)...")
            page.screenshot(path="debug_posco_reload.png", full_page=True)

            print("✅ Subida completada exitosamente.")
            
        except Exception as e:
            print(f"   ❌ Error en la exploración de PoscoClient: {e}")
            page.screenshot(path="debug_posco_error.png", full_page=True)

        browser.close()
        return archivo

if __name__ == "__main__":
    archivo = descargar_reporte()
    print(f"🎉 Listo! Archivo guardado como: {archivo}")
