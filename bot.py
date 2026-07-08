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
        page.goto(URL_LOGIN, wait_until="networkidle")

        # Login
        print("🔐 Haciendo login...")
        page.fill('input[name*="Usuario"], input[id*="Usuario"], input[type="text"]', USUARIO)
        page.fill('input[name*="Password"], input[id*="Password"], input[type="password"]', PASSWORD)
        page.click('input[type="submit"], button[type="submit"]')
        page.wait_for_load_state("networkidle")
        print("✅ Login exitoso")

        # Esperar a que cargue la tabla principal
        print("⏳ Esperando tabla de órdenes...")
        page.wait_for_selector("table", timeout=15000)

        # Hacer clic en "Todos" (radio button)
        print("🔘 Seleccionando 'Todos'...")
        page.click('input[type="radio"][value="Todos"], label:has-text("Todos")')
        time.sleep(1)

        # Hacer clic en el botón XLSX (ícono verde de Excel)
        print("📥 Descargando XLSX...")
        with page.expect_download(timeout=30000) as download_info:
            # El botón XLSX suele ser una imagen o ícono con extensión xls/xlsx
            page.click('img[src*="xls"], a[href*="xls"], input[src*="xls"], img[title*="Excel"], img[alt*="Excel"]')

        download = download_info.value
        archivo = "reporte_galleria.xlsx"
        download.save_as(archivo)
        print(f"✅ Archivo descargado: {archivo}")

        browser.close()
        return archivo

if __name__ == "__main__":
    archivo = descargar_reporte()
    print(f"🎉 Listo! Archivo guardado como: {archivo}")
