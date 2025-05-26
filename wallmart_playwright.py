

import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

INPUT_FILE = "model_file_products.xlsx"
OUTPUT_FILE = "scraped_results.csv"

def buscar_y_extraer(playwright, nombre):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    print(f"🔍 Buscando: {nombre}")
    page.goto(f"https://www.walmart.com.mx/search?q={nombre.replace(' ', '+')}")
    page.wait_for_timeout(10)  # espera bruta, se puede mejorar con wait_for_selector

    productos = page.query_selector_all("span.w_q67L")
    if not productos:
        print("❌ No encontrado.")
        context.close()
        browser.close()
        return None, None, None, None, None

    titulo = productos[0].inner_text()
    enlace = productos[0].evaluate("el => el.closest('a')?.href")
    precio = page.query_selector("span[data-automation-id='product-price']").inner_text() if page.query_selector("span[data-automation-id='product-price']") else None
    vendedor = page.query_selector("span:has-text('Vendido por') + span")
    vendedor = vendedor.inner_text() if vendedor else "Walmart"
    imagen = page.query_selector("img").get_attribute("src")

    context.close()
    browser.close()
    return titulo, precio, enlace, vendedor, imagen

def main():
    df = pd.read_excel(INPUT_FILE)
    if os.path.exists(OUTPUT_FILE):
        df_out = pd.read_csv(OUTPUT_FILE)
    else:
        df_out = pd.DataFrame(columns=["Producto", "Título encontrado", "Precio", "URL", "Vendedor", "Imagen"])

    with sync_playwright() as p:
        for _, row in df.iterrows():
            producto = row["Producto"]
            if producto in df_out["Producto"].values:
                print(f"✔️ Ya procesado: {producto}")
                continue

            titulo, precio, url, vendedor, img = buscar_y_extraer(p, producto)
            df_out.loc[len(df_out)] = [producto, titulo, precio, url, vendedor, img]
            time.sleep(1)

    df_out.to_csv(OUTPUT_FILE, index=False)
    print("✅ Scraping completado.")

if __name__ == "__main__":
    main()