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

        print("🌐 Abriendo página de login...")
        page.goto(URL_LOGIN, wait_until="networkidle", timeout=60000)

        # Screenshot para debug del login
        page.screenshot(path="debug_01_login_page.png")
        print("📸 Screenshot: debug_01_login_page.png")

        # Login
        print("🔐 Haciendo login...")
        page.fill('input[name*="Usuario"], input[id*="Usuario"], input[type="text"]', USUARIO)
        page.fill('input[name*="Password"], input[id*="Password"], input[type="password"]', PASSWORD)
        page.click('input[type="submit"], button[type="submit"]')

        # Esperar que la página cargue completamente después del login
        print("⏳ Esperando que cargue el dashboard...")
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(3)

        # Screenshot después del login
        page.screenshot(path="debug_02_after_login.png")
        print("📸 Screenshot: debug_02_after_login.png")

        # Esperar que desaparezca el panel de carga (LoadingPanel)
        print("⏳ Esperando que desaparezca el loading panel...")
        try:
            page.wait_for_selector(
                '#LoadingPanel[style*="display: none"], #LoadingPanel[style*="display:none"]',
                timeout=30000
            )
        except Exception:
            print("⚠️ LoadingPanel no desapareció, continuando de todas formas...")

        time.sleep(2)

        # Screenshot del estado actual
        page.screenshot(path="debug_03_dashboard.png")
        print("📸 Screenshot: debug_03_dashboard.png")

        # Hacer clic en "Todos" (radio button)
        print("🔘 Seleccionando 'Todos'...")
        try:
            page.click('input[type="radio"][value="Todos"], label:has-text("Todos")', timeout=10000)
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ No se encontró radio 'Todos': {e}")

        # Screenshot antes de descargar
        page.screenshot(path="debug_04_before_download.png")
        print("📸 Screenshot: debug_04_before_download.png")

        # Hacer clic en el botón XLSX
        print("📥 Descargando XLSX...")
        with page.expect_download(timeout=60000) as download_info:
            page.click(
                'img[src*="xls"], a[href*="xls"], input[src*="xls"], '
                'img[title*="Excel"], img[alt*="Excel"], '
                'a[title*="Excel"], span[title*="Excel"]',
                timeout=15000
            )

        download = download_info.value
        archivo = "reporte_galleria.xlsx"
        download.save_as(archivo)
        print(f"✅ Archivo descargado: {archivo}")

        browser.close()
        return archivo

if __name__ == "__main__":
    archivo = descargar_reporte()
    print(f"🎉 Listo! Archivo guardado como: {archivo}")
