import os
import time
from playwright.sync_api import sync_playwright

# Credenciales desde variables de entorno (GitHub Secrets)
USUARIO = os.environ.get("GF_USER", "POSCOCFBC")
PASSWORD = os.environ.get("GF_PASSWORD", "1234")

URL_LOGIN = "https://farms.galleriafarms.com/SplashWFrm.aspx?ReturnUrl=%2fDefault.aspx"

def descargar_reporte():
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

        # ── 2. Seleccionar "Todos" ─────────────────────────────────────────────
        print("🔘 Seleccionando radio 'Todos'...")
        try:
            page.locator('label:has-text("Todos")').click(timeout=8000)
            time.sleep(1)
            print("   ✅ Radio 'Todos' seleccionado")
        except Exception as e:
            print(f"   ⚠️ No se pudo clic en 'Todos': {e}")

        # ── 3. Clic en "Cargar" usando JavaScript (el botón es invisible pero funciona) ──
        print("▶️ Ejecutando 'Cargar' via JavaScript...")
        try:
            # El botón tiene id="btnRefresh_I" pero no es visible — lo clickeamos con JS
            page.evaluate("document.getElementById('btnRefresh_I').click()")
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(3)
            print("   ✅ Datos cargados")
        except Exception as e:
            print(f"   ⚠️ Error al cargar: {e}")

        # ── 4. Clic en botón Excel ─────────────────────────────────────────────
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

            # Detectar el formato real del archivo descargado
            nombre_sugerido = descarga.suggested_filename
            print(f"   → Nombre sugerido por el servidor: {nombre_sugerido}")

            # Determinar extensión real
            if nombre_sugerido.lower().endswith(".xlsx"):
                archivo = "reporte_galleria.xlsx"
            elif nombre_sugerido.lower().endswith(".xls"):
                archivo = "reporte_galleria.xls"
            elif nombre_sugerido.lower().endswith(".csv"):
                archivo = "reporte_galleria.csv"
            else:
                # Guardar con el nombre original del servidor
                import os as _os
                ext = _os.path.splitext(nombre_sugerido)[1] or ".download"
                archivo = f"reporte_galleria{ext}"

            descarga.save_as(archivo)
            print(f"✅ Archivo descargado: {archivo} (formato real: {nombre_sugerido})")

        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            print("   🔄 Intentando por clase CSS...")
            with page.expect_download(timeout=60000) as dl:
                page.locator('.dxIcon_export_exporttoxlsx_16x16').click(timeout=15000)
            descarga = dl.value
            nombre_sugerido = descarga.suggested_filename
            import os as _os
            ext = _os.path.splitext(nombre_sugerido)[1] or ".xls"
            archivo = f"reporte_galleria{ext}"
            descarga.save_as(archivo)
            print(f"✅ Archivo descargado (respaldo): {archivo}")

        browser.close()
        return archivo

if __name__ == "__main__":
    archivo = descargar_reporte()
    print(f"🎉 Listo! Archivo guardado como: {archivo}")
