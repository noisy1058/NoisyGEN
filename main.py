import os, json, time, csv, random
from playwright.sync_api import sync_playwright
from colorama import init, Fore, Style
from datetime import datetime
import calendar
from tzlocal import get_localzone

TITLE =("""  _   _       _            ____ _____ _   _ \n """
"""| \\ | | ___ (_)___ _   _ / ___| ____| \\ | |\n """
"""|  \\| |/ _ \\| / __| | | | |  _|  _| |  \\| |\n """
"""| |\\  | (_) | \\__ \\ |_| | |_| | |___| |\\  |\n """
"""|_| \\_|\\___/|_|___/\\__, |\\____|_____|_| \\_|\n """
"""                   |___/                   \n """)
URL_BASE = "https://www.icloud.com/"
SETTINGS_FILE = "settings.json"
OUTPUT_FILE = "mail.csv"
TANDA_MAX = 5
ESPERA_HORA = 3605 
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def error(msg): 
    print(f"{Fore.RED}[ERROR] {msg}")

def success(msg):
    print(f"{Fore.GREEN}[OK] {msg}")

def info(msg):
    print(f"{Fore.CYAN}[INFO] {msg}")

def save_to_csv(email):
    with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([email])

def check_session_validity(context, page):
    selector_perfil = 'div[aria-label="Ir a la página de ajustes de iCloud"]'
    try:
        page.goto(URL_BASE, wait_until="load", timeout=30000)
        return page.is_visible(selector_perfil, timeout=10000)
    except:
        return False
    
def get_timezone():
    timezone = get_localzone()
    return str(timezone)


