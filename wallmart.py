import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

INPUT_FILE = "model_file_products.xlsx"
OUTPUT_FILE = "scraped_results.csv"
BASE_URL = "https://www.walmart.com.mx"  # sitio base para construir URLs

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cookie": "bstc=erA4FrpTO654qzjJtZHd-U; vtc=erA4FrpTO654qzjJtZHd-U; TS014bbe1d=01e5446e15f2dc4259025e1492fb73467867b90479e8ab9eb5799f4cf74ea60b057518901bf65c8f20ba97c232e1104536445e9398; TS01fc8e13=01e5446e15f2dc4259025e1492fb73467867b90479e8ab9eb5799f4cf74ea60b057518901bf65c8f20ba97c232e1104536445e9398; exp-ck=GCJEp1; xpa=0GgO7|GCJEp|RXk9M|T0Pn-|ZUU4a|_Icwo|oqUkT|qzQJe; xpm=1%2B1747264180%2BerA4FrpTO654qzjJtZHd-U~%2B1; xpth=x-o-vertical%2BEA; TS01782124=01e5446e15f2dc4259025e1492fb73467867b90479e8ab9eb5799f4cf74ea60b057518901bf65c8f20ba97c232e1104536445e9398; TS9003c8fa027=086a3a4e09ab20007fc27101c7c25405ffc6324486d9be99382b5c3cc5af84f5cd22c3ea8501217308b5bbc7b3113000b61472e8358f05deaacc87bce80a5b71f682bf5ed8572fdb465c58aa8eea0e1882593f330be72f3e5ec947fa618aee61; _px3=12455316b2fd96a7a744eea72a66a0ecad88c72e2d6803736c3209fe00abbbe5:V3+IFmGocqintE+bk5M6zJuvSrsLUB3kqV1lxtbUXJJIwbe6e/6X7ik8wWizzvALCq9fZMh6SZHjBwwfL0ND2w==:1000:5h2Wx6LFr7RdaSf/frqGMy0UGOc6YP5FXTrk6J20CeyoTJ20DsOxqZM2csmCpshoVnBKUdgsBmNUdkI3n+jXLMnMcVyl+F49DivvjsGsBs0Cdfe/Mr3MTTUGKUOK79rxznFmQ6eLsYkKrf10YGPE/OnFnS6Gx1ZVbFSt9++Q95ZEKdH3YDRKcEqLHSMkBah3MocqD6eeKWXMTSCa/hrUjlq8HVpFDPd8R1TOMzHyPCE=; _pxde=8bfe633d78a0ccfc19307e1519ef8e9091120fb185c28b8064c70d5fa32ec4e6:eyJ0aW1lc3RhbXAiOjE3NDcyNjQzODkzNzR9; kampyleSessionPageCounter=1; kampyleUserSession=1747264028715; kampyleUserSessionsCount=2; __eoi=ID=95681bd3b70c3f6b:T=1747263345:RT=1747264027:S=AA-AfjbYMHsVW46nZvG_e5HO7SGR; __gads=ID=738c7dbbfb2a09bd:T=1747263345:RT=1747264027:S=ALNI_MavEmfvPXyoCj0p8LxmAnBdssCpEg; __gpi=UID=000010cf20e57143:T=1747263345:RT=1747264027:S=ALNI_MY-gYzM4XCmhGC7h0Td69WJ1hX10w; _ga_9K01KTJ6HC=GS2.1.s1747263278$o1$g1$t1747263906$j59$l0$h1325469381; _m=9; adblocked=false; bm_sz=9C3EA51B4BB84AA562BD2265D58B19FE~YAAQyioRAnSSPcSWAQAAv2AL0Ru9cNEAepdFGHvu9Gle3wCceJQ+8B9Vyk1lFxPWrgAC2LMLxV4ueVdhnWk9A5o8FqJBuGv8MNwcL6TtM9n3MoEI4aejehBMk6a3WSltTaX59kCa0NuMMUzR5PO7cJHH4zrHefa7plvDJgNi8kHmGAFPAkV1AXgF7bHyAYAsWBdpuaVsxkUay/8tjZULn+f02gdDIuaTKkVBHR84I8GfnFWobAtytSpOkfCywbmztKRJyn9NhuV+TYJQU2SgUoSdUIvjoaWPW+Fx8kUca1q0QlW/GzfdPs3Ix/nI6uJOioWfLL8RT8tXKyJR+6g3bNJT9MJVzrFAetnpWx3lTUlPpAq/hkJIpEhBsqqBpER1JsuwWeuEHp13uo0S4uH8CQ+HyyqnZLXlfA==~3225395~3356994",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15",
    "Accept-Language": "es-ES,es;q=0.9"
}

def buscar_producto(nombre):
    query = nombre.replace(" ", "+")
    url = f"{BASE_URL}/search?q={query}"
    print(f"[DEBUG] URL de búsqueda: {url}")
    resp = requests.get(url, headers=HEADERS)
    # Guardar la última respuesta HTML para depuración
    with open("last_response.html", "w", encoding="utf-8") as f:
        f.write(resp.text)
    print(f"[DEBUG] Código de estado: {resp.status_code}")
    soup = BeautifulSoup(resp.text, "html.parser")
    print(f"[DEBUG] Longitud HTML recibido: {len(resp.text)}")
    productos = soup.select("span.w_q67L")
    print(f"[DEBUG] ¿Hay productos? {len(productos)} encontrados")
    for i, prod in enumerate(productos[:3]):
        print(f"[DEBUG] Producto {i+1}: {prod.get_text(strip=True)}")
    if productos:
        href_tag = productos[0].find_parent("a")
        if href_tag and href_tag.has_attr("href"):
            return BASE_URL + href_tag["href"]
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
