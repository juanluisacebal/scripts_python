import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

INPUT_FILE = "model_file_products.xlsx"
OUTPUT_FILE = "scraped_results.csv"
BASE_URL = "https://www.walmart.com.mx"  # sitio base para construir URLs

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
}

def buscar_producto(nombre):
    query = nombre.replace(" ", "+")
    url = f"{BASE_URL}/search?q={query}"
    print(f"[DEBUG] URL de búsqueda: {url}")
    resp = requests.get(url, headers=HEADERS)
    print(f"[DEBUG] Código de estado: {resp.status_code}")
    soup = BeautifulSoup(resp.text, "html.parser")
    print(f"[DEBUG] Longitud HTML recibido: {len(resp.text)}")
    productos = soup.select(".search-result-product-title a")
    print(f"[DEBUG] ¿Hay productos? {len(productos)} encontrados")
    for i, prod in enumerate(productos[:3]):
        print(f"[DEBUG] Producto {i+1}: {prod.get_text(strip=True)} — href: {prod.get('href')}")
    if productos:
        return BASE_URL + productos[0].get("href")
    return None

def extraer_datos(url):
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    print(f"[DEBUG] Extrayendo datos de: {url}")
    print(f"[DEBUG] Longitud HTML: {len(resp.text)}")
    try:
        titulo = soup.find("h1").text.strip()
        precio_elem = soup.select_one(".price-characteristic")
        precio = precio_elem["content"] if precio_elem else None
        imagen = soup.find("img", {"class": "chakra-image"})
        img_url = imagen["src"] if imagen else None
        vendedor = soup.find("span", string="Vendido por")
        vendedor = vendedor.find_next("span").text if vendedor else "Walmart"
        return titulo, precio, url, vendedor, img_url
    except Exception as e:
        print(f"Error extrayendo {url}: {e}")
        return None, None, url, None, None

def main():
    df = pd.read_excel(INPUT_FILE)
    if os.path.exists(OUTPUT_FILE):
        df_out = pd.read_csv(OUTPUT_FILE)
    else:
        df_out = pd.DataFrame(columns=["Producto", "Título encontrado", "Precio", "URL", "Vendedor", "Imagen"])

    for _, row in df.iterrows():
        producto = row["Producto"]
        if producto in df_out["Producto"].values:
            print(f"✔️ Ya procesado: {producto}")
            continue

        print(f"🔍 Buscando: {producto}")
        url = buscar_producto(producto)
        if url:
            titulo, precio, link, vendedor, img = extraer_datos(url)
            df_out.loc[len(df_out)] = [producto, titulo, precio, link, vendedor, img]
        else:
            print(f"❌ No encontrado: {producto}")
            df_out.loc[len(df_out)] = [producto, None, None, None, None, None]

        time.sleep(1)  # evitar bloqueos

    df_out.to_csv(OUTPUT_FILE, index=False)
    print("✅ Scraping completado.")

if __name__ == "__main__":
    main()