def handle_login_flow():
    with sync_playwright() as p:
        storage = SETTINGS_FILE if os.path.exists(SETTINGS_FILE) and os.path.getsize(SETTINGS_FILE) > 100 else None
        
        browser = p.chromium.launch(headless=False,channel="chrome",args=["--start-maximized","--window-position=0,0"])
        context = browser.new_context(
            storage_state=storage, 
            user_agent=USER_AGENT,
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        if check_session_validity(context, page):
            pass
        else:
            print(get_timezone())
            info("LOGIN REQUIRED: Please identificate yourself in the window...")
            selector_perfil = 'div[aria-label="Ir a la página de ajustes de iCloud"]'
            page.wait_for_selector(selector_perfil, timeout=0)
            time.sleep(5)
            
            with open(SETTINGS_FILE, "w") as f:
                json.dump(context.storage_state(), f)
            success("Icloud session saved")
        
        browser.close()

def run_headless_generation(target_total, acumulado):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,channel="chrome",
            args=[
                '--disable-blink-features=AutomationControlled', 
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                f'--user-agent={USER_AGENT}'
            ],
            ignore_default_args=["--enable-automation"]
        )
        
        context = browser.new_context(
            storage_state=SETTINGS_FILE,
            user_agent=USER_AGENT,
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            locale='es-ES',
            timezone_id= get_timezone()
        )
        
        page = context.new_page()
        
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page.set_default_timeout(60000)

        try:
            try:
                page.goto(URL_BASE, wait_until="domcontentloaded")
                time.sleep(3)
            except Exception as e:
                info("Loading: {e}")

            info("Going to the menu...")
            
            try:
                page.get_by_role("button", name="Acceso rápido").click()
                time.sleep(1)
                page.get_by_text("Ocultar mi correo electrónico").first.click()
            except:
                print("Could not acces the menu, check if the cookie is still valid ")
                return 0

            page.wait_for_load_state("networkidle")
            time.sleep(5)

            generados_esta_tanda = 0
            while generados_esta_tanda < TANDA_MAX and (acumulado + generados_esta_tanda) < target_total:
                info(f"Trying to create account {acumulado + generados_esta_tanda + 1}/{target_total}...")

                selector_mas = 'button[title="Añadir"]'
                boton = page.locator(selector_mas)
                if not boton.is_visible():
                    for frame in page.frames:
                        if frame.locator(selector_mas).is_visible():
                            boton = frame.locator(selector_mas)
                            break
                if not boton.is_visible():
                    boton = page.locator('button:has(svg)').filter(has_text="").last

                boton.click(force=True)

                time.sleep(3)
                input_etiqueta = page.locator('input[name="hme-label"]')
                target_context = page 
                
                if not input_etiqueta.is_visible():
                    for frame in page.frames:
                        if frame.locator('input[name="hme-label"]').is_visible():
                            input_etiqueta = frame.locator('input[name="hme-label"]')
                            target_context = frame
                            break
                
                if not input_etiqueta.is_visible():
                    error("Not oepened correctly, retrying")
                    target_context.reload()
                    continue

                try:
                    nuevo_email = target_context.get_by_text("@icloud.com").first.inner_text()
                except:
                    error("Email could not be read ")
                    continue

                input_etiqueta.click()
                input_etiqueta.type("noisy_gen", delay=150) 
                time.sleep(2)

                info(f"Requesting to create account of: {nuevo_email}")
                target_context.locator('button:has-text("Crear dirección de correo")').click(force=True)
                
                exito_creacion = False

                try:
                    target_context.wait_for_selector('button:has-text("Volver")', state="visible", timeout=20000)
                    
                    save_to_csv(nuevo_email)
                    success(f"Email created and saved: {nuevo_email}")
                    
                    target_context.get_by_role("button", name="Volver").click()
                    exito_creacion = True
                    generados_esta_tanda += 1

                except Exception:
                    error(f"FAILURE: Apple not confirmed account creation for {nuevo_email}")
                    
                    try:
                        if target_context.locator('text="No se ha podido"').is_visible() or \
                           target_context.locator('text="límite"').is_visible():
                            error("RATELIMITED OR MAX AMMOUNT OF MAILS CREATED")
                            return generados_esta_tanda 
                    except:
                        pass
                    
                    info("Restarting navigation...")
                    page.goto(URL_BASE, wait_until="domcontentloaded")
                    time.sleep(5)
                    try:
                        page.get_by_role("button", name="Acceso rápido").click()
                        time.sleep(1)
                        page.get_by_text("Ocultar mi correo electrónico").first.click()
                    except: pass
                
                if exito_creacion and generados_esta_tanda < TANDA_MAX and (acumulado + generados_esta_tanda) < target_total:
                    info("Refreshing for next account")
                    try:
                        page.goto(URL_BASE, wait_until="domcontentloaded")
                        time.sleep(4)
                        page.get_by_role("button", name="Acceso rápido").click()
                        time.sleep(1)
                        page.get_by_text("Ocultar mi correo electrónico").first.click()
                        
                        page.wait_for_load_state("networkidle")
                        time.sleep(4)
                    except Exception as e:
                        print(f"Error al refrescar: {e}")
                        pass
                else:
                    time.sleep(random.uniform(5, 8))
            
            return generados_esta_tanda

        except Exception as e:
            print(f"Error crítico en modo terminal: {e}")
            try:
                page.screenshot(path="error_stealth.png")
            except: pass
            return 0
        finally:
            browser.close()

if __name__ == "__main__":

    print(TITLE)

    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f: pass

    while True:
        try:
            total_deseado = int(input("How many mails do you want to generate? "))
        
            handle_login_flow()
        
            total_acumulado = 0
            while total_acumulado < total_deseado:
                info(f"GLOBAL PROGRESS: {total_acumulado}/{total_deseado}")
            
                creados = run_headless_generation(total_deseado, total_acumulado)
                total_acumulado += creados
            
                if total_acumulado < total_deseado:
                    success("Batch finished, waiting 1 hour to continue...")
                    for i in range(60, 0, -1):
                        time.sleep(60) 
                    time.sleep(5) 
        
            success(f"\n{total_acumulado} mails generated and verified")
        
        except ValueError:
            error("Please enter a valid number")

        except KeyboardInterrupt:
            print("\nDetenido.")