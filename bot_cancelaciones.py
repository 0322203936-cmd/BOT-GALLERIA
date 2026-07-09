import os
import time
import csv
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

    print("⏳ Haciendo clic en 'Cargar Solicitudes De Cancelación'...")
    try:
        page.click('text="Cargar Solicitudes De Cancelación"', timeout=10000)
        time.sleep(8) # Esperar a que cargue la tabla
    except Exception as e:
        print(f"⚠️ No se pudo hacer clic en el botón cargar: {e}")

    print("📸 Tomando captura de pantalla antes de extraer (debug)...")
    page.screenshot(path="debug_cancelaciones.png", full_page=True)

    print("📊 Extrayendo datos de la tabla...")
    
    # Extraer encabezados de la tabla
    headers = page.evaluate('''() => {
        const headerNodes = Array.from(document.querySelectorAll('td[class*="dxgvHeader"], th[class*="dxgvHeader"]'));
        return headerNodes.map(h => h.innerText.trim()).filter(t => t.length > 0);
    }''')

    # Extraer filas de datos
    data_rows = page.evaluate('''() => {
        // En DevExpress, las filas de datos suelen tener la clase 'dxgvDataRow'
        const rows = Array.from(document.querySelectorAll('tr[class*="dxgvDataRow"]'));
        return rows.map(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            return cells.map(cell => cell.innerText.trim());
        });
    }''')
    
    # Si no hay encabezados, usamos unos por defecto según lo que vimos en la imagen
    if not headers:
        headers = ['Aprobar', 'Negar', 'Receta', 'Cliente #', 'Orden ID #', 'Finca', 'Fecha Envio Finca', 'Producto', 'Caja', 'Pack', 'Cantidad Confirmada', 'Solicitud Cancelación', 'Respuesta Cancelación', 'Aceptación Cancelación']

    print(f"Encontradas {len(data_rows)} solicitudes de cancelación.")
    
    csv_file = "reporte_cancelaciones_pendientes.csv"
    
    # Leer filas existentes para evitar duplicados
    existing_rows = set()
    if os.path.exists(csv_file):
        with open(csv_file, mode="r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            try:
                next(reader)  # Saltar encabezados
            except StopIteration:
                pass
            for r in reader:
                # Usar la fila completa como identificador para evitar duplicados exactos
                existing_rows.add(tuple(r))

    new_rows_count = 0
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)
            
        for row in data_rows:
            row_tuple = tuple(row)
            if row_tuple not in existing_rows:
                writer.writerow(row)
                existing_rows.add(row_tuple)
                new_rows_count += 1

    print(f"✅ Reporte actualizado exitosamente en {csv_file}")
    print(f"Se agregaron {new_rows_count} nuevas cancelaciones al acumulado.")
    
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
