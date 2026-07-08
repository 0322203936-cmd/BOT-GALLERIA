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
        page.screenshot(path="debug_01_login.png")

        print("🔐 Haciendo login...")
        # Usar placeholder para identificar los campos
        page.fill('input[placeholder*="usuario" i], input[placeholder*="Usuario" i], input[type="text"]', USUARIO)
        page.fill('input[placeholder*="ontra" i], input[type="password"]', PASSWORD)
        page.click('input[value*="Entrar" i], button:has-text("Entrar"), input[type="submit"]')

        print("⏳ Esperando que cargue el dashboard...")
        page.wait_for_load_state("networkidle", timeout=60000)
        time.sleep(3)
        page.screenshot(path="debug_02_dashboard.png")
        print(f"   URL actual: {page.url}")

        # ── 2. Seleccionar "Todos" y hacer clic en Cargar ─────────────────────
        print("🔘 Seleccionando radio 'Todos'...")
        try:
            # Buscar el radio button por el label "Todos"
            page.locator('label:has-text("Todos")').click(timeout=8000)
            time.sleep(1)
        except Exception:
            try:
                page.locator('input[type="radio"]').last.click(timeout=5000)
                time.sleep(1)
            except Exception as e:
                print(f"   ⚠️ No se pudo clic en 'Todos': {e}")

        print("▶️ Haciendo clic en 'Cargar'...")
        try:
            page.click('input[value="Cargar"], button:has-text("Cargar")', timeout=8000)
            page.wait_for_load_state("networkidle", timeout=30000)
            time.sleep(2)
        except Exception as e:
            print(f"   ⚠️ No se encontró botón 'Cargar': {e}")

        page.screenshot(path="debug_03_loaded.png")

        # ── 3. Inspeccionar la página para encontrar el botón Excel ───────────
        print("🔍 Inspeccionando botones de exportación...")
        elementos = page.evaluate("""() => {
            const info = [];
            // Todas las imágenes
            document.querySelectorAll('img').forEach(el => {
                info.push({tipo: 'img', src: el.src, alt: el.alt, title: el.title, id: el.id, clase: el.className});
            });
            // Todos los links
            document.querySelectorAll('a').forEach(el => {
                if (el.href && (el.href.includes('xls') || el.href.includes('Export') || el.href.includes('export') || el.href.includes('Excel'))) {
                    info.push({tipo: 'link', href: el.href, text: el.textContent, id: el.id});
                }
            });
            // Inputs tipo image
            document.querySelectorAll('input[type="image"]').forEach(el => {
                info.push({tipo: 'input-img', src: el.src, id: el.id, clase: el.className});
            });
            // Botones con texto relacionado
            document.querySelectorAll('button, input[type="button"]').forEach(el => {
                const t = (el.textContent || el.value || '').toLowerCase();
                if (t.includes('excel') || t.includes('xls') || t.includes('export')) {
                    info.push({tipo: 'boton', text: el.textContent, value: el.value, id: el.id});
                }
            });
            // Spans y divs con onclick que mencionen export/excel
            document.querySelectorAll('[onclick]').forEach(el => {
                const oc = el.getAttribute('onclick') || '';
                if (oc.toLowerCase().includes('excel') || oc.toLowerCase().includes('export') || oc.toLowerCase().includes('xls')) {
                    info.push({tipo: 'onclick', tag: el.tagName, onclick: oc, id: el.id, clase: el.className});
                }
            });
            return info;
        }""")

        print(f"   Elementos encontrados: {len(elementos)}")
        for el in elementos:
            print(f"   → {el}")

        # ── 4. Intentar descargar ─────────────────────────────────────────────
        print("📥 Intentando descargar XLSX...")

        # Estrategia 1: Buscar img con src relacionado a excel/xls
        selectores_excel = [
            'img[src*="xls"]',
            'img[src*="Excel"]',
            'img[src*="excel"]',
            'img[alt*="Excel" i]',
            'img[title*="Excel" i]',
            'a[href*="xls"]',
            'a[href*="Excel" i]',
            'a[href*="export" i]',
            'input[src*="xls"]',
            'input[src*="excel" i]',
            '[onclick*="xls" i]',
            '[onclick*="Excel" i]',
            '[onclick*="Export" i]',
        ]

        descargado = False
        for selector in selectores_excel:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    print(f"   ✅ Encontrado con selector: {selector} ({count} elemento/s)")
                    with page.expect_download(timeout=30000) as dl:
                        page.locator(selector).first.click()
                    archivo = "reporte_galleria.xlsx"
                    dl.value.save_as(archivo)
                    print(f"✅ Descargado: {archivo}")
                    descargado = True
                    break
            except Exception as e:
                print(f"   ✗ {selector}: {e}")

        if not descargado:
            # Estrategia 2: Clic en el ícono verde (segundo ícono arriba a la derecha del visor)
            print("   🔄 Intentando por posición del ícono verde (Excel)...")
            page.screenshot(path="debug_04_before_excel_click.png")
            try:
                # El ícono Excel suele ser el segundo ícono de exportación
                iconos = page.locator('img').all()
                print(f"   Total imágenes en página: {len(iconos)}")
                for i, icono in enumerate(iconos):
                    src = icono.get_attribute("src") or ""
                    print(f"   img[{i}] src={src}")
            except Exception as e:
                print(f"   Error listando imgs: {e}")

            raise Exception("❌ No se encontró el botón Excel. Revisa los logs y debug_*.png para inspeccionar la página.")

        browser.close()
        return "reporte_galleria.xlsx"

if __name__ == "__main__":
    archivo = descargar_reporte()
    print(f"🎉 Listo! Archivo guardado como: {archivo}")
