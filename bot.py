import os
import time
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from playwright.sync_api import sync_playwright

# Credenciales desde variables de entorno (GitHub Secrets)
USUARIO = os.environ.get("GF_USER", "POSCOCFBC")
PASSWORD = os.environ.get("GF_PASSWORD", "1234")

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
            """Hace clic forzado en el campo y escribe la fecha directamente"""
            selector = f"#{field_id}_I"
            try:
                # force=True ignora que el campo está disabled
                page.locator(selector).click(force=True, timeout=8000)
                time.sleep(0.3)
                page.keyboard.press("Control+a")
                page.keyboard.type(fecha_str)
                page.keyboard.press("Tab")
                time.sleep(0.5)
                print(f"   ✅ {field_id} llenado con: {fecha_str}")
            except Exception as e:
                print(f"   ⚠️ Error en {field_id}: {e}")

        # ── 2. Primero seleccionar "Todos" (activa los campos de fecha) ──────────
        print("🔘 Paso 1: Seleccionando radio 'Todos'...")
        try:
            page.locator('label:has-text("Todos")').click(timeout=8000)
            time.sleep(2)   # esperar que el portal habilite los campos
            print("   ✅ Radio 'Todos' seleccionado")
        except Exception as e:
            print(f"   ⚠️ No se pudo clic en 'Todos': {e}")

        # ── 3. Luego modificar las fechas escribiendo directamente ───────────────
        print(f"📅 Paso 2: Configurando fechas: Desde={fecha_inicio} | Hasta={fecha_fin}")
        set_devexpress_date("dtpFInicial", fecha_inicio)
        set_devexpress_date("dtpFFinal",   fecha_fin)
        time.sleep(1)

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

        browser.close()
        return archivo

if __name__ == "__main__":
    archivo = descargar_reporte()
    print(f"🎉 Listo! Archivo guardado como: {archivo}")
