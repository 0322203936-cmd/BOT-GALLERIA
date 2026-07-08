import os
import time
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1366, 'height': 768})
    page = context.new_page()

    print("🌐 Abriendo página de login...")
    page.goto("https://farms.galleriafarms.com/Login.aspx")

    # Obtener credenciales de los secretos
    user = os.environ.get("GF_USER")
    password = os.environ.get("GF_PASSWORD")

    if not user or not password:
        print("❌ Error: No se encontraron las credenciales en GF_USER o GF_PASSWORD")
        return

    print("🔐 Haciendo login...")
    page.fill('input[placeholder*="usuario" i], input[type="text"]', user)
    page.fill('input[placeholder*="ontra" i], input[type="password"]', password)
    page.click('button:has-text("Entrar"), input[value*="Entrar" i], input[type="submit"]')
    
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(2)

    # Navegar directamente a la página de solicitudes de cancelación
    print("➡️ Navegando a Solicitudes de Cancelación...")
    page.goto("https://farms.galleriafarms.com/CancelationRequestWFrm.aspx")
    page.wait_for_load_state("networkidle", timeout=30000)
    time.sleep(3)

    print("📸 Tomando captura de pantalla...")
    page.screenshot(path="debug_cancelaciones.png", full_page=True)

    print("✅ Listo, captura guardada como debug_cancelaciones.png")
    
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
