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
        # El botón tiene id="btnExportarExcelImg" (imagen dentro del botón)
        # El botón padre clickeable tiene id="btnExportarExcel" (sin "Img")
        print("📥 Descargando XLSX...")
        try:
            with page.expect_download(timeout=60000) as dl:
                # Intentar clic en el botón padre del ícono Excel
                try:
                    page.evaluate("document.getElementById('btnExportarExcel').click()")
                    print("   → Clic via JS en #btnExportarExcel")
                except Exception:
                    # Si no funciona JS, clic directo en la imagen
                    page.locator('#btnExportarExcelImg').click(timeout=15000)
                    print("   → Clic en #btnExportarExcelImg")

            archivo = "reporte_galleria.xlsx"
            dl.value.save_as(archivo)
            print(f"✅ Archivo descargado: {archivo}")

        except Exception as e:
            # Estrategia de respaldo: buscar por clase CSS
            print(f"   ⚠️ Error primer intento: {e}")
            print("   🔄 Intentando por clase CSS...")
            with page.expect_download(timeout=60000) as dl:
                page.locator('.dxIcon_export_exporttoxlsx_16x16').click(timeout=15000)
            archivo = "reporte_galleria.xlsx"
            dl.value.save_as(archivo)
            print(f"✅ Archivo descargado (respaldo): {archivo}")

        browser.close()
        return archivo

if __name__ == "__main__":
    archivo = descargar_reporte()
    print(f"🎉 Listo! Archivo guardado como: {archivo}")
