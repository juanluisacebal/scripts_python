import pandas as pd
from playwright.sync_api import sync_playwright
import time
import os

INPUT_FILE = "model_file_products.xlsx"
OUTPUT_FILE = "scraped_results.csv"

def buscar_y_extraer(context, nombre):
    resultados = []
    pagina = 1
    while True:
        url_busqueda = f"https://www.walmart.com.mx/search?q={nombre.replace(' ', '+')}&page={pagina}&affinityOverride=default"
        print(f"🔍 Página {pagina}: {url_busqueda}")
        page = context.new_page()
        page.goto(url_busqueda)
        resolver_captcha_si_aparece(page)

        page.wait_for_timeout(2000)
        if page.locator("text=No se encontraron resultados para").first.is_visible():
            print("🚫 Fin de resultados detectado por mensaje en página.")
            page.close()
            break
        try:
            print("⌛ Esperando aparición de productos visibles (span.w_q67L)...")
            page.wait_for_selector("span.w_q67L", timeout=15000)
        except:
            print("❌ No se encontraron resultados visibles tras esperar.")
            page.close()
            break

        productos = page.query_selector_all("span.w_q67L")
        # Guardar screenshot y HTML para depuración
        page.screenshot(path=f"screenshot_{nombre.replace(' ', '_')}_page{pagina}.png", full_page=True)
        with open(f"html_dump_{nombre.replace(' ', '_')}_page{pagina}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("🧾 Screenshot y HTML guardados para depuración.")
        print(f"📦 Productos encontrados: {len(productos)}")

        for i, prod in enumerate(productos):
            contenedor = prod.evaluate_handle("el => el.closest('div[data-item-id]')").as_element()
            if not contenedor:
                print(f"❗ No se encontró contenedor para producto {i}")
                continue
            print(f"✅ Contenedor encontrado para producto {i}")

            # Buscar título de manera robusta
            titulo_elem = contenedor.query_selector("span.w_q67L")
            titulo = titulo_elem.inner_text() if titulo_elem else "Sin título"
            enlace_elem = contenedor.query_selector("a[href*='/ip/']")
            enlace = enlace_elem.get_attribute("href") if enlace_elem else None

            import re
            id_producto = None
            if enlace:
                match = re.search(r'/(\d{11,})[\?/]?', enlace)
                if match:
                    id_producto = match.group(1)
                else:
                    print("⚠️ No se pudo extraer ID numérico de la URL.")

            precio_elem = contenedor.query_selector("span:has-text('$')")
            precio = precio_elem.inner_text() if precio_elem else None
            precio_lista_elem = contenedor.query_selector("span:has-text('Costaba')")
            precio_lista = precio_lista_elem.inner_text() if precio_lista_elem else ""

            import re
            def extraer_precio_numerico(texto):
                try:
                    precio_encontrado = re.search(r"\$?\s*([\d.,]+)", texto if texto else "")
                    if precio_encontrado:
                        valor = precio_encontrado.group(1)
                        # Si hay más de un punto, los puntos son separadores de miles y la coma es decimal
                        if valor.count(".") > 1:
                            valor = valor.replace(".", "")
                            valor = valor.replace(",", ".")
                        else:
                            valor = valor.replace(",", "")
                        return float(valor)
                except:
                    pass
                return None

            precio = extraer_precio_numerico(precio)
            precio_lista = extraer_precio_numerico(precio_lista)
            vendedor = "Walmart"  # valor por defecto
            if enlace:
                producto_page = context.new_page()
                try:
                    producto_page.goto("https://www.walmart.com.mx" + enlace, timeout=20000)
                    resolver_captcha_si_aparece(producto_page)
                    producto_page.wait_for_timeout(3000)
                    try:
                        vendedor_elem = producto_page.query_selector("span[data-testid='product-seller-info'] span")
                        if vendedor_elem:
                            vendedor = vendedor_elem.inner_text().strip()
                            print(f"    🏷️ Vendedor detallado: {vendedor}")
                    except Exception as e:
                        print(f"⚠️ No se pudo extraer el vendedor con data-testid: {e}")
                except Exception as e:
                    print(f"⚠️ Error al obtener vendedor en detalle: {e}")
                finally:
                    producto_page.close()
            img_elem = contenedor.query_selector("img[src*='walmartimages.com']")
            imagen = img_elem.get_attribute("src") if img_elem else None
            if imagen:
                if imagen.startswith("//"):
                    imagen = "https:" + imagen
                elif imagen.startswith("/"):
                    imagen = "https://www.walmart.com.mx" + imagen

            # Guardar miniatura local si es posible
            from urllib.parse import urlparse
            import urllib.request

            imagen_local = None
            if imagen and imagen.startswith("http"):
                img_name = f"img_{nombre.replace(' ', '_')}_{pagina}_{i}.jpg"
                img_path = os.path.join("imgs", img_name)
                os.makedirs("imgs", exist_ok=True)
                try:
                    urllib.request.urlretrieve(imagen, img_path)
                    imagen_local = img_path
                except Exception as e:
                    print(f"⚠️ Error al descargar imagen: {e}")

            print(f"📝 [{i}] Título: {titulo}")
            print(f"    🔗 Enlace: {enlace}")
            print(f"    🆔 ID producto: {id_producto}")
            print(f"    💲 Precio: {precio}")
            print(f"    💰 Precio lista: {precio_lista}")
            print(f"    🏷️ Vendedor: {vendedor}")
            print(f"    🖼️ Imagen: {imagen}")

            url_completa = f"https://www.walmart.com.mx{enlace}" if enlace and not enlace.startswith("http") else enlace
            resultados.append((titulo, precio, precio_lista, id_producto, url_completa, vendedor, imagen_local))
            import random
            delay = random.uniform(8, 12)
            print(f"⏱️ Esperando {delay:.2f} segundos antes de continuar con el siguiente producto...")
            page.wait_for_timeout(delay * 1000)

        page.close()
        print(f"➡️ Avanzando a la página {pagina + 1}")
        pagina += 1

    return resultados

def resolver_captcha_si_aparece(page):
    try:
        print("🧪 Verificando presencia de botón de captcha...")
        button = page.locator("text=Mantén presionado")
        if button.is_visible():
            nombre_archivo = f"captcha_detectado_{int(time.time())}"
            page.screenshot(path=f"{nombre_archivo}.png", full_page=True)
            with open(f"{nombre_archivo}.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"📸 Captura y HTML guardados como {nombre_archivo}.png y {nombre_archivo}.html")
            print("🤖 Intentando resolver el captcha automáticamente...")

            box = button.bounding_box()
            if box:
                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                page.mouse.move(x, y)
                page.mouse.down()
                print("🖱️ Mouse presionado sobre el botón")

                for intento in range(20):
                    still_visible = page.locator("text=Mantén presionado").is_visible() or page.locator(".px-inner-loading-area").is_visible()
                    if not still_visible:
                        print("✅ CAPTCHA resuelto exitosamente.")
                        break
                    print(f"⏳ Manteniendo presionado... intento {intento+1}")
                    page.wait_for_timeout(1000)
                else:
                    raise Exception("CAPTCHA no resuelto tras espera")

                page.mouse.up()
                print("🖱️ Mouse soltado")
    except Exception as e:
        print(f"⚠️ Fallo al intentar resolver el CAPTCHA: {e}")
        raise

def main():
    df = pd.read_excel(INPUT_FILE)
    if os.path.exists(OUTPUT_FILE):
        df_out = pd.read_csv(OUTPUT_FILE)
    else:
        df_out = pd.DataFrame(columns=["Producto", "Título encontrado", "Precio", "Precio lista", "ID producto", "URL", "Vendedor", "Imagen"])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="es-ES",
            java_script_enabled=True
        )
        context.add_init_script("""() => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        }""")
        for _, row in df.iterrows():
            producto = row["Producto"]
            if producto in df_out["Producto"].values:
                print(f"✔️ Ya procesado: {producto}")
                continue

            resultados = buscar_y_extraer(context, producto)
            if resultados:
                for titulo, precio, precio_lista, id_prod, url, vendedor, img in resultados:
                    df_out.loc[len(df_out)] = [producto, titulo, precio, precio_lista, id_prod, url, vendedor, img]
                    print("📝 Registro guardado:")
                    print(f"  Producto original: {producto}")
                    print(f"  Título: {titulo}")
                    print(f"  Precio: {precio}")
                    print(f"  Precio lista: {precio_lista}")
                    print(f"  ID producto: {id_prod}")
                    print(f"  URL: {url}")
                    print(f"  Vendedor: {vendedor}")
                    print(f"  Imagen: {img}")
                    print("—" * 40)
            time.sleep(1)

        context.close()
        browser.close()

    if not os.path.exists("repetidos.csv"):
        df_reps = pd.DataFrame(columns=df_out.columns)
    else:
        df_reps = pd.read_csv("repetidos.csv")

    nuevos = df_out.duplicated(subset=["ID producto", "Vendedor"], keep="first")
    repetidos = df_out[nuevos]
    df_out = df_out[~nuevos]

    if not repetidos.empty:
        df_reps = pd.concat([df_reps, repetidos], ignore_index=True)
        df_reps.to_csv("repetidos.csv", index=False)

    df_out.to_csv(OUTPUT_FILE, index=False)
    print(f"📊 Total de registros insertados: {len(df_out)}")
    print("✅ Scraping completado.")

if __name__ == "__main__":
    main()